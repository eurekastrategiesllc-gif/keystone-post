# Consultant scoreboard, step 1: candidates, results and which committee belongs to which candidate.
import json, re, collections, os
from common import *
import glob
_rf=sorted(glob.glob(os.path.join(RAW,'pa_results_*.json')))[-1]   # newest results pull
RESULTS_DATE=re.search(r'(\d{4}-\d\d-\d\d)',os.path.basename(_rf)).group(1)
R=json.load(open(_rf))['races']
OFF={'G':'GOV','L':'LTG','C':'USC','S':'STS','H':'STH'}
SUF={'JR','SR','II','III','IV'}
def toks(n):
    n=re.sub(r"[^A-Z' -]",' ',html.unescape(n).upper()).replace("'",'')
    return [w for w in re.split(r'[\s]+',n) if w]
def last(n):
    t=[w for w in toks(n) if w not in SUF]
    return t[-1] if t else ''
def first(n):
    t=toks(n); return t[0] if t else ''
C={}   # key (office,district,name) -> candidate
def cand(off,d,name,party):
    k=(off,d,name)
    return C.setdefault(k,{'name':name,'office':off,'district':d,'party':party,'prim':None,'gen':None,'margin':None,'opp':None})
for k,cs in R.items():
    t,off,d=k[0],OFF[k[1]],int(k[2:])
    if t=='P':
        byp=collections.defaultdict(list)
        for p,n,v in cs: byp[p].append((v,n))
        for p,l in byp.items():
            l.sort(reverse=True)
            for i,(v,n) in enumerate(l):
                c=cand(off,d,n,p); c['prim']='U' if len(l)==1 else ('W' if i==0 else 'L')
                if len(l)>1: c['pmargin']=round(100*(l[0][0]-(l[1][0] if i==0 else v))/sum(x[0] for x in l),1)
    else:
        tot=sum(v for _,_,v in cs); o=sorted(cs,key=lambda x:-x[2])
        for i,(p,n,v) in enumerate(o):
            p1={'DEM':'D','REP':'R','D+R':'D'}.get(p,'O')
            c=C.get((off,d,n)) or cand(off,d,n,p1)
            if p=='D+R': c['cross']=True
            c['gen']='W' if i==0 else 'L'
            c['margin']=None if len(o)==1 else round(100*(o[0][2]-(o[1][2] if i==0 else v))/tot,1)
            c['opp']=len(o)>1
# Lt. Governor rides with the governor ticket in November
gw=[c for c in C.values() if c['office']=='GOV' and c['gen']=='W'][0]
for c in C.values():
    if c['office']=='LTG' and c['prim'] in('W','U'): c['gen']='W' if c['party']==gw['party'] else 'L'; c['margin']=[x['margin'] for x in C.values() if x['office']=='GOV' and x['party']==c['party']][0]; c['opp']=True
def outcome(c):
    if c['gen']=='W': return 'W'
    if c['prim']=='L': return 'LP'
    if c['gen']=='L': return 'LG'
    return None   # won a primary but not on the November ballot
for c in C.values(): c['out']=outcome(c)
if __name__=='__main__':
    print('candidates',len(C),collections.Counter((c['office'],c['out']) for c in C.values()))
    print('no outcome',[(c['name'],c['office'],c['district']) for c in C.values() if not c['out']])
# ---- committees ----
S=json.load(open('state.json'))['F']; Fd=json.load(open('fed.json'))['C']
byseat=collections.defaultdict(list)
for c in C.values(): byseat[(c['office'],c['district'])].append(c)
NICK=[('TOM','THOMAS','TOMMY'),('MIKE','MICHAEL'),('JOE','JOSEPH'),('JIM','JAMES','JAMIE'),('BILL','WILLIAM','WILL'),('BOB','ROBERT','ROB'),('DAVE','DAVID'),('PAT','PATRICK','PATRICIA'),('CHRIS','CHRISTOPHER','CHRISTINE','CHRISTINA'),('DAN','DANIEL'),('MATT','MATTHEW'),('STEVE','STEVEN','STEPHEN'),('GREG','GREGORY'),('TIM','TIMOTHY'),('RICH','RICHARD','RICK'),('ED','EDWARD'),('KEN','KENNETH'),('JEFF','JEFFREY'),('NICK','NICHOLAS'),('TONY','ANTHONY'),('KATE','KATHRYN','KATIE','KATHLEEN','KATHY'),('LIZ','ELIZABETH','BETH'),('JEN','JENNIFER'),('BEN','BENJAMIN'),('ANDY','ANDREW'),('JON','JONATHAN'),('RON','RONALD'),('JOSH','JOSHUA'),('ZACH','ZACHARY'),('ART','ARTHUR'),('MARTY','MARTIN'),('SAM','SAMUEL','SAMANTHA'),('ABBY','ABIGAIL'),('MANDY','AMANDA'),('BRAD','BRADLEY'),('JAKE','JACOB'),('NATE','NATHAN'),('PETE','PETER'),('DON','DONALD'),('JACK','JOHN'),('LARRY','LAWRENCE'),('CHUCK','CHARLES','CHARLIE'),('ALEX','ALEXANDER'),('JESS','JESSICA'),('DEB','DEBORAH','DEBBIE'),('SUE','SUSAN'),('RAY','RAYMOND'),('FRED','FREDERICK'),('AL','ALAN','ALBERT'),('GT','GLENN')]
def nick(f):
    out={f}
    for g in NICK:
        if f in g: out|=set(g)
    return out
STOP=set("FRIENDS FRIEND OF FOR PA STATE REP REPRESENTATIVE SENATE SENATOR HOUSE CITIZENS PEOPLE TO ELECT REELECT RE-ELECT COMMITTEE COM VOTE TEAM TOGETHER TAXPAYERS IM THE LEGISLATURE DISTRICT PENNSYLVANIA CAMPAIGN NEIGHBORS".split())
BLOCK={'PEOPLE FOR PARKER'}
# hand-checked committees whose names the rules cannot read
OVERRIDE={'PATRIOTS FOR COLEMAN':('STS',16,'JARRETT COLEMAN'),'FRIENDS OF MEGAN GS':('STH',148,'MEGAN GRIFFIN-SHELLEY'),'CE-CE FOR PA':('STH',22,'CE-CE GERLACH'),'WAXPAC':('STH',182,'BEN WAXMAN')}
link={}   # camp key -> candidate key
how={}    # camp key -> how it was matched: seat, name, surname
amb=[]
def ntok(c):
    t=[w for w in toks(c['name']) if w not in SUF]
    out=set()
    for w in t[1:]:
        if len(w)>=3: out.add(w)
        for p in w.split('-'):
            if len(p)>3: out.add(p)
    return t[0] if t else '', out
def pick(cs,name,party=None):
    T=set(toks(name)); T|={w.replace('-','') for w in T}; flat=re.sub(r'[^A-Z]','',name.upper())
    sc=[]
    for c in cs:
        f,ls=ntok(c)
        s=3*len(ls&T)+(1 if (nick(f)&T) and len(f)>1 else 0)
        if not s and any(len(w)>=5 and w.replace('-','') in flat for w in ls|{f}): s=1
        if s and party in('R','D') and c['party'] in('R','D') and c['party']!=party: s-=0.5
        if s>0: sc.append((s,c))
    if not sc: return []
    m=max(s for s,_ in sc)
    return [c for s,c in sc if s==m]
def setlink(k,hit,h,f):
    if h=='seat' and len(hit)==1 and not (ntok(hit[0])[1]&(set(toks(f['name']))|{w.replace('-','') for w in toks(f['name'])})): h='first'
    if len(hit)==1: link[k]=(hit[0]['office'],hit[0]['district'],hit[0]['name']); how[k]=h
    elif len(hit)>1: amb.append((f['name'],h,[x['name'] for x in hit]))
act={fid:f for fid,f in S.items() if f['raised']>0 or f['spent']>0}
for fid,f in act.items():
    if f['name'].upper() in OVERRIDE: link['S'+fid]=OVERRIDE[f['name'].upper()]; how['S'+fid]='hand'; assert link['S'+fid] in C
for fid,f in act.items():
    if 'S'+fid in link: continue
    d=f['district']; d=int(d) if d.lstrip('-').isdigit() else 0
    off=f['office']
    if off in('GOV','LTG'): d=0
    if off in('GOV','LTG','STS','STH') and byseat.get((off,d)): setlink('S'+fid,pick(byseat[(off,d)],f['name'],f['party']),'seat',f)
for cid,c in Fd.items(): setlink('F'+cid,pick(byseat.get(('USC',c['district']),[]),c['name'],c['party']),'seat',c)
# no usable seat on the filing: match on first and last name, only when exactly one candidate fits
allc=[c for c in C.values() if c['office']!='USC']
CW=re.compile(r"\b(FRIENDS?|CITIZENS|COMMITTEE|COM|ELECT|RE-?ELECT|PEOPLE|NEIGHBORS|FOR|4|TEAM|VOTE|CAMPAIGN|SENATE|REP|STATE|TOGETHER|FORWARD)\b")
NOT=re.compile(r"\b(PAC|PARTY|DEMOCRATIC COM|REP COM|REPUBLICAN COM|COUNTY|TOWNSHIP|TWP|BOROUGH|LOCAL|UNION|ASSOCIATION|ASSN|CLUB|COUNCIL|WARD|CONGRESS|JUDGE|MAYOR|CO)\b")
lastn=collections.Counter(last(c['name']) for c in allc)
for fid,f in act.items():
    k='S'+fid
    if k in link or f['type'] not in('1','2'): continue
    U=f['name'].upper(); T=set(toks(U))
    if f['type']=='2' and not CW.search(U): continue
    hit=[c for c in allc if last(c['name']) in T and (nick(first(c['name']))&T) and (f['office'] in('',c['office']))]
    if hit: setlink(k,hit,'name',f); continue
    if NOT.search(U) or U in BLOCK or f['office'] not in('','STH','STS'): continue
    hit=[]
    for c in allc:
        l=last(c['name'])
        if l in T and len(l)>=5 and lastn[l]==1 and f['party'] in(c['party'],'O') and f['office'] in('',c['office']):
            rest=T-STOP-set(toks(c['name']))-{w for w in T if w.isdigit()}
            if not rest or (len(rest)==1 and rest<=nick(first(c['name']))): hit.append(c)
    if hit: setlink(k,hit,'surname',f)
if __name__=='__main__':
    print('linked',len(link),collections.Counter(k[0] for k in link))
    lc=collections.Counter(link.values()); print('candidates with a committee',len(lc),'of',len(C),'; with 2+',sum(1 for v in lc.values() if v>1))
    print('ambiguous',len(amb),amb[:25])
    un=[(f['name'],f['office'],f['district'],f['party'],round(f['spent'])) for fid,f in S.items() if f['office'] in('GOV','LTG','STS','STH') and 'S'+fid not in link and f['spent']>20000]
    print('office filers unlinked, spent over 20k:',len(un)); [print('  ',u) for u in sorted(un,key=lambda u:-u[4])[:45]]
    un=[(c['name'],c['district'],c['party'],round(c['spent'])) for cid,c in Fd.items() if 'F'+cid not in link]
    print('fed unlinked',len(un),sorted(un,key=lambda u:-u[3])[:25])
    nc=[(c['name'],c['office'],c['district'],c['party'],c['out']) for k,c in C.items() if k not in lc and c['opp'] and c['margin'] is not None and c['margin']<10]
    print('close-race candidates with no committee found',len(nc),nc[:40])
    print(collections.Counter(how.values()))
    ex=[(f['name'],f['party'],round(f['spent']),link['S'+fid]) for fid,f in S.items() if how.get('S'+fid)=='surname']
    print('linked by surname only',len(ex)); [print('  ',e) for e in sorted(ex,key=lambda x:-x[2])]
    ex=[(f['name'],f['party'],f['office'],f['district'],round(f['spent']),link['S'+fid][2]) for fid,f in S.items() if how.get('S'+fid)=='first']
    print('linked in-seat on first name or spelling only',len(ex)); [print('  ',e) for e in sorted(ex,key=lambda x:-x[4])]
    ex=[(f['name'],f['party'],round(f['spent']),link['S'+fid],C[link['S'+fid]]['party']) for fid,f in S.items() if how.get('S'+fid)=='name' and f['party'] in('R','D') and C[link['S'+fid]]['party']!=f['party']]
    print('name pass with party mismatch',ex)
