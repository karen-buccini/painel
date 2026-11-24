import json,sys
p=sys.argv[1]; d=json.load(open(p))
w=next(s for s in d if s.get('type')=='wallet')
ser=[x for x in w['series'] if x['t'] not in ('19/10','20/10','21/10')]
for x in ser:
    if x['t']=='18/11': x['v']=251730000
ser+= [{'t':'19/11','v':248640000},{'t':'20/11','v':248640000},{'t':'21/11','v':248640000}]
w['series']=ser; w['current']=248640000; w['pctChange']=-2.03
w['source']='Fonte: CR2 · série diária de 22/10 a 21/11'
open(p,'w').write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
