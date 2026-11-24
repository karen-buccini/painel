import sys,re
p=sys.argv[1]; s=open(p,encoding='utf-8').read()
def rep(a,b):
    global s
    assert s.count(a)==1, a[:60]
    s=s.replace(a,b)
# CSS: as duas faixas lado a lado
rep(""".selic-strip .info{color:var(--muted);font-size:clamp(18px,20.5px,26px);}
""",""".selic-strip .info{color:var(--muted);font-size:clamp(18px,20.5px,26px);}
/* Selic e juros futuro (DI) lado a lado, cada um na sua faixa. */
.taxas-row{display:grid;grid-template-columns:1fr 1fr;gap:clamp(14px,20px,26px);margin-top:clamp(14px,25.6px,26px);}
.taxas-row .selic-strip{margin-top:0;row-gap:clamp(8px,10px,14px);}
.taxas-row .selic-strip .pair{flex-basis:100%;}
.selic-strip .info.up{color:var(--mint);}
.selic-strip .info.down{color:var(--coral);}
""")
# Render
rep("""      ${(()=>{
        const selic = selicAtual(s);
        if(!selic) return '';
        const pct = selic.valor.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2});
        return `
          <div class="selic-strip">
            <div class="pair"><span class="flag">🇧🇷</span>Taxa Selic</div>
            <div class="val">${pct}%</div>
            <div class="info">ao ano${selic.desde ? ` · desde ${selic.desde.slice(0,5)}` : ''}</div>
          </div>`;
      })()}""","""      ${(()=>{
        const num = v => v.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2});
        const selic = selicAtual(s);
        const faixas = [];
        if(selic) faixas.push(`
          <div class="selic-strip">
            <div class="pair"><span class="flag">🇧🇷</span>Taxa Selic</div>
            <div class="val">${num(selic.valor)}%</div>
            <div class="info">ao ano${selic.desde ? ` · desde ${selic.desde.slice(0,5)}` : ''}</div>
          </div>`);
        if(jurosFuturo){
          const d = jurosFuturo.delta;
          const varTxt = d == null ? 'ao ano'
            : Math.abs(d) < 0.005 ? '= estável hoje'
            : `${d>0?'▲':'▼'} ${num(Math.abs(d))} p.p. hoje`;
          faixas.push(`
          <div class="selic-strip">
            <div class="pair"><span class="flag">📈</span>Juros futuro · DI ${jurosFuturo.venc}</div>
            <div class="val">${num(jurosFuturo.valor)}%</div>
            <div class="info ${d == null || Math.abs(d) < 0.005 ? '' : d>0 ? 'up' : 'down'}">${varTxt}</div>
          </div>`);
        }
        if(!faixas.length) return '';
        return faixas.length > 1 ? `<div class="taxas-row">${faixas.join('')}</div>` : faixas[0];
      })()}""")
# Fetch
rep("""// ---------- CLIMA AO VIVO (API pública, sem chave — Open-Meteo) ----------""","""// ---------- JUROS FUTURO AO VIVO (API pública da B3, sem chave) ----------
// Contrato de DI de 1 dia (DI1) que vence no janeiro seguinte a 12 meses de
// hoje: a referência de "juros de 1 ano" do mercado (em nov/26, o jan/28).
// A taxa é a do último negócio do pregão; sem negócio no dia (fim de semana,
// antes da abertura), vale o ajuste do dia anterior. A variação é em pontos
// percentuais contra esse ajuste. Se a B3 não responder, a faixa some.
let jurosFuturo = null;
async function refreshJurosFuturo(){
  try{
    const res = await fetch('https://cotacao.b3.com.br/mds/api/v1/DerivativeQuotation/DI1');
    if(!res.ok) throw new Error('HTTP ' + res.status);
    const dados = await res.json();
    const limite = new Date(Date.now() + 365*24*60*60*1000).toISOString().slice(0,10);
    const c = (dados.Scty || [])
      .filter(x => /^DI1F\\d\\d$/.test(x.symb) && x.asset && x.asset.AsstSummry && x.asset.AsstSummry.mtrtyCode > limite)
      .sort((a,b) => a.asset.AsstSummry.mtrtyCode.localeCompare(b.asset.AsstSummry.mtrtyCode))[0];
    if(!c) throw new Error('contrato não encontrado');
    const q = c.SctyQtn || {};
    const ajuste = q.prvsDayAdjstmntPric;
    const valor = q.curPrc != null ? q.curPrc : ajuste;
    if(valor == null) throw new Error('sem taxa');
    const ano = c.asset.AsstSummry.mtrtyCode.slice(2,4);
    jurosFuturo = { valor, venc: `jan/${ano}`, delta: q.curPrc != null && ajuste != null ? q.curPrc - ajuste : null };
  }catch(err){
    console.warn('Falha ao buscar o juros futuro (B3):', err);
  }
  if(slides[current] && slides[current].type==='currency') renderCurrent();
}

// ---------- CLIMA AO VIVO (API pública, sem chave — Open-Meteo) ----------""")
rep("""  refreshSelic();
  refreshWeather();
})();""","""  refreshSelic();
  refreshJurosFuturo();
  refreshWeather();
})();""")
rep("""setInterval(refreshSelic, 60*60*1000);    // Selic a cada hora""","""setInterval(refreshSelic, 60*60*1000);    // Selic a cada hora
setInterval(refreshJurosFuturo, 5*60*1000); // juros futuro a cada 5 minutos""")
s,n=re.subn(r"(const VERSAO_PAINEL = /\* versao-do-painel \*/ ')[^']*(')", r"\g<1>2026-11-24-02\2", s); assert n==1
open(p,'w',encoding='utf-8').write(s)
print('ok')
