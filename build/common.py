import re, html, json, os
RAW=os.path.join(os.path.dirname(__file__),'..','raw')
COUNTIES=['Adams','Allegheny','Armstrong','Beaver','Bedford','Berks','Blair','Bradford','Bucks','Butler','Cambria','Cameron','Carbon','Centre','Chester','Clarion','Clearfield','Clinton','Columbia','Crawford','Cumberland','Dauphin','Delaware','Elk','Erie','Fayette','Forest','Franklin','Fulton','Greene','Huntingdon','Indiana','Jefferson','Juniata','Lackawanna','Lancaster','Lawrence','Lebanon','Lehigh','Luzerne','Lycoming','McKean','Mercer','Mifflin','Monroe','Montgomery','Montour','Northampton','Northumberland','Perry','Philadelphia','Pike','Potter','Schuylkill','Snyder','Somerset','Sullivan','Susquehanna','Tioga','Union','Venango','Warren','Washington','Wayne','Westmoreland','Wyoming','York']
assert len(COUNTIES)==67
def geo():
    g={}
    for l in open(os.path.join(RAW,'geo.txt')):
        k,v=l.strip().split(' ',1); g[k]=v
    sldl={int(a.split(':')[0]):[int(x) for x in a.split(':')[1].split('.')] for a in g['SLDL'].split(';')}
    sldu={int(a.split(':')[0]):[int(x) for x in a.split(':')[1].split('.')] for a in g['SLDU'].split(';')}
    z={}
    for part in g['ZIP'].split(','):
        rng,c=part.split(':'); c=int(c)
        if '-' in rng:
            s,n=rng.split('-'); s=int(s); n=int(n)
        else: s=int(rng); n=0
        for i in range(s,s+n+1): z[str(i)]=c
    return sldl,sldu,z
KEEP={'PAC','LLC','LLP','PA','USA','II','III','IV','PSEA','UFCW','IBEW','SEIU','AFSCME','AFL-CIO','LP','PC','GOP','UPMC','PPL','PECO','NRA','ABC','CPA','MD','DO','JR','SR','FOP','HVAC','LIUNA','IUOE','PFT','APSCUF','PSCOA','UAW','UA','TV','US','DC','NE','NW','SE','SW'}
def nice(s):
    s=html.unescape(html.unescape(s or '')).strip(); s=re.sub(r'\s+',' ',s)
    if not s: return s
    if s.upper()==s or s.lower()==s:
        out=[]
        for w in s.split(' '):
            core=re.sub(r'[^A-Za-z-]','',w).upper()
            if core in KEEP: out.append(w.upper())
            else:
                t=w.lower().capitalize()
                t=re.sub(r"(?<=[-'./&(])([a-z])",lambda m:m.group(1).upper(),t)
                t=re.sub(r'^Mc([a-z])',lambda m:'Mc'+m.group(1).upper(),t)
                out.append(t)
        s=' '.join(out)
    return s
def party(p):
    p=(p or '').upper()
    return 'R' if p in('REP','R') else 'D' if p in('DEM','D') else 'O'
def dt(s):
    s=re.sub(r'\D','',s or '')
    return f'{s[0:4]}-{s[4:6]}-{s[6:8]}' if len(s)==8 and s[:2]=='20' else ''
