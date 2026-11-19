"""Township and borough news: called at the end of trend.py.

For every story already matched to a county, look for the names of that county's
townships, boroughs and cities, and write D['mnews'] = {county: {municipality key: [stories]}}.
"""
import re, json, collections, datetime, email.utils
def build(N, counties_for):
    slug=lambda s: re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')
    per=collections.defaultdict(list)
    for (name,typ),cs in N.subs.items():
        for c in cs: per[c].append((name,typ))
    rx={}
    for c,ms in per.items():
        pats=[]
        for name,typ in ms:
            e=re.escape(name)
            if typ=='township': pats.append((re.compile(r'\b%s (?:Township|Twp\b\.?)'%e),name,typ))
            elif name in N.STOP or len(name)<5: pats.append((re.compile(r'\b(?:%s (?:Borough|Boro\b|City\b)|(?:City|Borough) of %s\b|\bin %s\b(?! (?:County|Township|Twp)))'%(e,e,e)),name,typ))
            else: pats.append((re.compile(r'\b%s\b(?! (?:County|Township|Twp))'%e),name,typ))
        rx[c]=pats
    out=collections.defaultdict(lambda:collections.defaultdict(list)); seen=set()
    for host,items in N.RAWITEMS.items():
        src,home=N.HOME.get(host,(host,[]))
        for t,u,pd,desc in items:
            t=re.sub(r'\s+',' ',t)
            try: d=email.utils.parsedate_to_datetime(pd)
            except Exception: continue
            if d.tzinfo is None: d=d.replace(tzinfo=datetime.timezone.utc)
            if not t or not u.startswith('http') or (N.now-d).days>10 or d>N.now+datetime.timedelta(hours=6) or N.SKIP.search(u) or N.JUNK.search(t): continue
            text=t+' . '+desc; wire=bool(N.WIRE.search(text))
            rec={'t':t,'u':u,'s':src,'d':d.astimezone(datetime.timezone(datetime.timedelta(hours=-5))).strftime('%Y-%m-%d')}
            for c in counties_for(t,desc,home,wire):
                for r,name,typ in rx.get(c,[]):
                    if r.search(text) and (c,name,typ,u) not in seen:
                        seen.add((c,name,typ,u)); out[c][slug(name+' '+typ)].append(rec)
    res={c:{k:sorted(v,key=lambda x:x['d'],reverse=True)[:12] for k,v in m.items()} for c,m in out.items()}
    for dst in('../data.json','../site/data.json'):
        D=json.load(open(dst,encoding='utf-8')); D['mnews']=res
        open(dst,'w',encoding='utf-8').write(json.dumps(D,separators=(',',':'),ensure_ascii=False))
    print('township and borough news: counties',len(res),'places',sum(len(m) for m in res.values()),'stories',sum(len(v) for m in res.values() for v in m.values()))
