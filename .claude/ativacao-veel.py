import json,sys,re
p=sys.argv[1]; d=json.load(open(p))
FOTO_FER='https://avatars.slack-edge.com/2026-08-28/11929341580899_ad448f83f67214a68488_512.jpg'
FOTO_CAIO='https://avatars.slack-edge.com/2024-03-15/6807855125090_ada0fc6e0c989953f4a2_512.jpg'
VOL=3273273
# Mesmo nome que a rotina do HubSpot (nomeDeCliente) vai gerar para a meta.
nome='Veel Trade (grupo Cecil) - Sociedade Catarinense de Comércio, Imp. e Exp.'
# 1) Destaque "Novo cliente ativado": 7 dias a partir de 24/11.
if not any(s.get('type')=='celebration' and 'Veel' in s.get('client','') for s in d):
    d.insert(0,{'type':'celebration','duration':16000,'eyebrow':'Novo cliente ativado',
        'client':'Veel Trade (Grupo Cecil)',
        'pessoas':[{'name':'Fernando Velloso','photo':FOTO_FER},{'name':'Caio Gelfi','photo':FOTO_CAIO}],
        'valorAtivado':VOL,'limiteAprovado':5000000,'visivelAte':'2026-12-01'})
# 2) Meta do mês (a rotina do HubSpot reescreve igual na próxima execução).
g=next(s for s in d if s.get('type')=='goal')
if g.get('clientesAtivados',0)==0:
    g['atual']=VOL; g['clientesAtivados']=1; g['clientesLista']=[nome]; g['periodo']='2026-11'
# 3) Ranking do Closing (slide aparece quando há ativação no mês).
for s in d:
    for dv in s.get('divisions',[]) or []:
        if dv.get('name')=='Closing' and not dv.get('sellers'):
            dv['sellers']=[{'name':'Fernando Velloso','value':VOL,'deals':1,'color':'#9B8CFF','photo':FOTO_FER}]
open(p,'w').write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
