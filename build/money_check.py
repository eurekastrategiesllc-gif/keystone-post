"""Has any source file changed since the last money rebuild?

Asks each source for its Last-Modified date and size and compares with build/money_sources.json.
Prints changed=true/false for the workflow and writes the new signatures to build/money_sources.new.json.
"""
import json, os, sys, urllib.request, email.utils
HERE = os.path.dirname(os.path.abspath(__file__))
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
FEC = 'https://www.fec.gov/files/bulk-downloads/2026/'
SOURCES = {'weball26': FEC + 'weball26.zip', 'cm26': FEC + 'cm26.zip', 'ccl26': FEC + 'ccl26.zip', 'pas226': FEC + 'pas226.zip', 'oppexp26': FEC + 'oppexp26.zip', 'indiv26': FEC + 'indiv26.zip',
           'pa_dos_2026': 'https://www.pa.gov/content/dam/copapwp-pagov/en/dos/resources/voting-and-elections/campaign-finance/campaign-finance-data/2026.zip'}
def head(url):
    r = urllib.request.urlopen(urllib.request.Request(url, method='HEAD', headers={'User-Agent': UA, 'Accept': '*/*'}), timeout=60)
    return {'modified': r.headers.get('Last-Modified', ''), 'size': r.headers.get('Content-Length', ''), 'etag': r.headers.get('ETag', '')}
if __name__ == '__main__':
    old = {}
    p = os.path.join(HERE, 'money_sources.json')
    if os.path.exists(p): old = json.load(open(p))
    new = {}; bad = []
    for k, u in SOURCES.items():
        try: new[k] = head(u)
        except Exception as e: bad.append('%s: %s %s' % (k, type(e).__name__, e))
        print(k, new.get(k) or 'FAILED')
    if bad:
        print('could not reach:', *bad, sep='\n  '); print('changed=false'); sys.exit(1)
    changed = [k for k in SOURCES if (new[k]['modified'], new[k]['size']) != (old.get(k, {}).get('modified'), old.get(k, {}).get('size'))]
    json.dump(new, open(os.path.join(HERE, 'money_sources.new.json'), 'w'), indent=1)
    d = email.utils.parsedate_to_datetime(new['pa_dos_2026']['modified']) if new['pa_dos_2026']['modified'] else None
    print('changed sources:', changed or 'none')
    out = os.environ.get('GITHUB_OUTPUT')
    if out:
        open(out, 'a').write('changed=%s\nstate_export=%s\n' % ('true' if changed else 'false', d.strftime('%Y-%m-%d') if d else ''))
