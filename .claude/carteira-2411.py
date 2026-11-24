import json,sys
p=sys.argv[1]; d=json.load(open(p))
w=next(s for s in d if s.get('type')=='wallet')
ser=[x for x in w['series'] if x['t'] not in ('23/10','24/10')]
tem={x['t'] for x in ser}
for t in ('23/11','24/11'):
    if t not in tem: ser.append({'t':t,'v':249730000})
w['series']=ser; w['current']=249730000; w['pctChange']=0.15
w['source']='Fonte: CR2 · série diária de 25/10 a 24/11'
open(p,'w').write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
