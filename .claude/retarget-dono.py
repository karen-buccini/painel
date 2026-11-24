import sys,json
fh, dj = sys.argv[1], sys.argv[2]
s=open(fh,encoding='utf-8').read()
def rep(a,b):
    global s
    assert s.count(a)==1, a[:70]
    s=s.replace(a,b)
rep(""" * Retargeting: cards do pipeline Retarget que entraram na etapa
 * "Oportunidade Qualificada" no mês, contados pelo campo "Nome BDR/ Hunter/
 * Farmer" do card (regra da Karen, 06/11/2026). Antes contava pelo dono do
 * negócio, que nem sempre é o BDR: em novembro o painel mostrava Juliane 2 e
 * Josemir 1, e os três cards eram da Juliane no campo BDR. Card sem BDR
 * preenchido não entra na contagem.""",""" * Retargeting: cards do pipeline Retarget que entraram na etapa
 * "Oportunidade Qualificada" no mês, contados pelo proprietário do negócio
 * (regra da Karen, 24/11/2026: "olhe sempre o proprietário do negócio quando
 * no funil de retarget"). Entre 06/11 e 24/11 contava pelo campo "Nome BDR/
 * Hunter/ Farmer", e card sem BDR preenchido ficava de fora mesmo tendo dono
 * (Mega Pack, 23/11). Card sem proprietário não entra na contagem.""")
rep("""    ['dealname', 'nome_bdr__hunter__farmer_']
  );

  // Os valores do campo BDR são os mesmos IDs de usuário do HubSpot.
  const nomes = await owners();""","""    ['dealname', 'hubspot_owner_id']
  );

  const nomes = await owners();""")
rep("""    const bdr = d.properties.nome_bdr__hunter__farmer_;
    if (!bdr) continue;
    porPessoa[bdr] = (porPessoa[bdr] || 0) + 1;""","""    const dono = d.properties.hubspot_owner_id;
    if (!dono) continue;
    porPessoa[dono] = (porPessoa[dono] || 0) + 1;""")
open(fh,'w',encoding='utf-8').write(s)
d=json.load(open(dj,encoding='utf-8'))
slides = d['slides'] if isinstance(d,dict) and 'slides' in d else d
n=0
for sl in slides:
    for g in sl.get('divisions',[]) or []:
        if g.get('name')=='Retargeting':
            for v in g['sellers']:
                if v.get('name')=='Juliane Gadi':
                    assert v['oportunidades']==6, v['oportunidades']; v['oportunidades']=7; n+=1
assert n>=1
open(dj,'w',encoding='utf-8').write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print('ok',n)
