import sys,json
fh, dj = sys.argv[1], sys.argv[2]
s=open(fh,encoding='utf-8').read()
def rep(a,b):
    global s
    assert s.count(a)==1, a[:70]
    s=s.replace(a,b)
rep("""const DATE_RETARGETING = 'hs_v2_date_entered_983301662';
""","""const DATE_RETARGETING = 'hs_v2_date_entered_983301662';

// Cards do pipeline Retarget que contam num mês diferente do mês em que
// entraram em "Oportunidade Qualificada" (ID do negócio -> 'AAAA-MM').
// Fora do mês indicado, não entram na coluna Retargeting do Desempenho.
// Censi e SB Trade entraram em 03/11/2026, mas a Karen considera as duas só
// em outubro (24/11/2026).
const RETARGET_MES_CONTADO = {
  '66486445883': '2026-10', // CENSI INDUSTRIA DE PRODUTOS HIDROSSANITARIOS SA
  '67307204901': '2026-10', // SB TRADE COMERCIO EXTERIOR LTDA
};
""")
rep("""  // Os valores do campo BDR são os mesmos IDs de usuário do HubSpot.
  const nomes = await owners();
  const porPessoa = {};
  for (const d of negocios) {
    const bdr = d.properties.nome_bdr__hunter__farmer_;""","""  // Os valores do campo BDR são os mesmos IDs de usuário do HubSpot.
  const nomes = await owners();
  const porPessoa = {};
  const mesAtual = `${p.ano}-${String(p.mes).padStart(2, '0')}`;
  for (const d of negocios) {
    const mesContado = RETARGET_MES_CONTADO[String(d.id)];
    if (mesContado && mesContado !== mesAtual) continue;
    const bdr = d.properties.nome_bdr__hunter__farmer_;""")
open(fh,'w',encoding='utf-8').write(s)
# data.json: Juliane 8 -> 6 já agora, igual ao que o cron vai gravar
d=json.load(open(dj,encoding='utf-8'))
slides = d['slides'] if isinstance(d,dict) and 'slides' in d else d
n=0
for sl in slides:
    for g in sl.get('divisions',[]) or []:
        if g.get('name')=='Retargeting':
            for v in g['sellers']:
                if v.get('name')=='Juliane Gadi':
                    assert v['oportunidades']==8, v['oportunidades']; v['oportunidades']=6; n+=1
            g['sellers'].sort(key=lambda v:-v.get('oportunidades',0))
assert n>=1, n
open(dj,'w',encoding='utf-8').write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print('ok', n)
