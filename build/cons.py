# Consultant scoreboard: who the campaigns paid, and how those clients did.
import csv, json, re, collections, os, sys
from common import *
import cons_match as M
csv.field_size_limit(10**9)
S=M.S; Fd=M.Fd; C=M.C; link=M.link
P=os.path.join(RAW,re.search(r"P=os\.path\.join\(RAW,'([^']+)'\)",open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'state.py')).read()).group(1))   # same export folder state.py reads
MINCLIENT=1000
# ---- which side a committee is on ----
PARTY_D=re.compile(r'DEMOCRATIC (CAMPAIGN )?COMMITTEE|DEMOCRATIC PARTY|DEMOCRATIC STATE|HOUSE DEMOCRATIC|SENATE DEMOCRATIC|\bDEM(OCRATIC)? COM\b|DEMOCRATS\b')
PARTY_R=re.compile(r'REPUBLICAN (CAMPAIGN )?COMMITTEE|REPUBLICAN PARTY|REPUBLICAN STATE|HOUSE REPUBLICAN|SENATE REPUBLICAN|\bREP(UBLICAN)? COM\b|REPUBLICANS\b|\bGOP\b')
def side(k):
    """returns (party, kind) kind: cand = on the 2026 ballot, off = candidate or official not on it, party = party or caucus committee"""
    if k in link:
        p=C[link[k]]['party']; return (p,'cand') if p in('R','D') else (None,None)
    if k[0]=='F':
        p=Fd[k[1:]]['party']; return (p,'off') if p in('R','D') else (None,None)
    f=S[k[1:]]; U=f['name'].upper()
    if f['type']=='3' or PARTY_D.search(U) or PARTY_R.search(U):
        if PARTY_D.search(U) and not PARTY_R.search(U): return 'D','party'
        if PARTY_R.search(U) and not PARTY_D.search(U): return 'R','party'
        return (f['party'],'party') if f['party'] in('R','D') else (None,None)
    if f['office'] in('GOV','LTG','STS','STH') and f['type'] in('1','2') and f['party'] in('R','D') and not re.search(r'\bPAC\b|COPE|UNION|LOCAL',U): return f['party'],'off'
    return None,None
# ---- payee names ----
CORP=r'\b(LLC|L L C|INC|INCORPORATED|LLP|CORP|CORPORATION|CO|COMPANY|LTD|LP|PC|PLLC|LLLC)\b'
def vkey(n):
    n=re.sub(r"[^A-Z0-9 ]",'',html.unescape(html.unescape(n or '')).upper().replace('&',' AND ').replace('-',' ').replace('/',' '))
    n=re.sub(CORP,'',n); n=re.sub(r'^THE ','',n.strip())
    return re.sub(r'\s+',' ',n).strip()
FIRMS=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'cons_firms.json')))
SHOW={}; AL={}
for k,v in FIRMS['alias'].items(): AL[vkey(k).replace(' ','')]=vkey(v).replace(' ',''); SHOW[vkey(v).replace(' ','')]=v
DROPF={vkey(x).replace(' ','') for x in FIRMS['drop']}
# payees that are not consultants: transfers, platforms, ad sellers, payroll, everyday vendors
NOTFIRM=re.compile(r'\b(CLUB|RESORT|INN|LODGE|CATERERS?|SHERATON|RITZ|AIRBNB|PHILLIES|PIRATES|EAGLES|STEELERS|META|AUTOBODY|ESCROW|SIGNS?|BROADCASTING|TAX SERVICE|PA DEMS|SENATOR|REPRESENTATIVE|VOLUNTEERS FOR|EVENT CENTER|BALLROOM|WINERY|VINEYARDS?|FARMS?|CARD|CARDMEMBER|OUTDOOR|LAMAR|BILLBOARDS?|AVIATION|CHARTER|TRANSPORTATION|LIMOUSINE|USPS|US POSTAL|POSTAL SERVICE|POSTMASTER|POST OFFICE|FACEBOOK|META PLATFORMS|GOOGLE|ACTBLUE|WINRED|ANEDOT|NGP VAN|PAYCHEX|ADP|GUSTO|QUICKBOOKS|INTUIT|BANK|CREDIT UNION|AMERICAN EXPRESS|AMEX|VISA|MASTERCARD|CAPITAL ONE|AMAZON|COMCAST|EFFECTV|SPECTRUM|VERIZON|ATT|T MOBILE|STRIPE|PAYPAL|SQUARE|TWITTER|MAILCHIMP|VISTAPRINT|STAPLES|WALMART|COSTCO|SAMS CLUB|HOTEL|MARRIOTT|HILTON|RESTAURANT|CATERING|GOLF|COUNTRY CLUB|AIRLINES|UBER|LYFT|IHEART|IHEARTMEDIA|AUDACY|NEXSTAR|SINCLAIR|HEARST|TEGNA|CUMULUS|NEWSPAPER|GAZETTE|DEPARTMENT OF|TREASURY|IRS|INTERNAL REVENUE|REVENUE|COMMONWEALTH OF|INSURANCE|HIGHMARK|BLUE CROSS|AETNA|UNEMPLOYMENT|EXPENDITURES|TRANSACTIONS|DISBURSEMENTS|UNITEMIZED|AGGREGATE|ZOOM|MICROSOFT|APPLE|ADOBE|GODADDY|SQUARESPACE|WIX|CANVA|FEDEX|UPS|ENTERPRISE|HERTZ|AVIS|SUNOCO|SHEETZ|WAWA|TURNPIKE|EZPASS|E ZPASS|ELECTIONS?|VOTER SERVICES|RENT|REALTY|PROPERTIES|LANDLORD|UNIVERSITY|COLLEGE|CHURCH|FIRE (CO|COMPANY|DEPARTMENT)|VFW|LEGION|TAVERN|PUB|BREWING|BREWERY|PIZZA|DINER|GRILLE?|CAFE|BAKERY|WINERY|STEAKHOUSE)\b|^W[A-Z]{3}( TV| FM| AM| RADIO)?$|^K[A-Z]{3} TV$|\bTV$|\bRADIO$')
NOTDESC=re.compile(r'contribut|donation|transfer|loan|refund|reimburs|non.?pa\b|non.?penn|federal|fec report|payroll|salary|wages|\btax|insurance|rent\b|in.?kind to|sponsor|dues|ticket|assessment|filing fee|gift|flowers|bank|interest|processing fee|credit card|merchant|void',re.I)
CATS=[('Media buying',r'media buy|media placement|placement|ad buy|tv buy|buy\b|air ?time|cable|broadcast'),
      ('Media and ads',r'\btv\b|televis|radio|advertis|\bads?\b|commercial|video|production|creative|media'),
      ('Digital',r'digital|online|facebook|meta ads|google|text|sms|p2p|email|e-mail|web|social'),
      ('Mail and print',r'mail|postage|print|literature|\blit\b|palm ?card|signs?\b|brochure|flyer|postcard|door hanger|banner'),
      ('Polling and research',r'poll|survey|research|data|voter file|analytics|target'),
      ('Fundraising',r'fundrais|finance|donor|call time'),
      ('Field',r'field|canvass|petition|gotv|door|phone ?bank|organiz|turnout|robo|calls?\b'),
      ('Compliance and legal',r'compliance|account|legal|treasur|bookkeep|attorney|\blaw\b|audit'),
      ('Consulting',r'consult|strateg|manage|campaign services|professional|advis|communications|public relations|\bpr\b')]
CATS=[(n,re.compile(r,re.I)) for n,r in CATS]
def cat(d):
    for n,r in CATS:
        if r.search(d): return n
    return 'Other'
filerkeys={vkey(f['name']) for f in S.values()}
COMMITTEEISH=re.compile(r'\b(PAC|COMMITTEE|FRIENDS OF|FRIENDS|CITIZENS FOR|FOR SENATE|FOR PA|FOR CONGRESS|FOR STATE|FOR GOVERNOR|FOR PENNSYLVANIA|PARTY|HDCC|HRCC|SRCC|SDCC|CAMPAIGN COMMITTEE|VICTORY FUND|DEMOCRATS|REPUBLICANS|FUND)\b')
PERSONWORD=re.compile(r'\b(STRATEG|MEDIA|CONSULT|GROUP|PARTNERS|ASSOCIATES|COMMUNICATIONS|SOLUTIONS|PRINT|MAIL|DIGITAL|RESEARCH|POLLING|ADVIS|PUBLIC|AFFAIRS|SERVICES|CREATIVE|DESIGN|MARKETING|ANALYTICS|DATA|STUDIO|PRODUCTIONS?|AGENCY|ENTERPRISES|ADVERTISING|GRAPHICS|PRESS|DIRECT|CAMPAIGNS?|POLITIC|TARGET|FIRM|LAW|TECHNOLOG|LABS?|WORKS|INTERACTIVE|OUTREACH|FIELD|VENTURES|HOLDINGS|MANAGEMENT|INTERNATIONAL|NATIONAL|AMERICA|PENNSYLVANIA|PA|KEYSTONE|STRATEGIES)')
# payments to individual people (staff, solo operators) are left out: this is a board of firms
_fn=collections.Counter()
for d in json.load(open('state.json'))['don']:
    t=re.sub(r'[^A-Z ]','',d[1].upper()).split()
    if 2<=len(t)<=3: _fn[t[0]]+=1
FIRST={n for n,c in _fn.items() if c>=25 and len(n)>2}
BIZ=re.compile(r'\b(STRATEG\w*|MEDIA|CONSULT\w*|GROUP|PARTNERS|ASSOCIATES|COMMUNICATIONS?|SOLUTIONS|PRINT\w*|MAIL\w*|DIGITAL|RESEARCH|POLLING|ADVIS\w*|PUBLIC|AFFAIRS|SERVICES|CREATIVE|DESIGNS?|MARKETING|ANALYTICS|DATA|STUDIOS?|PRODUCTIONS?|AGENCY|ENTERPRISES|ADVERTISING|GRAPHICS|PRESS|DIRECT|CAMPAIGNS?|POLITIC\w*|TARGET\w*|FIRM|LAW|TECHNOLOG\w*|LABS?|WORKS|INTERACTIVE|OUTREACH|FIELD|VENTURES|HOLDINGS|MANAGEMENT|COMPLIANCE|PROMOTIONS|AND|FUNDRAISING|SYSTEMS|BUYING|IMPACT|VICTORY)\b')
KEEPP={vkey(x).replace(' ','') for x in FIRMS.get('keep_person',[])}
def person(payee):
    raw=html.unescape(html.unescape(payee or '')).strip(); U=raw.upper()
    if re.search(CORP,U.replace('.','')) or BIZ.search(U) or any(ch.isdigit() for ch in U): return False
    if re.match(r'(MR|MRS|MS|DR|MISS)\b\.?\s',U): return True
    t=re.sub(r'[^A-Z, ]','',U).split()
    if not 2<=len(t)<=4: return False
    if ',' in U: return True
    return t[0] in FIRST
# ---- read spending ----
pay=collections.defaultdict(lambda:collections.defaultdict(lambda:collections.Counter()))  # firm -> camp -> category -> $
names=collections.defaultdict(collections.Counter)
def add(k,payee,desc,a):
    vk=vkey(payee)
    if not vk or a<=0: return
    if NOTDESC.search(desc or '') or vk in filerkeys or COMMITTEEISH.search(vk) or NOTFIRM.search(vk): return
    fk=vk.replace(' ',''); fk=AL.get(fk,fk)   # spellings that differ only by spaces are one firm
    if fk in DROPF or (fk not in KEEPP and fk not in SHOW and person(payee)): return
    pay[fk][k][cat(desc or '')]+=a; names[fk][re.sub(r',?\s*\b(LLC|L\.L\.C\.|Inc\.?|LLP|Corp\.?|Ltd\.?|LLLC)\s*$','',nice(html.unescape(html.unescape(payee)).strip()),flags=re.I).strip(' ,.')]+=a
rows=list(csv.DictReader(open(P+'/filer_2026.txt',encoding='latin-1')))
keep={}
for r in rows:
    if r['CYCLE'] not in {'1','2','3','4','5','6'}: continue
    k=(r['FILERID'],r['CYCLE'])
    if k not in keep or int(r['CampaignfinanceID'])>int(keep[k]['CampaignfinanceID']): keep[k]=r
kept={r['CampaignfinanceID'] for r in keep.values()}
SIDE={}
for fid in S: SIDE['S'+fid]=side('S'+fid)
for cid in Fd: SIDE['F'+cid]=side('F'+cid)
for r in csv.DictReader(open(P+'/expense_2026.txt',encoding='latin-1')):
    k='S'+r['FILERID']
    if r['CampaignFinanceID'] in kept and SIDE.get(k,(None,))[0]: add(k,r['EXPNAME'],r['EXPDESC'],float(r['EXPAMT'] or 0))
cm2c={}
for l in open(RAW+'/ccl26/ccl.txt'):
    p=l.rstrip('\n').split('|')
    if p[0] in Fd and p[5] in('P','A') and p[2]=='2026': cm2c[p[3]]=p[0]
seen=set()
for l in open(RAW+'/oppexp26/oppexp.txt',encoding='latin-1'):
    p=l.split('|')
    if p[0] in cm2c and p[18]!='X' and p[21] not in seen:
        seen.add(p[21]); k='F'+cm2c[p[0]]
        if SIDE.get(k,(None,))[0]: add(k,p[8],p[15]+' '+p[17],float(p[13] or 0))
if __name__=='__main__' and len(sys.argv)>1 and sys.argv[1]=='firms':
    for sd in('R','D'):
        tot={v:sum(sum(c.values()) for k,c in d.items() if SIDE[k][0]==sd) for v,d in pay.items()}
        print('=====',sd,len([v for v,t in tot.items() if t>0]))
        for v,t in sorted(tot.items(),key=lambda x:-x[1])[:int(sys.argv[2])]:
            cc=collections.Counter()
            for k,c in pay[v].items():
                if SIDE[k][0]==sd: cc.update(c)
            n=sum(1 for k in pay[v] if SIDE[k][0]==sd)
            print(round(t),'|',v,'|',n,'|',' '.join('%s %d%%'%(a[:9],100*b/t) for a,b in cc.most_common(3)),'|',SHOW.get(v) or names[v].most_common(1)[0][0])
# ---- score ----
CLOSE=10.0   # a race decided by under 10 points
OFFL={'GOV':'Governor','LTG':'Lt. Governor','USC':'U.S. House, PA-%d','STS':'State Senate, District %d','STH':'State House, District %d'}
LVL={'GOV':'statewide','LTG':'statewide','USC':'congress','STS':'legislature','STH':'legislature'}   # same level names the page's Races filter uses
_sldl,_sldu,_z=geo(); _cd=json.load(open('fed.json'))['cd']
def where(c):
    """county numbers (1 to 67, alphabetical) the candidate's district touches; empty for statewide races"""
    d=c['district']
    return sorted(set(_cd.get(str(d),[]))) if c['office']=='USC' else _sldu.get(d,[]) if c['office']=='STS' else _sldl.get(d,[]) if c['office']=='STH' else []
def seat(c): return OFFL[c['office']]%c['district'] if '%' in OFFL[c['office']] else OFFL[c['office']]
def decided(c):
    """margin, in points, of the contest that settled this candidate's year"""
    return c.get('pmargin') if c['out']=='LP' else c['margin']
try: SITECAMPS=set(json.load(open('../site/data.json'))['camps'])
except Exception: SITECAMPS=set()
def build(sd):
    out=[]
    for fk,d in pay.items():
        ks=[k for k in d if SIDE[k][0]==sd]
        if not ks: continue
        mix=collections.Counter(); tot=0
        cl={}   # candidate or committee -> row
        for k in ks:
            a=sum(d[k].values()); tot+=a; mix.update(d[k])
            kind=SIDE[k][1]
            if kind=='cand':
                ck=link[k]; r=cl.setdefault(('c',)+ck,{'a':0,'k':None,'c':C[ck]})
            else:
                nm=(S[k[1:]]['name'] if k[0]=='S' else Fd[k[1:]]['name']); r=cl.setdefault((kind,k),{'a':0,'k':None,'c':None,'n':nm,'kind':kind,'lv':'congress' if k[0]=='F' else 'statewide' if S[k[1:]]['office'] in('GOV','LTG') else 'legislature'})
            r['a']+=a
            if k in SITECAMPS and (r['k'] is None or a>r.get('ka',0)): r['k']=k; r['ka']=a
        if tot<10000 or mix['Other']>0.5*tot: continue
        if max((c for c in mix if c!='Other'),key=lambda c:mix[c])=='Compliance and legal': continue   # lawyers and bookkeepers are not scored
        w=l=cw=clo=0; wd=ld=0; rows=[]
        for key,r in cl.items():
            c=r['c']; a=round(r['a'])
            if c and c['out'] and r['a']>=MINCLIENT:
                m=decided(c); close=bool(c['out']=='LP' or (c['opp'] and m is not None and m<CLOSE)) if c['out']!='LP' else bool(m is not None and m<CLOSE)
                if c['out']=='W': w+=1; wd+=r['a']; cw+=close
                else: l+=1; ld+=r['a']; clo+=close
                rows.append([nice(c['name']),seat(c),a,c['out'],m,int(close),r['k'],int(not c['opp']) if c['out']=='W' else 0,LVL[c['office']],where(c)])
            elif c:
                rows.append([nice(c['name']),seat(c),a,'',None,0,r['k'],0,LVL[c['office']],where(c)])   # under the client floor, or no November result
            else:
                rows.append([r['n'],'Party or caucus committee' if r['kind']=='party' else 'Not on the 2026 ballot',a,'',None,0,r['k'],0,'county' if r['kind']=='party' else r['lv']])
        rows.sort(key=lambda x:-x[2])
        typ=max((c for c in mix if c!='Other'),key=lambda c:mix[c])
        out.append({'n':SHOW.get(fk) or names[fk].most_common(1)[0][0],'t':typ,'tot':round(tot),'w':w,'l':l,'cw':cw,'cl':clo,'wd':round(wd),'ld':round(ld),'nc':len(rows),'mix':[[c,round(v)] for c,v in mix.most_common(4) if v>=0.05*tot],'c':rows,'more':0})
    out.sort(key=lambda f:-f['tot'])
    return out
_m=json.load(open('../data.json'))['meta']; _a=collections.Counter(c['asof'] for c in Fd.values() if c['asof']).most_common(1)[0][0]
res={'meta':{'results_pulled':M.RESULTS_DATE,'results_note':'Primary results are final. November results are the county returns as posted on the Department of State site on '+M.RESULTS_DATE+'; they are unofficial until the state certifies them, and the site is checked again every few hours.','state_through':_m['state_through'],'fed_through':_a[6:]+'-'+_a[:2]+'-'+_a[3:5],'min_client':MINCLIENT,'close':CLOSE,'built':__import__('datetime').date.today().isoformat(),'cands':len(C),'linked':len(set(link.values()))},'R':build('R'),'D':build('D')}
if __name__=='__main__' and len(sys.argv)==1:
    for sd in('R','D'):
        F=res[sd]; print(sd,'firms',len(F),'total',sum(f['tot'] for f in F),'with a scored client',sum(1 for f in F if f['w']+f['l']))
        for f in F[:25]: print('  %-34s %-20s %10d  %d-%d  close %d-%d  clients %d'%(f['n'][:34],f['t'],f['tot'],f['w'],f['l'],f['cw'],f['cl'],f['nc']))
    s=json.dumps(res,separators=(',',':'),ensure_ascii=False)
    os.makedirs('../site/cons',exist_ok=True)
    open('../site/cons/board.json','w',encoding='utf-8').write(s); print(len(s),'bytes -> site/cons/board.json')
