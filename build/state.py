import csv, collections, json, sys, os
from common import *
csv.field_size_limit(10**9)
sldl,sldu,zipc=geo()
P=os.path.join(RAW,'pa_dos_2026')
rows=list(csv.DictReader(open(P+'/filer_2026.txt',encoding='latin-1')))
print('cycle7 submit months',collections.Counter(r['SubmittedDate'][:7] for r in rows if r['CYCLE']=='7'))
print('cycle6',collections.Counter(r['SubmittedDate'][:7] for r in rows if r['CYCLE']=='6'),'cycle8',collections.Counter(r['SubmittedDate'][:7] for r in rows if r['CYCLE']=='8').most_common(3),'cycle9',collections.Counter(r['SubmittedDate'][:7] for r in rows if r['CYCLE']=='9').most_common(3))
CYC={'1','2','3','4','5','6'}
keep={}
for r in rows:
    if r['CYCLE'] not in CYC: continue
    k=(r['FILERID'],r['CYCLE'])
    if k not in keep or int(r['CampaignfinanceID'])>int(keep[k]['CampaignfinanceID']): keep[k]=r
kept={r['CampaignfinanceID']:r for r in keep.values()}
print('reports kept',len(kept),'of',sum(1 for r in rows if r['CYCLE'] in CYC))
F={}
for r in sorted(keep.values(),key=lambda r:int(r['CYCLE'])):
    f=F.setdefault(r['FILERID'],{'raised':0.0,'spent':0.0,'pac':0.0,'other':0.0,'county':None})
    f.update(name=nice(r['FILERNAME']),type=r['FILERTYPE'],office=r['OFFICE'].strip() or f.get('office',''),district=r['DISTRICT'].strip(),party=party(r['PARTY']) if r['PARTY'].strip() else f.get('party','O'),last=r['CampaignfinanceID'],begin=float(r['BEGINNING'] or 0),lastmon=float(r['MONETARY'] or 0),lastcycle=r['CYCLE'],lastdate=r['SubmittedDate'])
    f['raised']+=float(r['MONETARY'] or 0); f['unitem']=f.get('unitem',0)+float(r['MONETARY'] or 0)
    c=r['COUNTY'].strip()
    if c.isdigit() and 1<=int(c)<=67: f['county']=int(c)
    elif not f['county'] and r['STATE'].strip().upper()=='PA': f['county']=zipc.get(r['ZIPCODE'].strip()[:5])
lastexp=collections.Counter(); lastrec=collections.Counter()
exp=collections.defaultdict(list)
for r in csv.DictReader(open(P+'/expense_2026.txt',encoding='latin-1')):
    if r['CampaignFinanceID'] not in kept: continue
    a=float(r['EXPAMT'] or 0); fid=r['FILERID']
    if fid not in F: continue
    F[fid]['spent']+=a
    if F[fid]['last']==r['CampaignFinanceID']: lastexp[fid]+=a
    if a>0: exp[fid].append((a,nice(r['EXPNAME']),nice(r['EXPDESC'])[:60],dt(r['EXPDATE'])))
for r in csv.DictReader(open(P+'/receipt_2026.txt',encoding='latin-1')):
    if r['CampaignFinanceID'] in kept and r['FILERID'] in F:
        a=float(r['RECAMT'] or 0); F[r['FILERID']]['other']+=a
        if F[r['FILERID']]['last']==r['CampaignFinanceID']: lastrec[r['FILERID']]+=a
pac=collections.defaultdict(list); don=[]; lastcon=collections.Counter()
n=0
for r in csv.DictReader(open(P+'/contrib_2026.txt',encoding='latin-1')):
    if r['CampaignFinanceID'] not in kept: continue
    fid=r['FilerID']
    if fid not in F: continue
    a=sum(float(r[k] or 0) for k in('CONTAMT1','CONTAMT2','CONTAMT3'))
    sec=r['Section']; n+=1
    if sec in('IA','IB','IC','ID'):
        F[fid]['raised']+=a
        if F[fid]['last']==r['CampaignFinanceID']: lastcon[fid]+=a
    if sec in('IA','IC'): F[fid]['pac']+=a
    if a<=0: continue
    if sec in('IA','IC'):
        pac[fid].append((a,nice(r['CONTRIBUTOR']),dt(r['CONTDATE1'])))
    elif sec in('IB','ID') and a>=250:
        dc=zipc.get(r['ZIPCODE'].strip()[:5]) if r['STATE'].strip().upper()=='PA' else None
        don.append((a,nice(r['CONTRIBUTOR']),nice(r['CITY']),r['STATE'].strip().upper(),nice(r['OCCUPATION'])[:40],nice(r['ENAME'])[:40],dt(r['CONTDATE1']),fid,dc))
print('contrib rows used',n,'donor items',len(don))
for fid,f in F.items():
    f['cash']=round(f['begin']+f['lastmon']+lastcon[fid]+lastrec[fid]-lastexp[fid],2)
    f['exp']=sorted(exp[fid],reverse=True)[:60]; f['pacs']=sorted(pac[fid],reverse=True)[:60]
json.dump({'F':F,'don':don},open(os.path.join(os.path.dirname(__file__),'state.json'),'w'))
act=[f for f in F.values() if f['raised']>0 or f['spent']>0]
print('filers',len(F),'active',len(act),'no county',sum(1 for f in act if not f['county']))
print('offices',collections.Counter(f['office'] for f in act))
for f in sorted(act,key=lambda f:-f['raised'])[:12]: print(f['name'],f['office'],f['district'],f['party'],f['county'],round(f['raised']),round(f['spent']),round(f['cash']),round(f['pac']),f['lastcycle'])
