"""Run on the Mac after a Chrome pull: gather the last 3 days of pulls into two files for GitHub.

Reads ../raw/feeds/ksnews*.json and ksop_*.json changed in the last 3 days and writes
../macpull/ksnews_mac.json and ../macpull/ksop_mac.json, one row per link.
"""
import json, glob, os, time
HERE = os.path.dirname(os.path.abspath(__file__))
FEEDS = os.path.join(HERE, '..', 'raw', 'feeds'); OUT = os.path.join(HERE, '..', 'macpull')
os.makedirs(OUT, exist_ok=True); cut = time.time() - 3 * 86400
for pat, name in (('ksnews*.json', 'ksnews_mac.json'), ('ksop_*.json', 'ksop_mac.json')):
    S = {}
    for f in sorted(glob.glob(os.path.join(FEEDS, pat)), key=os.path.getmtime, reverse=True):
        if os.path.getmtime(f) < cut: continue
        for host, items in json.load(open(f, encoding='utf-8')).items():
            rows = S.setdefault(host, []); have = {r[1] for r in rows}
            for i in items:
                if len(i) >= 4 and i[1] not in have: rows.append(list(i[:4])); have.add(i[1])
    open(os.path.join(OUT, name), 'w', encoding='utf-8').write(json.dumps(S, ensure_ascii=False, separators=(',', ':')))
    print(name, len(S), 'hosts', sum(len(v) for v in S.values()), 'rows')
