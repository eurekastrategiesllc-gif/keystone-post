"""Pull every feed in feeds.json from a plain server and keep a rolling store.

Writes raw/feeds/ksnews_store.json and raw/feeds/ksop_store.json in the shape
news.py and trend.py already read: {"<host>": [[title, link, pubDate, description], ...]}
(opinion feeds use the key "<host>#op"). New rows are merged into the store by
link, so a host that fails on one run keeps its earlier stories.
"""
import json, os, re, sys, gzip, html, time, datetime, email.utils, urllib.request, urllib.error, concurrent.futures

HERE = os.path.dirname(os.path.abspath(__file__))
FEEDS = os.path.join(HERE, '..', 'raw', 'feeds')
KEEP_DAYS = {'news': 14, 'opinion': 50}
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
BOT = 'KeystonePostFeedReader/1.0 (+https://github.com/eurekastrategiesllc-gif/keystone-post)'
now = datetime.datetime.now(datetime.timezone.utc)

def clean(s):
    s = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', s or '', flags=re.S)
    s = html.unescape(s)
    s = re.sub(r'<[^>]+>', ' ', s)
    return re.sub(r'\s+', ' ', html.unescape(s)).strip()

def tag(block, name):
    m = re.search(r'<%s(?:\s[^>]*)?>(.*?)</%s>' % (name, name), block, re.S)
    return m.group(1) if m else ''

def when(s):
    s = clean(s)
    if not s: return None
    try:
        d = email.utils.parsedate_to_datetime(s)
    except Exception:
        try: d = datetime.datetime.fromisoformat(s.replace('Z', '+00:00'))
        except Exception: return None
    if d.tzinfo is None: d = d.replace(tzinfo=datetime.timezone.utc)
    return d

def parse(x):
    rows = []
    for it in re.findall(r'<item[\s>].*?</item>', x, re.S):
        rows.append((clean(tag(it, 'title')), clean(tag(it, 'link')), tag(it, 'pubDate') or tag(it, 'dc:date'), clean(tag(it, 'description'))[:300]))
    if not rows:
        for it in re.findall(r'<entry[\s>].*?</entry>', x, re.S):
            m = re.search(r'<link[^>]*rel=["\']alternate["\'][^>]*href=["\']([^"\']+)', it) or re.search(r'<link[^>]*href=["\']([^"\']+)', it)
            rows.append((clean(tag(it, 'title')), html.unescape(m.group(1)) if m else '', tag(it, 'published') or tag(it, 'updated'), clean(tag(it, 'summary') or tag(it, 'content'))[:300]))
    out = []
    for t, u, pd, d in rows:
        dt = when(pd)
        if t and u.startswith('http') and dt:
            out.append([t, u, email.utils.format_datetime(dt), d])
    return out

def pull(f):
    url = f.get('feed') or f.get('feed_guess'); err = ''
    # First ask as a browser would; if the site answers 429, ask once more under the project's own name.
    for ua in (UA, BOT):
        req = urllib.request.Request(url, headers={'User-Agent': ua, 'Accept': 'application/rss+xml, application/atom+xml, application/xml;q=0.9, */*;q=0.8', 'Accept-Language': 'en-US,en;q=0.9', 'Accept-Encoding': 'gzip'})
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                b = r.read(8_000_000)
                if r.headers.get('Content-Encoding') == 'gzip' or b[:2] == b'\x1f\x8b': b = gzip.decompress(b)
            rows = parse(b.decode('utf-8', 'replace'))
            return f, rows, '' if rows else 'no items in response'
        except urllib.error.HTTPError as e:
            err = 'HTTP %s' % e.code
            if e.code != 429: break
            time.sleep(3)
        except Exception as e:
            err = ('%s %s' % (type(e).__name__, e))[:120]; break
    return f, [], err

def pull_slowly(group):
    # Sites on one shared platform answer 429 when asked in parallel, so ask them one at a time.
    out = []
    for f in group:
        out.append(pull(f)); time.sleep(2)
    return out

def main():
    feeds = json.load(open(os.path.join(HERE, 'feeds.json'), encoding='utf-8'))
    paths = {'news': os.path.join(FEEDS, 'ksnews_store.json'), 'opinion': os.path.join(FEEDS, 'ksop_store.json')}
    store = {k: (json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}) for k, p in paths.items()}
    status = {}
    is_shared = lambda f: f.get('cms') == 'townnews' or '/search/?f=rss' in (f.get('feed') or f.get('feed_guess') or '')
    shared = [f for f in feeds if is_shared(f)]
    rest = [f for f in feeds if not is_shared(f)]
    with concurrent.futures.ThreadPoolExecutor(8) as ex:
        slow = ex.submit(pull_slowly, shared)
        results = list(ex.map(pull, rest)) + slow.result()
    for f, rows, err in results:
        kind = f['kind']; key = f['host'] + ('#op' if kind == 'opinion' else '')
        old = store[kind].get(key, []); have = {r[1] for r in old}
        fresh = [r for r in rows if r[1] not in have]
        merged = fresh + old; keep = []
        for r in merged:
            d = when(r[2])
            if d and (now - d).days <= KEEP_DAYS[kind]: keep.append(r)
        store[kind][key] = keep
        status[key] = {'ok': not err, 'got': len(rows), 'new': len(fresh), 'kept': len(keep), 'err': err}
    # Pulls made through Chrome on the Mac (branch "macpull") cover the sites that refuse this server.
    mac = {'news': os.path.join(FEEDS, 'mac', 'ksnews_mac.json'), 'opinion': os.path.join(FEEDS, 'mac', 'ksop_mac.json')}
    for kind, mp in mac.items():
        if not os.path.exists(mp): continue
        added = 0
        for key, rows in json.load(open(mp, encoding='utf-8')).items():
            if kind == 'opinion' and not key.endswith('#op'): key += '#op'
            old = store[kind].get(key, []); have = {r[1] for r in old}; fresh = []
            for r in rows:
                if len(r) < 4: continue
                t, u, d = clean(r[0]), clean(r[1]), when(r[2])
                if t and u.startswith('http') and d and u not in have and (now - d).days <= KEEP_DAYS[kind]:
                    fresh.append([t, u, email.utils.format_datetime(d), clean(r[3])[:300]]); have.add(u)
            if fresh:
                store[kind][key] = fresh + old; added += len(fresh)
                st = status.setdefault(key, {'ok': False, 'got': 0, 'new': 0, 'kept': len(old), 'err': 'not in feeds.json'})
                st['mac_new'] = len(fresh); st['kept'] = len(store[kind][key])
        print('rows added from the Mac pull (%s): %d' % (kind, added))
    os.makedirs(FEEDS, exist_ok=True)
    for k, p in paths.items():
        open(p, 'w', encoding='utf-8').write(json.dumps(store[k], ensure_ascii=False, separators=(',', ':')))
    ok = sum(1 for v in status.values() if v['ok'])
    json.dump({'at': now.strftime('%Y-%m-%dT%H:%M:%SZ'), 'ok': ok, 'total': len(status), 'hosts': status}, open(os.path.join(HERE, 'pull_status.json'), 'w'), indent=1)
    print('feeds answered %d of %d; new rows %d' % (ok, len(status), sum(v['new'] for v in status.values())))
    for k, v in sorted(status.items()):
        if not v['ok']: print('  FAILED', k, v['err'])

if __name__ == '__main__':
    main()
