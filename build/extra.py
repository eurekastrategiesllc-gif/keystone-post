"""Extra detail files: PAC and committee profiles, donor giving histories, townships and boroughs.

Run in build/ after merge.py (it reads ../data.json) and before news.py / trend.py:
  python3 extra.py
Writes ../site/pac/*.json, ../site/donor/*.json, ../site/muni/county-*.json and adds a
"munis" index to ../data.json and ../site/data.json.
Donor profiles carry name, city, state, occupation or employer and gifts only. No street
addresses, phone numbers or emails of individuals are written anywhere.
"""
import csv, collections, json, os, re, glob, shutil
from common import *
csv.field_size_limit(10**9)
HERE=os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
sldl,sldu,zipc=geo()
D=json.load(open('../data.json',encoding='utf-8')); camps=D['camps']
S=json.load(open('state.json')); Fd=json.load(open('fed.json'))
slug=lambda s: re.sub(r'[^a-z0-9]+','-',(s or '').lower()).strip('-')
P=os.path.join(RAW,'pa_dos_2026')
rows=list(csv.DictReader(open(P+'/filer_2026.txt',encoding='latin-1')))
CYC={'1','2','3','4','5','6'}; keep={}
for r in rows:
    if r['CYCLE'] not in CYC: continue
    k=(r['FILERID'],r['CYCLE'])
    if k not in keep or int(r['CampaignfinanceID'])>int(keep[k]['CampaignfinanceID']): keep[k]=r
kept={r['CampaignfinanceID'] for r in keep.values()}
filer={}
for r in sorted(keep.values(),key=lambda r:int(r['CYCLE'])): filer[r['FILERID']]=r
def addr(*parts):
    a1,a2,city,st,z=[(p or '').strip() for p in parts]; z=re.sub(r'\D','',z)
    z=z[:5]+('-'+z[5:9] if len(z)>=9 else '') if len(z)>=5 else ''
    line2=' '.join(x for x in(', '.join(x for x in(nice(city),st.upper()) if x),z) if x)
    return [x for x in(nice(a1),nice(a2),line2) if x]

PAC={}; DON={}
def pac(name):
    k=slug(name)
    return PAC.setdefault(k,{'n':name,'g':[],'_a':collections.Counter()}) if k else None
def donor(name,city,st,occ):
    k=slug(name)+'--'+slug(city)
    if not slug(name): return None
    d=DON.setdefault(k,{'n':name,'c':', '.join(x for x in(city,st) if x),'o':'','g':[],'_big':False})
    if occ and not d['o']: d['o']=occ
    return d
# ---- state filings ----
n=0
for r in csv.DictReader(open(P+'/contrib_2026.txt',encoding='latin-1')):
    if r['CampaignFinanceID'] not in kept: continue
    k='S'+r['FilerID']
    if k not in camps: continue
    a=sum(float(r[x] or 0) for x in('CONTAMT1','CONTAMT2','CONTAMT3'))
    if a<=0: continue
    sec=r['Section']; d=dt(r['CONTDATE1']); n+=1
    if sec in('IA','IC'):
        p=pac(nice(r['CONTRIBUTOR']))
        if p:
            p['g'].append([k,round(a),d]); ad=addr(r['ADDRESS1'],r['ADDRESS2'],r['CITY'],r['STATE'],r['ZIPCODE'])
            if ad: p['_a']['\n'.join(ad)]+=1
    elif sec in('IB','ID'):
        x=donor(nice(r['CONTRIBUTOR']),nice(r['CITY']),r['STATE'].strip().upper(),(nice(r['OCCUPATION']) or nice(r['ENAME']))[:40])
        if x:
            x['g'].append([k,round(a),d])
            if a>=250: x['_big']=True
print('state contribution rows',n)
# ---- federal filings ----
cm={}
for l in open(RAW+'/cm26/cm.txt',encoding='latin-1'):
    p=l.rstrip('\n').split('|'); cm[p[0]]=p
for l in open(RAW+'/pas226/itpas2.txt',encoding='latin-1'):
    p=l.split('|')
    if p[16] in Fd['C'] and p[5]=='24K' and 'F'+p[16] in camps:
        a=float(p[14] or 0)
        if a<=0: continue
        c=cm.get(p[0]); x=pac(nice(c[1]) if c else p[0])
        if not x: continue
        x['g'].append(['F'+p[16],round(a),dt(p[13][4:8]+p[13][0:4])])
        if c and 'fec' not in x:
            last,_,first=c[2].partition(',')
            x['fec']=p[0]; x['t']=nice((first.strip()+' '+last.strip()).strip()); x['a']=addr(c[3],c[4],c[5],c[6],c[7])
            if len(c)>13 and c[13].strip() and c[13].strip().upper()!='NONE': x['org']=nice(c[13])
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
feddon=[]
for (name,z,cmte),(a,d,city,occ,emp,st) in agg.items():
    if a<200 or 'F'+cm2c[cmte] not in camps: continue
    last,_,first=name.partition(',')
    first=' '.join(w for w in first.split() if w.upper().strip('.') not in('MR','MRS','MS','DR','MISS','HON'))
    nm=nice((first.strip()+' '+last.strip()).strip()); o=nice(occ or emp)[:40]
    x=donor(nm,nice(city),st,o)
    if x: x['g'].append(['F'+cm2c[cmte],round(a),d]); x['_big']=True
    feddon.append((a,nm,nice(city),st,o,d,'F'+cm2c[cmte],zipc.get(z) if st=='PA' else None))
# ---- committees that are also state filers: use the address on their own report ----
fname={}
for fid,r in filer.items():
    if 'S'+fid in camps: fname.setdefault(slug(nice(r['FILERNAME'])),fid)
for k,p in PAC.items():
    fid=fname.get(k)
    if fid:
        p['id']='S'+fid
        if 'a' not in p:
            r=filer[fid]; ad=addr(r['ADDRESS1'],r['ADDRESS2'],r['CITY'],r['STATE'],r['ZIPCODE'])
            if ad: p['a']=ad; p['asrc']='own'
    if 'a' not in p and p['_a']:
        p['a']=p['_a'].most_common(1)[0][0].split('\n'); p['asrc']='given'
    elif 'a' in p and 'asrc' not in p: p['asrc']='fec'
def finish(x,cap=200):
    g=sorted(x['g'],key=lambda r:(-r[1],r[2])); x['tot']=sum(r[1] for r in g); x['cnt']=len(g); x['g']=g[:cap]
    for k in [k for k in x if k[0]=='_']: del x[k]
    return x
def write(folder,items,nb):
    os.makedirs('../site/'+folder,exist_ok=True)
    B=collections.defaultdict(dict)
    for k,v in items.items(): B[sum(map(ord,k))%nb][k]=v
    sz=0
    for b in range(nb):
        s=json.dumps(B.get(b,{}),separators=(',',':'),ensure_ascii=False); sz+=len(s.encode())
        open('../site/%s/%d.json'%(folder,b),'w',encoding='utf-8').write(s)
    print(folder,len(items),'profiles in',nb,'files,',sz,'bytes')
PACo={k:finish(dict(v)) for k,v in PAC.items()}
write('pac',PACo,32)
DONo={k:finish(dict(v)) for k,v in DON.items() if v['_big']}
write('donor',DONo,128)
# ---- townships and boroughs ----
MUNI=collections.defaultdict(list)
for i,l in enumerate(open(RAW+'/pa_cousub.txt',encoding='utf-8-sig')):
    p=l.rstrip('\n').split('|')
    if i==0: h=p; ni=[k for k,x in enumerate(h) if x.startswith('NAMELSAD_COUSUB')][0]; gi=[k for k,x in enumerate(h) if x.startswith('GEOID_COUSUB')][0]; continue
    m=re.match(r'(.+) (township|borough|city|town|municipality)$',p[ni])
    if m:
        ci=(int(p[gi][2:5])+1)//2
        if (m.group(1),m.group(2)) not in [(a,b) for a,b,_ in MUNI[ci]]: MUNI[ci].append((m.group(1),m.group(2),slug(m.group(1)+' '+m.group(2))))
def place(ci,city):
    cn=(city or '').lower().strip(); twp=bool(re.search(r'\b(twp|township)\b',cn))
    base=re.sub(r'\b(twp|township|boro|borough|city)\b\.?','',cn).strip(' ,.')
    base=re.sub(r'^mt\.? ','mount ',base); base=re.sub(r'^st\.? ','saint ',base)
    norm=lambda s:re.sub(r'^st\.? ','saint ',re.sub(r'^mt\.? ','mount ',s.lower()))
    c=[m for m in MUNI.get(ci,[]) if norm(m[0])==base]
    if not c: return None
    pref=[m for m in c if (m[1]=='township')==twp]
    return (pref or c)[0][2]
M=collections.defaultdict(lambda:collections.defaultdict(lambda:{'don':[],'names':set(),'tot':0}))
for a,name,city,st,occ,emp,d,fid,dc in S['don']:
    k='S'+fid
    if dc and k in camps:
        mk=place(dc,city)
        if mk: x=M[dc][mk]; x['don'].append([name,occ or emp,k,round(a),d,city]); x['names'].add(name); x['tot']+=round(a)
for a,nm,city,st,o,d,k,dc in feddon:
    if dc and a>=250:
        mk=place(dc,city)
        if mk: x=M[dc][mk]; x['don'].append([nm,o,k,round(a),d,city]); x['names'].add(nm); x['tot']+=round(a)
os.makedirs('../site/muni',exist_ok=True); index={}; placed=0
for ci,cname in enumerate(COUNTIES,1):
    local=[k for k in D['counties'][cname]['camps'] if camps[k][3]=='county']
    out={}; idx=[]; shared=collections.Counter(m[0] for m in MUNI[ci])
    for base,typ,mk in sorted(MUNI[ci]):
        x=M[ci].get(mk,{'don':[],'names':set(),'tot':0}); cmt=[]
        if len(base)>=5 and base!=cname:
            rx=re.compile(r'\b'+re.escape(base)+r'\b',re.I)
            for k in local:
                nm=camps[k][0]
                if not rx.search(nm): continue
                says_twp=bool(re.search(r'\b(twp|township)\b',nm,re.I)); says_boro=bool(re.search(r'\b(boro|borough|city)\b',nm,re.I))
                if shared[base]>1 and ((says_twp and typ!='township') or (says_boro and typ=='township')): continue
                cmt.append(k)
        if x['don'] or cmt:
            out[mk]={'don':sorted(x['don'],key=lambda r:-r[3])[:40],'nd':len(x['names']),'tot':x['tot'],'cm':cmt}; placed+=len(x['don'])
        idx.append([mk,base,typ,len(x['names']),x['tot'],len(cmt)])
    open('../site/muni/county-%s.json'%cname.lower(),'w',encoding='utf-8').write(json.dumps(out,separators=(',',':'),ensure_ascii=False))
    index[cname]=idx
print('municipalities',sum(len(v) for v in index.values()),'with donors',sum(1 for v in index.values() for r in v if r[3]),'with committees',sum(1 for v in index.values() for r in v if r[5]),'gifts placed',placed,'of',sum(1 for r in S['don'] if r[8])+sum(1 for r in feddon if r[7] and r[0]>=250))
for dst in('../data.json','../site/data.json'):
    X=json.load(open(dst,encoding='utf-8')); X['munis']=index
    open(dst,'w',encoding='utf-8').write(json.dumps(X,separators=(',',':'),ensure_ascii=False))
ex=[(k,v) for k,v in PACo.items() if v.get('fec')][:1]+[(k,v) for k,v in PACo.items() if v.get('asrc')=='own'][:1]+[(k,v) for k,v in PACo.items() if v.get('asrc')=='given'][:1]
for k,v in ex: print(k,json.dumps({a:b for a,b in v.items() if a!='g'}),v['g'][:2])
k=next(iter(DONo)); print(k,json.dumps(DONo[k])[:300])
print('pac address source',collections.Counter(v.get('asrc','none') for v in PACo.values()))
