import json,sys
p=sys.argv[1]; d=json.load(open(p))
w=next(s for s in d if s.get('type')=='wallet')
ser=[x for x in w['series'] if x['t']!='22/10']
if ser[-1]['t']!='22/11': ser.append({'t':'22/11','v':248640000})
w['series']=ser; w['current']=248640000; w['pctChange']=-0.28
w['source']='Fonte: CR2 · série diária de 23/10 a 22/11'
open(p,'w').write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
