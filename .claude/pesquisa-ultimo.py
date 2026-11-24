import sys,json
dj=sys.argv[1]
d=json.load(open(dj,encoding='utf-8'))
idx=[i for i,x in enumerate(d) if x.get('qr')=='qr/pesquisa-clima.png']
assert len(idx)==1, idx
d.append(d.pop(idx[0]))
open(dj,'w',encoding='utf-8').write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print('ok', len(d)-1)
