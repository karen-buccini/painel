import json,sys
p=sys.argv[1]; d=json.load(open(p))
n=next(s for s in d if s.get('type')=='news')
ev=next(i for i in n['items'] if i.get('tag')=='evento')
ev['linhas']=[l for l in ev['linhas'] if l['quando']!='18/11']
if not any(l['quando']=='03/12' for l in ev['linhas']):
    ev['linhas'].append({'quando':'03/12','oque':'Jantar Cobranded - Cordier em Curitiba'})
open(p,'w').write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
