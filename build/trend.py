import re, json, glob, collections, datetime, email.utils
import news as N
from common import *
TOPICS=[('Property taxes and budgets',r'property tax|tax (increase|hike|rate|relief|bill)|millage|budget|reassessment|deficit'),
('Schools',r'school board|school district|teachers?\b|superintendent|students?\b|curriculum|cyber charter|school (closure|closing|consolidat)|tuition|campus'),
('Data centers, zoning and development',r'data center|zoning|warehouse|rezon|land development|planning commission|solar (farm|project)|developer'),
('Roads, bridges and transit',r'\bbridge|road (work|closure|project)|penndot|turnpike|transit|septa|pothole|traffic|paving|\brail'),
('Crime and public safety',r'police|shooting|homicide|crime|sheriff|district attorney|fentanyl|overdose|fire (company|department|chief)|\bems\b|ambulance|\bjail|prison'),
('Health care',r'hospital|upmc|geisinger|health (system|care|center)|nursing home|medicaid|clinic|maternity|mental health'),
('Energy, water and utilities',r'electric (bill|rate)|utility|utilities|\bppl\b|peco|natural gas|fracking|pipeline|water (rate|authority|system|bill)|sewer|power plant|\bgrid\b'),
('Housing and cost of living',r'housing|\brent\b|homeless|affordab|eviction|shelter|inflation|grocer|food (bank|pantry)|\bsnap\b|liheap'),
('Jobs and local economy',r'layoffs?|plant (closing|closure)|\bjobs\b|unemployment|factory|manufactur|small business|downtown|economic development|tourism'),
('Elections and local government',r'election|ballot|voter|commissioners?\b|county council|city council|\bmayor|borough council|supervisors|recount|campaign|legislat|state budget|shapiro|governor'),
('Environment and farming',r'\bfarm|agricultur|flood|pollution|\bdep\b|landfill|wildlife|game commission|drought|conservation'),
('Immigration',r'\bice\b|immigra|deport|detention center')]
TOPICS=[(k,re.compile(p,re.I)) for k,p in TOPICS]
NEG=re.compile(r'oppos|protest|concern|complain|critic|outrage|anger|angry|frustrat|lawsuit|\bsue[sd]?\b|against|reject|\bden(y|ies|ied)|clos(e|es|ing|ure)|hike|shortage|crisis|\bcuts?\b|fail|delay|worr|fear|scandal|resign|investigat|backlash|petition|demand|unfair|shame|struggl|controvers|problem',re.I)
POS=re.compile(r'prais|celebrat|thank|grateful|honor|award|approv|\bgrants?\b|welcom|success|\bwins?\b|\bwon\b|improv|restor|\bsav(e|es|ed)\b|donat|volunteer|proud|milestone|expan|invest|recogni|hero|kudos|reopen',re.I)
VOICE=re.compile(r'residents?\b|neighbors?\b|parents\b|taxpayers?|public comment|packed|crowd|petition|protest|rall(y|ies)|outcry|speak out|spoke out|voters\b|community members|locals\b|opponents|supporters|homeowners|families\b|town hall|public (hearing|meeting)|letter',re.I)
OPJUNK=re.compile(r'cartoon|horoscope|today in history|bible|crossword|dear abby|thought for',re.I)
def counties_for(t,desc,home,wire):
    text=t+' . '+desc; cs=set()
    for c in COUNTIES:
        if re.search(r'\b%s (County|Co\.)'%re.escape(c),text): cs.add(c)
    for p,c in N.PLACES.items():
        if p in N.STRICT:
            if re.search(r'\b(in|at|of|near) %s\b(?! (County|Daily|Eagle|Times))'%re.escape(p),t): cs.add(c)
        elif re.search(r'\b%s\b'%re.escape(p),t): cs.add(c)
    for m in N.twp_re.finditer(text): cs.add(N.TWP[m.group(1)])
    for m in N.town_re.finditer(t): cs.add(N.TOWN[m.group(1)])
    if not cs and len(home)==1 and not wire: cs=set(home)
    return cs
pool=collections.defaultdict(list)
import os
LAB={}
if os.path.exists('tone_labels.json') and os.path.exists('voice_index.json'):
    ix={r['i']:r['u'] for r in json.load(open('voice_index.json'))}
    LAB={ix[int(i)]:v for i,v in json.load(open('tone_labels.json')).items() if int(i) in ix}
def feed(host,items,op):
    src,home=N.HOME.get(host,(host,[]))
    for t,u,pd,desc in items:
        t=re.sub(r'\s+',' ',t)
        try: d=email.utils.parsedate_to_datetime(pd)
        except Exception: continue
        if d.tzinfo is None: d=d.replace(tzinfo=datetime.timezone.utc)
        if not t or not u.startswith('http') or (N.now-d).days>(45 if op else 10) or N.JUNK.search(t) or OPJUNK.search(t): continue
        if not op and N.SKIP.search(u): continue
        text=t+' . '+desc; wire=bool(N.WIRE.search(text))
        tp=[k for k,rx in TOPICS if rx.search(text)][:2]
        if not tp: continue
        voice=bool(op or VOICE.search(text))
        if op and wire: continue
        lab=LAB.get(u); tone={'f':-1,'p':1}.get(lab[0],0) if lab else 0
        rec={'t':t,'u':u,'s':src,'d':d.astimezone(datetime.timezone(datetime.timedelta(hours=-5))).strftime('%Y-%m-%d')}
        if op: rec['op']=1
        if lab: rec['v']=1; rec['tn']=lab[0]; rec['say']=lab[1]
        rec['_cand']=voice
        for c in counties_for(t,desc,home,wire): pool[c].append((tp,tone,rec))
for host,items in N.RAWITEMS.items(): feed(host,items,False)
nop=0
for f in sorted(glob.glob(RAW+'/feeds/ksop_*.json')):
    for key,items in json.load(open(f,encoding='utf-8')).items():
        feed(key.split('#')[0],[tuple(N.clean(v) for v in i) for i in items],True); nop+=len(items)
def topics(entries,maxn=6):
    seen=set(); T={}
    for tp,tone,rec in entries:
        for k in tp:
            if (k,rec['u']) in seen: continue
            seen.add((k,rec['u']))
            x=T.setdefault(k,{'k':k,'n':0,'o':0,'v':0,'neg':0,'pos':0,'items':[]})
            x['n']+=1; x['o']+=1 if rec.get('op') else 0; x['v']+=1 if rec.get('v') else 0; x['neg']+=tone<0; x['pos']+=tone>0; x['items'].append(rec)
    out=[]
    for x in T.values():
        x['tone']='frustration' if x['neg']>x['pos'] else 'praise' if x['pos']>x['neg'] else 'mixed' if x['v'] else 'news'
        x['w']=x['n']+2*x['v']; x['items']=[{k:v for k,v in r.items() if k!='_cand'} for r in sorted(x['items'],key=lambda r:(r.get('v',0),r['d']),reverse=True)[:10]]
        out.append(x)
    return sorted(out,key=lambda x:-x['w'])[:maxn]
own={c:topics(pool.get(c,[])) for c in COUNTIES}
area={r:topics([e for c in cs for e in pool.get(c,[])],8) for r,cs in N.REG.items()}
area['statewide']=topics([e for c in COUNTIES for e in pool.get(c,[])],8)
reg_of={c:r for r,cs in N.REG.items() for c in cs}
trend={c:({'scope':'own','topics':own[c]} if own[c] else {'scope':'region','topics':area[reg_of[c]][:4]}) for c in COUNTIES}
WEB=json.load(open('web_trend.json',encoding='utf-8')) if os.path.exists('web_trend.json') else {}
for c,items in WEB.items():
    G={}
    for it in items:
        x=G.setdefault(it['k'],{'k':it['k'],'n':0,'o':0,'v':0,'neg':0,'pos':0,'web':1,'items':[]})
        x['n']+=1; x['v']+=1; x['neg']+=it['tn']=='f'; x['pos']+=it['tn']=='p'
        x['items'].append({'t':it['t'],'u':it['u'],'s':it['s'],'d':it['d'],'v':1,'tn':it['tn'],'say':it['say']})
    for x in G.values(): x['tone']='frustration' if x['neg']>x['pos'] else 'praise' if x['pos']>x['neg'] else 'mixed'; x['w']=99
    trend[c]={'scope':'own','topics':list(G.values())+(trend[c]['topics'] if trend[c]['scope']=='own' else [])}
print('web counties',sorted(WEB))
for dst in('../data.json','../site/data.json'):
    D=json.load(open(dst,encoding='utf-8')); D['trend']=trend; D['trendArea']=area
    open(dst,'w',encoding='utf-8').write(json.dumps(D,separators=(',',':'),ensure_ascii=False))
print('opinion items read',nop,'counties with own topics',sum(1 for c in COUNTIES if own[c]),'regional fallback',sorted(c for c in COUNTIES if not own[c]))
print('labeled items',sum(1 for c in COUNTIES for e in pool.get(c,[]) if e[2].get('v')),'opinion kept',sum(1 for c in COUNTIES for e in pool.get(c,[]) if e[2].get('op')))
print('tones',collections.Counter(x['tone'] for c in COUNTIES for x in own[c]))
for c in('Lancaster','Erie','Lawrence','Cumberland','Forest'):
    print(c,trend[c]['scope'],[(x['k'],x['tone'],x['n'],x['v']) for x in trend[c]['topics']])
print([(c,x['k'],x['tone'],r['t'][:80]) for c in COUNTIES for x in own[c] if x['tone'] in('frustration','praise') for r in x['items'][:1] if r.get('v')][:14])

import muni_news; muni_news.build(N, counties_for)
