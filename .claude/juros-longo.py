import sys,re
p=sys.argv[1]; s=open(p,encoding='utf-8').read()
def rep(a,b):
    global s
    assert s.count(a)==1, a[:70]
    s=s.replace(a,b)
rep("""// Contrato de DI de 1 dia (DI1) que vence no janeiro seguinte a 12 meses de
// hoje: a referência de "juros de 1 ano" do mercado (em nov/26, o jan/28).
// A taxa é a do último negócio do pregão; sem negócio no dia (fim de semana,
// antes da abertura), vale o ajuste do dia anterior. A variação é em pontos
// percentuais contra esse ajuste. Se a B3 não responder, a faixa some.""","""// Contrato de DI de 1 dia (DI1) de vencimento mais longo que teve negócio no
// pregão (em 24/11/26, o jan/38). Os vencimentos mais distantes passam dias sem
// negócio, por isso a escolha é entre os que negociaram hoje. Sem negócio
// nenhum (fim de semana, antes da abertura), vale o mais longo com ajuste do
// dia anterior, sem variação. A variação é em pontos percentuais contra o
// ajuste do dia anterior. Se a B3 não responder, a faixa some.""")
rep("""    const limite = new Date(Date.now() + 365*24*60*60*1000).toISOString().slice(0,10);
    const c = (dados.Scty || [])
      .filter(x => /^DI1F\\d\\d$/.test(x.symb) && x.asset && x.asset.AsstSummry && x.asset.AsstSummry.mtrtyCode > limite)
      .sort((a,b) => a.asset.AsstSummry.mtrtyCode.localeCompare(b.asset.AsstSummry.mtrtyCode))[0];
    if(!c) throw new Error('contrato não encontrado');""","""    const contratos = (dados.Scty || [])
      .filter(x => /^DI1[FGHJKMNQUVXZ]\\d\\d$/.test(x.symb) && x.asset && x.asset.AsstSummry && x.SctyQtn)
      .sort((a,b) => b.asset.AsstSummry.mtrtyCode.localeCompare(a.asset.AsstSummry.mtrtyCode));
    const c = contratos.find(x => x.SctyQtn.curPrc != null)
           || contratos.find(x => x.SctyQtn.prvsDayAdjstmntPric != null);
    if(!c) throw new Error('contrato não encontrado');""")
rep("""    const ano = c.asset.AsstSummry.mtrtyCode.slice(2,4);
    jurosFuturo = { valor, venc: `jan/${ano}`,""","""    const [ano, mes] = c.asset.AsstSummry.mtrtyCode.split('-');
    const meses = ['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez'];
    jurosFuturo = { valor, venc: `${meses[Number(mes)-1]}/${ano.slice(2)}`,""")
s,n=re.subn(r"(const VERSAO_PAINEL = /\* versao-do-painel \*/ ')[^']*(')", r"\g<1>2026-11-24-03\2", s); assert n==1
open(p,'w',encoding='utf-8').write(s); print('ok')
