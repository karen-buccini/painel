/**
 * merge-and-save.js
 * ------------------------------------------------------------------
 * Lê o data.json atual, aplica por cima os dados coletados pelos outros
 * scripts (HubSpot, carteira) e grava de volta.
 *
 * Só os campos automatizados são tocados. Tudo que continua manual —
 * aniversariantes, aniversários de casa, novo talento, novidades da
 * empresa, celebração de ativação, cotação de moedas — fica intacto.
 *
 * Uso:
 *   node scripts/fetch-hubspot.js > /tmp/hubspot.json
 *   node scripts/fetch-cr2.js > /tmp/cr2.json
 *   node scripts/merge-and-save.js /tmp/hubspot.json /tmp/cr2.json data.json
 *
 * Qualquer um dos dois primeiros argumentos pode ser "" (string vazia)
 * para atualizar só uma parte dos dados. O trânsito da CET-SP saiu do
 * painel em 23/10, junto com o slide de clima e trânsito.
 * ------------------------------------------------------------------
 */

const fs = require('fs');

const [, , hubspotPath, cr2Path, dataJsonPath = 'data.json'] = process.argv;

function readJSON(path, fallback = null) {
  try {
    return JSON.parse(fs.readFileSync(path, 'utf-8'));
  } catch (e) {
    return fallback;
  }
}

const findSlide = (slides, type) => slides.find((s) => s.type === type);

/** Todos os slides de ranking, na ordem em que aparecem. */
const rankings = (slides) => slides.filter((s) => s.type === 'ranking');

/** Acha o slide de ranking que contém uma divisão com este nome. */
function findDivision(slides, nomeDivisao) {
  const alvo = nomeDivisao.toLowerCase();
  for (const s of rankings(slides)) {
    const d = (s.divisions || []).find((x) => String(x.name).toLowerCase() === alvo);
    if (d) return d;
  }
  return null;
}

const PALETA = ['var(--gold)', 'var(--mint)', 'var(--sky)', 'var(--coral)', '#9B8CFF'];

/**
 * Varre o data.json inteiro e monta um cadastro nome → { photo, color }.
 *
 * É assim que as fotos do Slack sobrevivem às atualizações automáticas: o
 * HubSpot devolve só nome e número, e aqui a gente reencontra a foto de quem
 * já apareceu no painel alguma vez. Quem for novo entra sem foto (o painel
 * mostra as iniciais) até alguém colar a URL da foto no data.json uma vez.
 */
function montarElenco(slides) {
  const elenco = {};

  // Base: o cadastro de fotos em fotos.json. Antes o elenco saia so do proprio
  // data.json, e ai bastava a rotina reescrever um ranking num momento em que
  // aquela pessoa nao estivesse em nenhuma outra lista para a foto dela sumir
  // de vez - foi o que aconteceu com os tres closers. Com o cadastro por fora,
  // a foto sobrevive a qualquer reescrita.
  try {
    const cadastro = JSON.parse(fs.readFileSync("fotos.json", "utf-8"));
    for (const [nome, foto] of Object.entries(cadastro)) {
      elenco[nome.toLowerCase().trim()] = { photo: foto };
    }
  } catch (e) {
    console.error("Aviso: nao consegui ler fotos.json. As fotos vao sair so do data.json.");
  }
  const registrar = (p) => {
    if (!p || !p.name) return;
    const chave = String(p.name).toLowerCase().trim();
    if (!elenco[chave]) elenco[chave] = {};
    if (p.photo && !elenco[chave].photo) elenco[chave].photo = p.photo;
    if (p.color && !elenco[chave].color) elenco[chave].color = p.color;
  };

  for (const s of slides) {
    (s.people || []).forEach(registrar);
    for (const d of s.divisions || []) {
      for (const v of d.sellers || []) {
        registrar(v);
        (v.people || []).forEach(registrar);
      }
    }
  }
  return elenco;
}

/** Aplica foto e cor de quem já é conhecido; o resto ganha cor da paleta. */
function vestir(pessoas, elenco) {
  return pessoas.map((p, i) => {
    const conhecido = elenco[String(p.name).toLowerCase().trim()] || {};
    const out = { ...p };
    out.color = conhecido.color || PALETA[i % PALETA.length];
    if (conhecido.photo) out.photo = conhecido.photo;
    return out;
  });
}

/**
 * Troca a lista de uma divisão — mas nunca a esvazia.
 *
 * Em 25/09 uma execução voltou do HubSpot com as duas divisões de farmer
 * vazias e o painel apagou as duas colunas na TV, sem nenhum aviso. Lista
 * vazia quase sempre é soluço de consulta, não a verdade do mês; e mesmo
 * quando for verdade, é melhor mostrar o número de ontem do que um branco.
 * Quando isso acontecer, o log da rotina registra.
 */
function aplicarLista(divisao, novos, rotulo, vestirFn) {
  if (!divisao) return false;
  if (!Array.isArray(novos) || novos.length === 0) {
    if ((divisao.sellers || []).length > 0) {
      console.error(`Aviso: o HubSpot não devolveu ninguém para "${rotulo}". Mantido o que já estava no painel.`);
    }
    return false;
  }
  divisao.sellers = vestirFn(novos);
  return true;
}

/** Troca só o número de uma divisão de uma pessoa só, preservando nome e foto. */
function atualizarContagem(divisao, valor) {
  if (!divisao || valor == null) return;
  for (const v of divisao.sellers || []) v.oportunidades = valor;
}

const milhoes = (v) =>
  `R$ ${(v / 1e6).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}M`;

/**
 * Tira do arquivo os slides temporarios que ja sairam da tela.
 *
 * O painel ja esconde comemoracao, novo talento e evento depois da data, mas
 * eles continuavam guardados no data.json para sempre — em tres semanas viraram
 * dez slides mortos, e e justamente este arquivo que alguem abre no GitHub para
 * editar na mao. A poda espera 24h depois do vencimento, e slide sem data de
 * saida nunca e removido.
 */
const TIPOS_TEMPORARIOS = new Set(['celebration', 'newhire', 'evento', 'campanha']);

function venceEm(s) {
  if (s.visivelAte) return new Date(s.visivelAte + 'T23:59:59-03:00').getTime();
  if (s.type === 'celebration' && s.postedAt) {
    return new Date(s.postedAt).getTime() + (s.diasVisivel || 1) * 864e5;
  }
  if (s.type === 'newhire' && s.joinedAt) {
    return new Date(s.joinedAt).getTime() + (s.diasVisivel || 30) * 864e5;
  }
  return null;  // sem data de saida: fica
}

function podarVencidos(slides) {
  const agora = Date.now();
  const fica = [];
  const removidos = [];
  for (const s of slides) {
    const fim = TIPOS_TEMPORARIOS.has(s.type) ? venceEm(s) : null;
    if (fim !== null && agora - fim > 864e5) {
      removidos.push(s.name || s.client || s.eyebrow || s.type);
    } else {
      fica.push(s);
    }
  }
  return { fica, removidos };
}

function main() {
  const slides = readJSON(dataJsonPath, []);
  if (!Array.isArray(slides) || slides.length === 0) {
    console.error(
      `Erro: ${dataJsonPath} não encontrado ou vazio. O merge parte sempre de um data.json existente, para não perder os slides manuais.`
    );
    process.exit(1);
  }

  const hubspot = hubspotPath ? readJSON(hubspotPath) : null;
  const cr2 = cr2Path ? readJSON(cr2Path) : null;

  const elenco = montarElenco(slides);
  const mudancas = [];

  if (hubspot) {
    // --- Progresso da meta -------------------------------------------
    // A meta so e reescrita quando a consulta traz ativacao. Zero vindo do
    // HubSpot quase sempre e soluco de consulta, e zerar a meta na TV no meio
    // do mes e o pior erro que este painel pode cometer: some o valor ativado,
    // some a lista de clientes e a barra de progresso volta ao inicio. Se for
    // zero de verdade (dia 1o do mes, por exemplo), o proprio mes vira e a
    // primeira ativacao corrige. Quando isso acontecer, fica registrado no log.
    const goal = findSlide(slides, 'goal');
    if (goal && hubspot.ativados) {
      const veioVazio = !hubspot.ativados.clientesAtivados;
      const tinhaDado = goal.clientesAtivados > 0 || goal.atual > 0;
      if (veioVazio && tinhaDado) {
        console.error('Aviso: o HubSpot não devolveu nenhuma ativação do mês. Meta mantida como estava.');
      } else {
        goal.atual = hubspot.ativados.volumeAtivado;
        goal.clientesAtivados = hubspot.ativados.clientesAtivados;
        goal.clientesLista = hubspot.ativados.clientesLista;
        mudancas.push('meta do mês');
      }
    }

    // --- Forecasting closing -----------------------------------------
    const funnel = findSlide(slides, 'funnel');
    if (funnel && hubspot.pipeline) {
      funnel.quenteTotal = hubspot.pipeline.quenteTotal;
      funnel.mornoTotal = hubspot.pipeline.mornoTotal;
      funnel.top3 = hubspot.pipeline.top3;
      mudancas.push('forecasting closing');
    }

    // --- Forecasting por farmer --------------------------------------
    // Vem chaveado pelo nome da operação no HubSpot ("Aumento de volume
    // tomado", "Renovação", "Reativação"), que é o mesmo nome da coluna no
    // painel. Operação que não tenha coluna correspondente simplesmente não
    // aparece — se um dia surgir Reativação, é criar a coluna no data.json.
    if (hubspot.forecastingFarmer) {
      const aplicadas = [];
      for (const [operacao, pessoas] of Object.entries(hubspot.forecastingFarmer)) {
        const div = findDivision(slides, operacao);
        if (!div) continue;
        if (aplicarLista(div, pessoas.slice(0, 3), operacao, (l) => vestir(l, elenco))) {
          aplicadas.push(operacao);
        }
      }
      if (aplicadas.length) mudancas.push('forecasting por farmer (' + aplicadas.join(', ') + ')');
    }

    // --- Desempenho: closing -----------------------------------------
    const closing = findDivision(slides, 'Closing');
    if (closing && hubspot.ativados && hubspot.ativados.closers) {
      // Ate cinco: cortar em tres escondia quem ativou no mes, que e
      // exatamente o contrario do que este card existe para fazer.
      if (aplicarLista(closing, hubspot.ativados.closers.slice(0, 5), 'Closing',
            (l) => vestir(l, elenco))) {
        mudancas.push('ranking de closing');
      }
    }

    // --- Desempenho: parcerias ---------------------------------------
    // Até quatro pessoas: a coluna hoje mostra quatro, e cortar em três
    // deixaria alguém de fora sem ninguém perceber.
    if (hubspot.parcerias && hubspot.parcerias.farming) {
      const farming = findDivision(slides, 'Parcerias · Farming');
      if (farming) {
        if (aplicarLista(farming, hubspot.parcerias.farming.slice(0, 4), 'Parcerias · Farming',
              (l) => vestir(l, elenco).map((v) => ({ ...v, metricLabel: 'oportunidades' })))) {
          mudancas.push('ranking de parcerias');
        }
      }
    }

    // --- Desempenho: retargeting, frete e câmbio ----------------------
    // Aqui o HubSpot devolve só a contagem do mês; os nomes e as fotos de
    // quem responde por cada frente continuam vindo do data.json.
    // Retargeting vem como lista de donos: quem aparece na TV e quem tem
    // oportunidade no mes. Sem oportunidade nenhuma, a coluna fica vazia e o
    // painel escreve "Em apuracao" — melhor do que um nome fixo com zero.
    const retg = findDivision(slides, 'Retargeting');
    if (retg && Array.isArray(hubspot.retargeting)) {
      if (hubspot.retargeting.length) {
        retg.sellers = vestir(hubspot.retargeting.slice(0, 4), elenco)
          .map((v) => ({ ...v, metricLabel: 'oportunidades' }));
      } else {
        retg.sellers = [];
      }
    }
    // Frete continua por contagem: a coluna mostra uma pessoa so, fixa.
    atualizarContagem(findDivision(slides, 'Frete'), hubspot.frete);
    // Câmbio não entra aqui: a divisão mostra quatro métricas próprias
    // (volume, margem, clientes, transações) e não uma contagem de negócios.
    mudancas.push('retargeting, frete e câmbio');

    // --- Novidades: o card de crédito aprovado ------------------------
    const news = findSlide(slides, 'news');
    const cardCredito = news && (news.items || []).find((i) => i.tag === 'credito');
    if (cardCredito && hubspot.ativados && hubspot.ativados.creditoAprovado) {
      cardCredito.title = `Crédito aprovado chega a ${milhoes(hubspot.ativados.creditoAprovado)} no mês`;
      mudancas.push('card de crédito aprovado');
    }
  }

  if (cr2) {
    const wallet = findSlide(slides, 'wallet');
    if (wallet) {
      wallet.current = cr2.current;
      wallet.pctChange = cr2.pctChange;
      wallet.series = cr2.series;
      mudancas.push('carteira');
    }
  }

  const poda = podarVencidos(slides);
  if (poda.removidos.length) {
    mudancas.push('poda de ' + poda.removidos.length + ' slide(s) vencido(s)');
    console.error('Removidos do arquivo (já tinham saído da tela): ' + poda.removidos.join(', '));
  }

  fs.writeFileSync(dataJsonPath, JSON.stringify(poda.fica, null, 2) + '\n');
  console.log(`OK: ${dataJsonPath} atualizado (${mudancas.join(', ') || 'nada a aplicar'}).`);
}

main();
