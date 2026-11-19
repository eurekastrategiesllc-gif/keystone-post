import json, os, glob, trend as T
# 2026-11-19: lists every candidate (trend.py marks them _cand), keeps existing labels attached to their URLs
# when the index is renumbered, and marks items not seen in the previous index as NEW.
old={r['i']:r['u'] for r in json.load(open('voice_index.json'))} if os.path.exists('voice_index.json') else {}
labs=json.load(open('tone_labels.json')) if os.path.exists('tone_labels.json') else {}
bylab={old[int(i)]:v for i,v in labs.items() if int(i) in old}
oldurls=set(old.values())
seen={}
for c in T.COUNTIES:
    for tp,tone,rec in T.pool.get(c,[]):
        if rec.get('_cand') or rec.get('v'): seen.setdefault(rec['u'],[rec,set(),tp])[1].add(c)
for u in bylab: seen.setdefault(u,[{'t':'(no longer in feeds)','u':u},set(),[]])
desc={}
for host,items in T.N.RAWITEMS.items():
    for t,u,pd,d in items: desc[u]=d
for f in glob.glob(T.RAW+'/feeds/ksop_*.json'):
    for k,items in json.load(open(f,encoding='utf-8')).items():
        for i in items: desc[T.N.clean(i[1])]=T.N.clean(i[3])
rows=[]; newlabs={}
for i,(u,(rec,cs,tp)) in enumerate(sorted(seen.items())):
    rows.append({'i':i,'u':u})
    if u in bylab: newlabs[str(i)]=bylab[u]
    flag='LAB' if u in bylab else ('old' if u in oldurls else 'NEW')
    print(i,'|',flag,'|',','.join(sorted(cs)),'|','OP' if rec.get('op') else 'news','|',rec.get('d',''),'|',rec['t'][:110],'||',desc.get(u,'')[:300],'||',u)
json.dump(rows,open('voice_index.json','w'))
json.dump(newlabs,open('tone_labels.json','w'))
print('rows',len(rows),'labels kept',len(newlabs),'of',len(labs))
