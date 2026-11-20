"""Print the last state reporting period that the export covers, for the site's "state through" date.

Pennsylvania 2026 cycles: 5 = second Friday pre-election report (complete as of Oct 19),
6 = 30-day post-election report (complete as of Nov 23, due Dec 3). The post-election date is
used once at least a quarter as many filers have filed cycle 6 as filed cycle 5.
"""
import csv, os, collections
from common import RAW
c = collections.Counter()
seen = set()
for r in csv.DictReader(open(os.path.join(RAW, 'pa_dos_2026', 'filer_2026.txt'), encoding='latin-1')):
    k = (r['FILERID'], r['CYCLE'])
    if k not in seen: seen.add(k); c[r['CYCLE']] += 1
print('2026-11-23' if c['6'] >= max(1, c['5']) * 0.25 else '2026-10-19')
