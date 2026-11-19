"""Checks before publishing (from the runbook). Exit 1 means: do not publish."""
import json, os, sys, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, '..', 'site', 'data.json')
D = json.load(open(P, encoding='utf-8')); bad = []
news = D.get('news', {}); trend = D.get('trend', {})
if len(news) != 67: bad.append('news has %d counties, not 67' % len(news))
thin = sorted(c for c, v in news.items() if len(v) < 3)
if thin: bad.append('counties with fewer than 3 stories: ' + ', '.join(thin))
if len(trend) != 67: bad.append('trend has %d counties, not 67' % len(trend))
if not D.get('camps') or not D.get('counties'): bad.append('campaign or county data is empty')
dates = [x['d'] for v in news.values() for x in v]
newest = max(dates) if dates else ''
et = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-5)))
if not newest or (et.date() - datetime.date.fromisoformat(newest)).days > 2: bad.append('newest story is %s, more than 2 days old' % (newest or 'missing'))
txt = json.dumps(D['news']) + json.dumps(D['trend'])
st = os.path.join(HERE, 'pull_status.json')
if os.path.exists(st):
    S = json.load(open(st)); D['meta']['news_pulled_at'] = S['at']; D['meta']['feeds_ok'] = S['ok']; D['meta']['feeds_total'] = S['total']
    if S['ok'] == 0: bad.append('no feed answered on this run')
own = sum(1 for v in news.values() if sum(1 for x in v if not x.get('scope')) >= 3)
print('newest story', newest, '| counties with 3+ own stories', own, '| stories shown', len(dates))
if bad:
    print('CHECKS FAILED:'); [print(' -', b) for b in bad]; sys.exit(1)
open(P, 'w', encoding='utf-8').write(json.dumps(D, separators=(',', ':'), ensure_ascii=False))
print('checks passed')
