import json, collections, os
from common import *
sldl,sldu,zipc=geo()
S=json.load(open('state.json')); Fd=json.load(open('fed.json'))
camps={}; tied=collections.defaultdict(set); src={}
N=4
for cid,c in Fd['C'].items():
    k='F'+cid; camps[k]=[c['name'],c['party'],'U.S. House, PA-%d'%c['district']+(' (incumbent)' if c['inc']=='I' else ''),'congress',round(c['raised']),round(c['spent']),round(c['cash']),round(c['pac'])]
    src[k]=c
    for co in Fd['cd'][str(c['district'])]: tied[co].add(k)
state_ids=[]
for fid,f in S['F'].items():
    if not(f['raised']>0 or f['spent']>0): continue
    k='S'+fid; d=f['district']; d=int(d) if d.lstrip('-').isdigit() else 0
    if f['office'] in('GOV','LTG'): lvl,off,cos='statewide',{'GOV':'Governor','LTG':'Lt. Governor'}[f['office']],[]
    elif f['office']=='STH' and 1<=d<=203: lvl,off,cos='legislature','State House, District %d'%d,sldl[d]
    elif f['office']=='STS' and 1<=d<=50: lvl,off,cos='legislature','State Senate, District %d'%d,sldu[d]
    else: lvl,off,cos='county','Committee',[f['county']] if f['county'] else []
    camps[k]=[f['name'],f['party'],off,lvl,round(f['raised']),round(f['spent']),(round(f['cash']) if f['cash']>=0 else None),round(f['pac'])]
    src[k]=f
    for co in cos: tied[co].add(k)
    if lvl=='statewide': state_ids.append(k)
def top(items,keyparty,N=N):
    b=collections.defaultdict(list)
    for it in sorted(items,key=lambda x:-x[-2]):
        p=keyparty(it)
        if len(b[p])<N: b[p].append(it)
    return sorted(sum(b.values(),[]),key=lambda x:-x[-2])
def lists(ids):
    out={'pac':{},'exp':{}}
    for lvl in('congress','statewide','legislature','county'):
        ks=[k for k in ids if camps[k][3]==lvl]
        if not ks: continue
        out['pac'][lvl]=top([[p[1],k,round(p[0]),p[2]] for k in ks for p in src[k]['pacs']],lambda it:camps[it[1]][1])
        out['exp'][lvl]=top([[e[1],e[2],k,round(e[0]),e[3]] for k in ks for e in src[k]['exp']],lambda it:camps[it[2]][1])
    return out
don=collections.defaultdict(lambda:collections.defaultdict(list)); campdon=collections.defaultdict(list)
for a,name,city,st,occ,emp,d,fid,dc in S['don']:
    k='S'+fid
    if k in camps: campdon[k].append([name,', '.join(x for x in(city,st) if x),occ or emp,round(a),d])
    if dc and k in camps: don[dc][camps[k][3]].append([name,city,occ or emp,k,round(a),d])
import glob
cm2c={}
for l in open(RAW+'/ccl26/ccl.txt'):
    p=l.rstrip('\n').split('|')
    if p[0] in Fd['C'] and p[5] in('P','A') and p[2]=='2026': cm2c[p[3]]=p[0]
agg={}
for f in glob.glob('indiv/*.txt'):
    for l in open(f,encoding='latin-1'):
        p=l.rstrip('\n').split('|')
        if p[0] not in cm2c or p[5] not in('15','15E') or p[6]!='IND': continue
        try: a=float(p[14])
        except ValueError: continue
        if a<=0: continue
        key=(p[7],p[10][:5],p[0]); d=dt(p[13][4:8]+p[13][0:4])
        r=agg.setdefault(key,[0.0,'',p[8],p[12],p[11],p[9]])
        r[0]+=a; r[1]=max(r[1],d)
nfed=0
for (name,z,cmte),(a,d,city,occ,emp,st) in agg.items():
    dc=zipc.get(z) if st=='PA' else None
    if a<200: continue
    last,_,first=name.partition(',')
    first=' '.join(w for w in first.split() if w.upper().strip('.') not in('MR','MRS','MS','DR','MISS','HON'))
    nm=nice((first.strip()+' '+last.strip()).strip()); campdon['F'+cm2c[cmte]].append([nm,', '.join(x for x in(nice(city),st) if x),nice(occ or emp)[:40],round(a),d])
    if dc and a>=250: don[dc]['congress'].append([nm,nice(city),nice(occ or emp)[:40],'F'+cm2c[cmte],round(a),d]); nfed+=1
print('federal donor items',nfed)
counties={}
for i,name in enumerate(COUNTIES,1):
    L=lists(tied[i])
    L['don']={lvl:top(v,lambda it:camps[it[3]][1]) for lvl,v in don[i].items()}
    L['camps']=sorted(tied[i],key=lambda k:-camps[k][4])
    counties[name]=L
G=lists(state_ids); G['camps']=sorted(state_ids,key=lambda k:-camps[k][4])
used=set(G['camps'])
for L in counties.values():
    used|=set(L['camps'])
    for v in L['don'].values(): used|={it[3] for it in v}
camps={k:v for k,v in camps.items() if k in used}
meta={'fed_donors':True,'fed_asof':max(c['asof'][6:]+'-'+c['asof'][:2]+'-'+c['asof'][3:5] for c in Fd['C'].values() if c['asof']),'state_export':os.environ.get('STATE_EXPORT','2026-11-06'),'state_through':os.environ.get('STATE_THROUGH','2026-10-19'),'built':os.environ.get('BUILT','2026-11-17')}
out={'meta':meta,'camps':camps,'counties':counties,'state':G}
s=json.dumps(out,separators=(',',':'),ensure_ascii=False)
open('../data.json','w',encoding='utf-8').write(s)
print(len(s),'bytes; camps',len(camps),'levels',collections.Counter(v[3] for v in camps.values()))
for n in('Erie','Forest','Dauphin','Philadelphia'):
    L=counties[n]; print(n,len(L['camps']),{k:len(v) for k,v in L['pac'].items()},{k:len(v) for k,v in L['don'].items()},{k:len(v) for k,v in L['exp'].items()})
print(json.dumps(counties['Erie']['don'],indent=0)[:900]); print([camps[k] for k in counties['Erie']['camps'][:8]]); print([camps[k] for k in G['camps']])

# ---- full-detail files for the site ----
import os, shutil
SITE='../site'; os.makedirs(SITE+'/area',exist_ok=True); os.makedirs(SITE+'/camp',exist_ok=True)  # no deleting: files are overwritten in place
REG={'northeast':['Bradford','Carbon','Lackawanna','Lehigh','Luzerne','Monroe','Northampton','Pike','Schuylkill','Sullivan','Susquehanna','Wayne','Wyoming'],'northwest':['Cameron','Clarion','Crawford','Elk','Erie','Forest','Jefferson','Lawrence','McKean','Mercer','Potter','Venango','Warren'],'southeast':['Berks','Bucks','Chester','Delaware','Lancaster','Montgomery','Philadelphia'],'southwest':['Allegheny','Armstrong','Beaver','Butler','Cambria','Fayette','Greene','Indiana','Somerset','Washington','Westmoreland']}
REG['central']=[c for c in COUNTIES if not any(c in v for v in REG.values())]
assert sum(len(v) for v in REG.values())==67
M=60
def area(idxs):
    ids=set().union(*[tied[i] for i in idxs]); o={'pac':{},'exp':{},'don':{}}
    for lvl in('congress','statewide','legislature','county'):
        ks=state_ids if lvl=='statewide' else [k for k in ids if k in camps and camps[k][3]==lvl]
        ks=[k for k in ks if k in camps]
        o['pac'][lvl]=top([[p[1],k,round(p[0]),p[2]] for k in ks for p in src[k]['pacs']],lambda it:camps[it[1]][1],M)
        o['exp'][lvl]=top([[e[1],e[2],k,round(e[0]),e[3]] for k in ks for e in src[k]['exp']],lambda it:camps[it[2]][1],M)
        o['don'][lvl]=top([it for i in idxs for it in don[i].get(lvl,[]) if it[3] in camps],lambda it:camps[it[3]][1],M)
    return o
dump=lambda p,o:open(p,'w',encoding='utf-8').write(json.dumps(o,separators=(',',':'),ensure_ascii=False))
ix={c:i for i,c in enumerate(COUNTIES,1)}
for c in COUNTIES: dump(SITE+'/area/county-%s.json'%c.lower(),area([ix[c]]))
for r,cs in REG.items(): dump(SITE+'/area/%s.json'%r,area([ix[c] for c in cs]))
dump(SITE+'/area/statewide.json',area(list(range(1,68))))
B=collections.defaultdict(dict)
for k in camps:
    s=src[k]
    B[sum(map(ord,k))%32][k]={'pac':[[p[1],round(p[0]),p[2]] for p in s['pacs'][:50]],'exp':[[e[1],e[2],round(e[0]),e[3]] for e in s['exp'][:50]],'don':sorted(campdon.get(k,[]),key=lambda x:-x[3])[:50]}
for b in range(32): dump(SITE+'/camp/%d.json'%b,B.get(b,{}))
sz=sum(os.path.getsize(os.path.join(d,f)) for d,_,fs in os.walk(SITE) for f in fs)
print('site files',sum(len(fs) for _,_,fs in os.walk(SITE)),'bytes',sz)

# keep the published copy in step; extra.py and trend.py then add townships, news and trending to both
shutil.copyfile('../data.json',SITE+'/data.json')
