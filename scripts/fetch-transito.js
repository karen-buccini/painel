/**
 * fetch-transito.js
 * ------------------------------------------------------------------
 * Extrai os dados de "Trânsito Agora" do site da CET-SP (cetsp.com.br).
 * Não existe API pública — isso faz parsing do HTML da página inicial.
 *
 * Como o HTML da CET pode mudar sem aviso, este script foi escrito para
 * ser tolerante a pequenas variações, mas vale revisar se ele parar de
 * funcionar (o seletor principal são os títulos de região: Norte, Sul,
 * Leste, Oeste, Centro, cada um seguido de "X km" e "(Y%)").
 *
 * Uso:
 *   node scripts/fetch-transito.js > transito-data.json
 * ------------------------------------------------------------------
 */

/**
 * Rodízio por regra: segunda 1 e 2, terça 3 e 4, quarta 5 e 6, quinta 7 e 8,
 * sexta 9 e 0, nada no fim de semana. (Feriado suspende, e a conta não sabe.)
 *
 * O painel novo calcula isto sozinho na hora de desenhar. Isto aqui existe só
 * para as telas que ainda estão com uma versão antiga do index.html em cache,
 * que lê o valor pronto do data.json.
 */
function rodizioDeHoje() {
  const hoje = new Date(new Date().toLocaleString('en-US', { timeZone: 'America/Sao_Paulo' }));
  const finais = { 1: '1 e 2', 2: '3 e 4', 3: '5 e 6', 4: '7 e 8', 5: '9 e 0' };
  const f = finais[hoje.getDay()];
  return f ? `Placas final ${f}` : 'Sem rodízio no fim de semana';
}

/**
 * Busca a página da CET, repetindo com espera crescente quando ela não
 * responde.
 *
 * Em 23/10 a rotina das 18h ficou 41 segundos esperando o site, desistiu e
 * ficou vermelha — e na execução seguinte o site respondia em um segundo e
 * meio. Soluço de site, não mudança de layout. Agora cada tentativa tem 20
 * segundos de limite, e a falha só vale depois de quatro. Erro 4xx (fora o
 * 429) não é soluço e não é repetido.
 */
async function buscarPaginaCet() {
  const TENTATIVAS = 4;
  for (let tentativa = 1; tentativa <= TENTATIVAS; tentativa++) {
    let motivo;
    try {
      const res = await fetch('https://www.cetsp.com.br/', { signal: AbortSignal.timeout(20000) });
      if (res.ok) return await res.text();
      if (res.status !== 429 && res.status < 500) {
        throw Object.assign(new Error(`CET-SP retornou HTTP ${res.status}`), { definitivo: true });
      }
      motivo = `HTTP ${res.status}`;
    } catch (e) {
      if (e.definitivo) throw e;
      motivo = e.name === 'TimeoutError' ? 'sem resposta em 20s' : e.message;
    }

    if (tentativa === TENTATIVAS) {
      throw new Error(`CET-SP não respondeu em ${TENTATIVAS} tentativas (última: ${motivo})`);
    }
    const espera = 2000 * 2 ** (tentativa - 1);
    console.error(`CET-SP ${motivo}; repetindo em ${espera}ms (tentativa ${tentativa} de ${TENTATIVAS})`);
    await new Promise((r) => setTimeout(r, espera));
  }
}

async function fetchTransito() {
  const html = await buscarPaginaCet();

  // O rodízio não é raspado daqui: é regra fixa por dia da semana, e o painel
  // calcula sozinho. Raspar servia só para herdar o cache da CET.

  // A data que a CET escreve na página ("São Paulo, 24 de setembro de 2026")
  // é montada no navegador, então um fetch simples continua vendo a do dia
  // anterior enquanto os quilômetros já vêm atualizados — foi assim que a TV
  // passou um dia inteiro carimbando 23/09 em dados de hoje. O que o painel
  // mostra agora é a hora em que esta rotina leu a página, que é exatamente a
  // idade do número na tela.
  const dataAtualizacao = new Date().toLocaleString('pt-BR', {
    timeZone: 'America/Sao_Paulo', day: '2-digit', month: '2-digit',
    hour: '2-digit', minute: '2-digit',
  }).replace(',', ' ·');

  // Cada região: nome, seguido em algum ponto próximo por "NN km" e "(NN%)"
  const regioes = ['Norte', 'Oeste', 'Centro', 'Leste', 'Sul'];
  const traffic = [];

  for (const nome of regioes) {
    // Procura o bloco de HTML entre o nome da região e a próxima ocorrência
    // de "km" seguida de "%", tolerando tags HTML no meio.
    const regex = new RegExp(
      `${nome}[\\s\\S]{0,200}?(\\d+)\\s*km[\\s\\S]{0,100}?\\((\\d+)%\\)`,
      'i'
    );
    const m = html.match(regex);
    if (m) {
      const km = Number(m[1]);
      const pct = Number(m[2]);
      const level = pct < 15 ? 'ok' : pct < 25 ? 'mid' : 'bad';
      traffic.push({ name: nome, km, pct, level });
    }
  }

  // Ordena da maior para a menor lentidão, como no painel
  traffic.sort((a, b) => b.pct - a.pct);

  return {
    // Só para telas com o index.html antigo em cache; o painel novo calcula.
    rodizio: rodizioDeHoje(),
    // Só a data. Os parenteses e a fonte quem escreve e o painel, senao sai
    // 'Lentidao por regiao (23 de setembro de 2026 (fonte: CET-SP))'.
    trafficUpdatedAt: dataAtualizacao,
    traffic,
  };
}

fetchTransito()
  .then((data) => console.log(JSON.stringify(data, null, 2)))
  .catch((e) => {
    console.error('Erro ao buscar dados de trânsito da CET-SP:', e);
    process.exit(1);
  });
