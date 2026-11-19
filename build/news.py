import re, os, json, glob, html, email.utils, datetime, collections
from common import *
HOME={'lancasteronline.com':('LNP | LancasterOnline',['Lancaster']),'triblive.com':('TribLive',[]),'penncapital-star.com':('Pennsylvania Capital-Star',[]),'whyy.org':('WHYY',[]),'witf.org':('WITF',[]),'pennlive.com':('PennLive',[]),'lehighvalleylive.com':('lehighvalleylive.com',[]),'yourerie.com':('YourErie.com',['Erie']),'wtaj.com':('WTAJ',[]),'abc27.com':('abc27',[]),'2822news.com':('28/22 News',[]),'dailyitem.com':('The Daily Item',['Northumberland']),'tribdem.com':('The Tribune-Democrat',['Cambria']),'meadvilletribune.com':('The Meadville Tribune',['Crawford']),'sharonherald.com':('The Herald',['Mercer']),'ncnewsonline.com':('New Castle News',['Lawrence']),'thecourierexpress.com':('The Courier Express',['Clearfield']),'indianagazette.com':('The Indiana Gazette',['Indiana']),'gettysburgtimes.com':('Gettysburg Times',['Adams']),'cumberlink.com':('The Sentinel',['Cumberland']),'thedailyreview.com':('The Daily Review',['Bradford']),'thederrick.com':('The Derrick',['Venango']),'huntingdondailynews.com':('The Daily News',['Huntingdon']),'observer-reporter.com':('Observer-Reporter',['Washington']),'altoonamirror.com':('Altoona Mirror',['Blair']),'sungazette.com':('Williamsport Sun-Gazette',['Lycoming']),'statecollege.com':('StateCollege.com',['Centre']),'lebtown.com':('LebTown',['Lebanon']),'spotlightpa.org':('Spotlight PA',[]),
'northcentralpa.com':('NorthcentralPa.com',[]),'levittownnow.com':('LevittownNow.com',['Bucks']),'6abc.com':('6abc',[]),'wesb.com':('WESB',['McKean']),'wfmz.com':('WFMZ',[]),'fultoncountynews.com':('Fulton County News',['Fulton']),'nbcphiladelphia.com':('NBC10 Philadelphia',[]),'wnep.com':('WNEP',[]),'timesobserver.com':('Times Observer',['Warren']),'mychesco.com':('MyChesCo',[]),'lockhaven.com':('The Express',['Clinton']),'tiogapublishing.com':('Tioga Publishing',['Tioga']),'northpennnow.com':('North Penn Now',['Montgomery']),'butlerradio.com':('Butler Radio',['Butler']),'lewistownsentinel.com':('The Sentinel (Lewistown)',['Mifflin']),'susqcoindy.com':('Susquehanna County Independent',['Susquehanna']),'gantnews.com':('GantNews',['Clearfield']),'yourdailylocal.com':('Your Daily Local',['Warren']),'heraldstandard.com':('Herald-Standard',['Fayette']),'beavercountian.com':('BeaverCountian.com',['Beaver']),'connectradio.fm':('Connect FM',[])}
STATEWIDE={'spotlightpa.org','penncapital-star.com','witf.org'}
PLACES={'Pittsburgh':'Allegheny','Harrisburg':'Dauphin','Hershey':'Dauphin','Scranton':'Lackawanna','Allentown':'Lehigh','Bethlehem':'Northampton','Easton':'Northampton','Wilkes-Barre':'Luzerne','Hazleton':'Luzerne','Williamsport':'Lycoming','Gettysburg':'Adams','Doylestown':'Bucks','Norristown':'Montgomery','West Chester':'Chester','Stroudsburg':'Monroe','Pottsville':'Schuylkill','Sunbury':'Northumberland','Shamokin':'Northumberland','Lewisburg':'Union','Bloomsburg':'Columbia','Danville':'Montour','Towanda':'Bradford','Tunkhannock':'Wyoming','Honesdale':'Wayne','Jim Thorpe':'Carbon','Bellefonte':'Centre','State College':'Centre','Penn State':'Centre','Lock Haven':'Clinton','Wellsboro':'Tioga','Coudersport':'Potter','Smethport':'McKean','Emporium':'Cameron','Ridgway':'Elk','St. Marys':'Elk','Brookville':'Jefferson','Punxsutawney':'Jefferson','DuBois':'Clearfield','Tionesta':'Forest','Oil City':'Venango','Meadville':'Crawford','Titusville':'Crawford','New Castle':'Lawrence','Hermitage':'Mercer','Kittanning':'Armstrong','Uniontown':'Fayette','Waynesburg':'Greene','Greensburg':'Westmoreland','Johnstown':'Cambria','Ebensburg':'Cambria','Altoona':'Blair','Hollidaysburg':'Blair','Chambersburg':'Franklin','McConnellsburg':'Fulton','Mifflintown':'Juniata','Lewistown':'Mifflin','Selinsgrove':'Snyder','Middleburg':'Snyder','New Bloomfield':'Perry','Carlisle':'Cumberland','Mechanicsburg':'Cumberland','Philadelphia':'Philadelphia','Philly':'Philadelphia','Delco':'Delaware','Montco':'Montgomery','Poconos':'Monroe','Erie':'Erie','Lancaster':'Lancaster','Reading':'Berks','Lebanon':'Lebanon','York':'York'}
STRICT={'Erie','Lancaster','Reading','Lebanon','York'}
subs=collections.defaultdict(set)
for i,l in enumerate(open(RAW+'/pa_cousub.txt',encoding='utf-8-sig')):
    p=l.rstrip('\n').split('|')
    if i==0: h=p; ni=[k for k,x in enumerate(h) if x.startswith('NAMELSAD_COUSUB')][0]; gi=[k for k,x in enumerate(h) if x.startswith('GEOID_COUSUB')][0]; continue
    m=re.match(r'(.+) (township|borough|city|town|municipality)$',p[ni])
    if m: subs[(m.group(1),m.group(2))].add(COUNTIES[(int(p[gi][2:5])+1)//2-1])
byname=collections.defaultdict(set)
for (n,t),cs in subs.items(): byname[n]|=cs
STOP=set(COUNTIES)|{'Liberty','Jackson','Madison','Houston','Dallas','California','Export','Paradise','Freedom','Industry','Prospect','Homestead','Mars','Media','Chester','Delta','Economy','Progress','Enon Valley','Summit','Center','Centre','Highland','Pleasant','Fairview','Franklin','Washington','Jefferson','Lincoln','Hanover','Newtown','Milford','Oxford','Bristol','Richland','Salem','Springfield','Union','Hamilton','Clinton','Marion','Monroe','Girard','Troy','Athens','Rome','Moscow','Dover','Avalon','Carbondale','Mount Pleasant','Middletown'}
TWP={n:next(iter(cs)) for (n,t),cs in subs.items() if t=='township' and len(cs)==1}
TOWN={n:next(iter(cs)) for (n,t),cs in subs.items() if t in('borough','city','town','municipality') and len(byname[n])==1 and len(n)>=7 and n not in STOP and n not in PLACES}
print('municipalities',len(subs),'unique townships',len(TWP),'unique towns',len(TOWN))
twp_re=re.compile(r'\b('+'|'.join(sorted(map(re.escape,TWP),key=len,reverse=True))+r') (?:Township|Twp\b\.?)')
town_re=re.compile(r'\b('+'|'.join(sorted(map(re.escape,TOWN),key=len,reverse=True))+r')\b(?! (?:County|Township|Twp))')
SKIP=re.compile(r'/(sports?|obituar|lifestyle|entertainment|opinion|nation|world|national|ap|classifieds|community/announce|weather|video|podcast|arts_and_living|business/national)[/_-]',re.I)
WIRE=re.compile(r'\(AP\)|Associated Press|\bTrump\b|White House|Ukrain|Russia|\bChina\b|Israel|Gaza|\bIran\b|Supreme Court|Wall Street|\bNFL\b|\bNBA\b|Hollywood|Pentagon|\bXi\b|Yemen|Venezuela|Middle East|\bU\.?N\.?\b')
JUNK=re.compile(r"top stories|forecast|obituar|horoscope|property transfers|police (log|blotter)|newsletter|lottery|crossword|birth announcements|photo gallery",re.I)
KW=re.compile(r'council|commission|budget|election|tax|school board|school district|mayor|senat|state rep|township|borough|supervisor|district attorney|judge|court|county|legislat|governor|congress|zoning|vote|candidate|ballot|republican|democrat|shapiro|funding|ordinance|authority|police|sheriff|grant',re.I)
now=datetime.datetime.now(datetime.timezone.utc)  # was fixed at 2026-11-18; changed 2026-11-19 so daily pulls are not dropped as future-dated
clean=lambda s:html.unescape(re.sub(r'<[^>]+>',' ',re.sub(r'<!\[CDATA\[(.*?)\]\]>',r'\1',s,flags=re.S))).strip()
RAWITEMS=collections.defaultdict(list)
for f in sorted(glob.glob(RAW+'/feeds/ksfeed_*.xml')):
    host=os.path.basename(f)[7:-4]; x=open(f,encoding='utf-8',errors='replace').read()
    for it in re.findall(r'<item[\s>].*?</item>',x,re.S):
        g=lambda tag:(re.search(r'<%s[^>]*>(.*?)</%s>'%(tag,tag),it,re.S) or [None,''])[1]
        RAWITEMS[host].append((clean(g('title')),clean(g('link')),clean(g('pubDate')),clean(g('description'))[:300]))
for f in sorted(glob.glob(RAW+'/feeds/ksnews*.json')):
    for host,items in json.load(open(f,encoding='utf-8')).items(): RAWITEMS[host]+=[tuple(clean(v) for v in i) for i in items]
# merge pulls instead of letting whichever file sorts last win; one row per link (changed 2026-11-19)
for host in list(RAWITEMS):
    _seen=set(); RAWITEMS[host]=[r for r in RAWITEMS[host] if not (r[1] in _seen or _seen.add(r[1]))]
out=collections.defaultdict(list); statepool=[]; stats={}
for host,items in RAWITEMS.items():
    src,home=HOME.get(host,(host,[])); n=0
    for t,u,pd,desc in items:
        t=re.sub(r'\s+',' ',t)
        try: d=email.utils.parsedate_to_datetime(pd)
        except Exception: continue
        if d.tzinfo is None: d=d.replace(tzinfo=datetime.timezone.utc)
        age=(now-d).days
        if not t or not u.startswith('http') or age>10 or d>now+datetime.timedelta(hours=6) or SKIP.search(u) or JUNK.search(t): continue
        text=t+' . '+desc; cs=set()
        for c in COUNTIES:
            if re.search(r'\b%s (County|Co\.)'%re.escape(c),text): cs.add(c)
        for p,c in PLACES.items():
            if p in STRICT:
                if re.search(r'\b(in|at|of|near) %s\b(?! (County|Daily|Eagle|Times))'%re.escape(p),t) or re.search(r'\bCity of %s\b'%p,text): cs.add(c)
            elif re.search(r'\b%s\b'%re.escape(p),t): cs.add(c)
        for m in twp_re.finditer(text): cs.add(TWP[m.group(1)])
        for m in town_re.finditer(t): cs.add(TOWN[m.group(1)])
        wire=bool(WIRE.search(text))
        if not cs and len(home)==1 and not wire: cs=set(home)
        rec={'t':t,'u':u,'s':src,'d':d.astimezone(datetime.timezone(datetime.timedelta(hours=-5))).strftime('%Y-%m-%d')}
        if host in STATEWIDE and age<=5 and not wire: statepool.append(rec)
        for c in cs: out[c].append(rec); n+=1
    stats[host]=n
def rank(v):
    seen=set(); L=[]
    for x in sorted(v,key=lambda x:(x['d'],bool(KW.search(x['t']))),reverse=True):
        k=x['t'].lower()[:60]
        if k in seen: continue
        seen.add(k); L.append(x)
    return L
REG={'northeast':['Bradford','Carbon','Lackawanna','Lehigh','Luzerne','Monroe','Northampton','Pike','Schuylkill','Sullivan','Susquehanna','Wayne','Wyoming'],'northwest':['Cameron','Clarion','Crawford','Elk','Erie','Forest','Jefferson','Lawrence','McKean','Mercer','Potter','Venango','Warren'],'southeast':['Berks','Bucks','Chester','Delaware','Lancaster','Montgomery','Philadelphia'],'southwest':['Allegheny','Armstrong','Beaver','Butler','Cambria','Fayette','Greene','Indiana','Somerset','Washington','Westmoreland']}
REG['central']=[c for c in COUNTIES if not any(c in v for v in REG.values())]
own={c:rank(out.get(c,[])) for c in COUNTIES}
state=rank(statepool); news={}
for r,cs in REG.items():
    pool=rank([x for c in cs for x in own[c] if KW.search(x['t'])])
    for c in cs:
        L=[dict(x) for x in own[c][:20]]; have={x['u'] for x in L}
        if len(L)<3:
            for x in pool:
                if len([y for y in L if y.get('scope')=='region'])>=3: break
                if x['u'] not in have: L.append(dict(x,scope='region')); have.add(x['u'])
            for x in state:
                if len(L)>=6: break
                if x['u'] not in have: L.append(dict(x,scope='state')); have.add(x['u'])
        news[c]=L
for dst in('../data.json','../site/data.json'):
    D=json.load(open(dst,encoding='utf-8')); D['news']=news; D['meta']['news_pulled']=now.astimezone(datetime.timezone(datetime.timedelta(hours=-5))).strftime('%Y-%m-%d'); D['meta']['news_sources']=sorted(set(HOME[h][0] for h,n in stats.items() if n and h in HOME))
    open(dst,'w',encoding='utf-8').write(json.dumps(D,separators=(',',':'),ensure_ascii=False))
print({h:n for h,n in stats.items()})
cnt={c:len(own[c]) for c in COUNTIES}
print('own>=3:',sum(1 for v in cnt.values() if v>=3),'own 1-2:',sorted(c for c,v in cnt.items() if 0<v<3),'own 0:',sorted(c for c,v in cnt.items() if v==0))
print('min shown',min(len(v) for v in news.values()),'sources',len(D['meta']['news_sources']))
for c in('Forest','Cameron','Bucks','Delaware','Lawrence','Tioga'): print(c,[(x['s'],x.get('scope','own'),x['t'][:60]) for x in news[c][:4]])
