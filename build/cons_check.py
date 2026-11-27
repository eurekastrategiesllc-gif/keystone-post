"""Is a rebuilt consultant board safe to publish?  python3 cons_check.py OLD.json NEW.json  (exit 1 = keep the old one)"""
import json, sys
a = json.load(open(sys.argv[1])); b = json.load(open(sys.argv[2])); bad = []
for p in ('R', 'D'):
    print(p, 'firms %d -> %d,' % (len(a[p]), len(b[p])), 'paid %d -> %d,' % (sum(f['tot'] for f in a[p]), sum(f['tot'] for f in b[p])), 'scored clients %d -> %d' % (sum(f['w'] + f['l'] for f in a[p]), sum(f['w'] + f['l'] for f in b[p])))
    if len(b[p]) < 0.8 * len(a[p]): bad.append(p + ': firm count fell by more than 20%')
    if sum(f['w'] + f['l'] for f in b[p]) < 0.8 * sum(f['w'] + f['l'] for f in a[p]): bad.append(p + ': scored clients fell by more than 20%')
    if any(len(r) < 9 for f in b[p] for r in f['c']): bad.append(p + ': payer rows are missing the race level')
print('results file', b['meta']['results_pulled'])
if bad:
    print('BOARD NOT USED:'); [print(' -', x) for x in bad]; sys.exit(1)
