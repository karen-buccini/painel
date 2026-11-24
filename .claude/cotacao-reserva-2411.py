import json,sys
p=sys.argv[1]; d=json.load(open(p))
c=next(s for s in d if s.get('type')=='currency')
novos={'USD':(5.87,-1.75),'EUR':(6.43,-1.18),'USDT':(5.83,-3.07)}
for m in c['list']:
    if m['code'] in novos: m['value'],m['pct']=novos[m['code']]
open(p,'w').write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
