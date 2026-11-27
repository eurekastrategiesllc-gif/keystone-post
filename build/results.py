"""Election results for the consultant scoreboard.

  python3 results.py fetch                 read the Department of State returns site directly (GitHub)
  python3 results.py from-download FILE    reshape a file saved from that site in Chrome (Joe's Mac)

Either way the new results are checked, compared with the newest raw/pa_results_*.json, and saved as
raw/pa_results_<today>.json only when something changed. Prints changed=true or changed=false.
Exit 1 means the pull failed or looked wrong; the old file is left alone.
"""
import json, os, re, sys, glob, datetime, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, '..', 'raw')
YEAR = 2026
SITE = 'https://www.electionreturns.pa.gov/api/ElectionReturn/'
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
OFFICES = [(3, 'GOV'), (4, 'LTG'), (11, 'USC'), (12, 'STS'), (13, 'STH')]
LETTER = {'GOV': 'G', 'LTG': 'L', 'USC': 'C', 'STS': 'S', 'STH': 'H'}

def deep(x):
    """the site wraps JSON inside JSON strings, sometimes twice"""
    while isinstance(x, str):
        try: x = json.loads(x)
        except ValueError: break
    if isinstance(x, list): return [deep(v) for v in x]
    if isinstance(x, dict): return {k: deep(v) for k, v in x.items()}
    return x

def get(path):
    r = urllib.request.urlopen(urllib.request.Request(SITE + path, headers={'User-Agent': UA, 'Accept': 'application/json, text/plain, */*', 'Referer': 'https://www.electionreturns.pa.gov/'}), timeout=90)
    return deep(json.loads(r.read().decode('utf-8-sig')))

def elections():
    """(election id, type, is-active flag) for this year's primary and general, found by name"""
    found = {}
    def walk(x):
        if isinstance(x, list): [walk(v) for v in x]
        elif isinstance(x, dict):
            if 'ElectionName' in x: found[str(x['ElectionName']).strip()] = x
            else: [walk(v) for v in x.values()]
    walk(get('GetAllElections?methodName=GetAllElections'))
    out = []
    for name, t in (('%d General Primary' % YEAR, 'P'), ('%d General Election' % YEAR, 'G')):
        e = found.get(name)
        if e: out.append((str(e['Electionid']), t, str(e.get('ISActive', '0'))))
        else: print('not on the site yet:', name)
    return out

def rows_from(x, t, code, rows):
    def add(d, c):
        if 'CandidateName' in c: rows.append([t, code, d.get('District') or 'Statewide', c.get('PartyName') or '', c['CandidateName'], c.get('Votes') or 0])
        else:
            for v in c.values():
                if isinstance(v, list): [add(d, cc) for cc in v if isinstance(cc, dict)]
    for off in (x.get('Election') or {}).values():
        for blk in off:
            if 'Statewide' in blk or 'Candidates' in blk:
                [add(blk, c) for c in (blk.get('Statewide') or blk.get('Candidates') or [])]; continue
            for arr in blk.values():
                if isinstance(arr, list):
                    for d in arr: [add(d, c) for c in (d.get('Candidates') or d.get('Statewide') or [])]

def fetch_rows():
    rows = []
    for eid, t, act in elections():
        for oid, code in OFFICES:
            try: x = get('GetOfficeData?officeId=%d&methodName=GetOfficeDetails&electionid=%s&electiontype=%s&isactive=%s' % (oid, eid, t, act))
            except Exception as e:
                if code == 'LTG' and t == 'G': continue   # lieutenant governor is on the governor's ticket in November
                raise
            if not isinstance(x, dict):
                print('no table for %s %s: %r' % (t, code, str(x)[:120])); continue   # the counts are checked afterwards
            n = len(rows); rows_from(x, t, code, rows); print(t, code, len(rows) - n, 'candidates')
    return rows

def races_from(rows):
    races = {}
    for r in rows:
        t, code, dist, party, name, votes = r[:6]
        d = (re.match(r'\d+', str(dist)) or [0])[0]
        p = party[:1].upper() if t == 'P' else party.replace('D/R', 'D+R').replace('R/D', 'D+R')
        nm = re.sub(r'\s+', ' ', re.sub(r'[;:/,=?&]', ' ', str(name))).strip()
        races.setdefault('%s%s%s' % (t, LETTER[code], int(d)), []).append([p, nm, int(float(votes or 0))])
    return races

def norm(races): return {k: sorted(v) for k, v in sorted(races.items())}

def problems(races, old):
    bad = []
    n = lambda pre: sum(1 for k in races if k.startswith(pre))
    for pre, want in (('PC', 17), ('PS', 25), ('PH', 203)):
        if n(pre) != want: bad.append('%s races: %d, expected %d' % (pre, n(pre), want))
    if any(k[0] == 'G' for k in races) or any(k[0] == 'G' for k in old):
        for pre, want in (('GC', 17), ('GS', 25), ('GH', 203), ('GG', 1)):
            if n(pre) != want: bad.append('%s races: %d, expected %d' % (pre, n(pre), want))
    tot = lambda R: sum(c[2] for v in R.values() for c in v)
    if old and tot(races) < 0.9 * tot(old): bad.append('total votes fell from %d to %d' % (tot(old), tot(races)))
    if old and len(races) < len(old): bad.append('fewer races than the last pull (%d, was %d)' % (len(races), len(old)))
    return bad

def main():
    if len(sys.argv) >= 3 and sys.argv[1] == 'from-download':
        rows = json.load(open(sys.argv[2]))['rows']
    elif len(sys.argv) == 2 and sys.argv[1] == 'fetch':
        rows = fetch_rows()
    else: sys.exit(__doc__)
    races = races_from(rows)
    files = sorted(glob.glob(os.path.join(RAW, 'pa_results_*.json')))
    old = json.load(open(files[-1]))['races'] if files else {}
    print('pulled %d races, %d candidates, %d votes' % (len(races), sum(len(v) for v in races.values()), sum(c[2] for v in races.values() for c in v)))
    bad = problems(races, old)
    if bad:
        print('RESULTS NOT USED:'); [print(' -', b) for b in bad]; print('changed=false'); sys.exit(1)
    changed = norm(races) != norm(old)
    if changed:
        diff = [k for k in races if sorted(races[k]) != sorted(old.get(k, []))]
        winner = lambda v: max(v, key=lambda c: c[2])[1] if v else ''
        flips = [k for k in diff if k[0] == 'G' and k in old and winner(races[k]) != winner(old[k])]
        print('%d races differ from %s; November leaders changed in: %s' % (len(diff), os.path.basename(files[-1]) if files else 'nothing', ', '.join(flips) or 'none'))
        today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-5))).date().isoformat()
        out = {'pulled': today, 'source': 'electionreturns.pa.gov: %d General Primary (P) and %d General Election (G); November numbers are unofficial until the state certifies them' % (YEAR, YEAR),
               'key': '<P|G><G gov|L lt gov|C congress|S state senate|H state house><district>: [party, name, votes]', 'races': races}
        json.dump(out, open(os.path.join(RAW, 'pa_results_%s.json' % today), 'w'), separators=(',', ':'))
        print('saved raw/pa_results_%s.json' % today)
    else: print('same as', os.path.basename(files[-1]))
    print('changed=%s' % ('true' if changed else 'false'))
    o = os.environ.get('GITHUB_OUTPUT')
    if o: open(o, 'a').write('changed=%s\n' % ('true' if changed else 'false'))

if __name__ == '__main__': main()
