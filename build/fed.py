import csv, collections, json, os
from common import *
cd=collections.defaultdict(list)
for i,l in enumerate(open(RAW+'/tab20_cd11920_county20_st42.txt',encoding='utf-8-sig')):
    p=l.rstrip('\n').split('|')
    if i==0: h=p; continue
    r=dict(zip(h,p))
    if int(r['AREALAND_PART'])>0: cd[int(r['GEOID_CD119_20'][2:])].append((int(r['GEOID_COUNTY_20'][2:])+1)//2)
print({k:[COUNTIES[c-1] for c in v] for k,v in sorted(cd.items())})
W='CAND_ID|CAND_NAME|CAND_ICI|PTY_CD|CAND_PTY_AFFILIATION|TTL_RECEIPTS|TRANS_FROM_AUTH|TTL_DISB|TRANS_TO_AUTH|COH_BOP|COH_COP|CAND_CONTRIB|CAND_LOANS|OTHER_LOANS|CAND_LOAN_REPAY|OTHER_LOAN_REPAY|DEBTS_OWED_BY|TTL_INDIV_CONTRIB|CAND_OFFICE_ST|CAND_OFFICE_DISTRICT|SPEC_ELECTION|PRIM_ELECTION|RUN_ELECTION|GEN_ELECTION|GEN_ELECTION_PRECENT|OTHER_POL_CMTE_CONTRIB|POL_PTY_CONTRIB|CVG_END_DT|INDIV_REFUNDS|CMTE_REFUNDS'.split('|')
C={}
for l in open(RAW+'/weball26/weball26.txt',encoding='latin-1'):
    r=dict(zip(W,l.rstrip('\n').split('|')))
    if r['CAND_OFFICE_ST']!='PA' or r['CAND_ID'][0]!='H': continue
    d=int(r['CAND_OFFICE_DISTRICT'] or 0)
    if not 1<=d<=17 or float(r['TTL_RECEIPTS'] or 0)<5000: continue
    last,_,first=r['CAND_NAME'].partition(',')
    toks=[w for w in first.split() if len(w.strip('.'))>1 and w.upper().strip('.') not in('MR','MRS','MS','DR','HON','REP')]
    suf=[w.strip('.').capitalize()+('.' if w.upper().strip('.') in('JR','SR') else '') if w.upper().strip('.') in('JR','SR') else w.upper() for w in toks if w.upper().strip('.') in('JR','SR','II','III','IV')]
    first=' '.join(w for w in toks if w.upper().strip('.') not in('JR','SR','II','III','IV'))
    C[r['CAND_ID']]=dict(name=(nice((first+' '+last).strip().upper())+(' '+suf[0] if suf else '')),party=party(r['CAND_PTY_AFFILIATION']),district=d,inc=r['CAND_ICI'],raised=float(r['TTL_RECEIPTS']),spent=float(r['TTL_DISB'] or 0),cash=float(r['COH_COP'] or 0),pac=float(r['OTHER_POL_CMTE_CONTRIB'] or 0),asof=r['CVG_END_DT'],pacs=[],exp=[])
print('PA House candidates',len(C))
cm={}
for l in open(RAW+'/cm26/cm.txt',encoding='latin-1'):
    p=l.split('|'); cm[p[0]]=nice(p[1])
cmte={}
for l in open(RAW+'/ccl26/ccl.txt'):
    p=l.rstrip('\n').split('|')
    if p[0] in C and p[5] in('P','A') and p[2]=='2026': cmte[p[3]]=p[0]
print('committees',len(cmte))
for l in open(RAW+'/pas226/itpas2.txt',encoding='latin-1'):
    p=l.split('|')
    if p[16] in C and p[5]=='24K':
        a=float(p[14] or 0)
        if a>0: C[p[16]]['pacs'].append((a,cm.get(p[0],p[0]),dt(p[13][4:8]+p[13][0:4])))
seen=set()
for l in open(RAW+'/oppexp26/oppexp.txt',encoding='latin-1'):
    p=l.split('|')
    if p[0] in cmte and p[18]!='X':
        a=float(p[13] or 0)
        if a>0 and p[21] not in seen:
            seen.add(p[21]); d=p[12]; C[cmte[p[0]]]['exp'].append((a,nice(p[8]),nice(p[15])[:60],dt(d[6:10]+d[0:2]+d[3:5])))
for c in C.values():
    c['pacs']=sorted(c['pacs'],reverse=True)[:60]; c['exp']=sorted(c['exp'],reverse=True)[:60]
json.dump({'C':C,'cd':cd},open('fed.json','w'))
for c in sorted(C.values(),key=lambda c:-c['raised'])[:10]: print(c['name'],c['party'],c['district'],c['inc'],round(c['raised']),round(c['spent']),round(c['cash']),c['asof'],len(c['pacs']),len(c['exp']),c['pacs'][:1],c['exp'][:1])
