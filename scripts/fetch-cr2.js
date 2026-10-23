/**
 * fetch-cr2.js
 * ------------------------------------------------------------------
 * ⚠️ AUTOMAÇÃO DE LOGIN — LEIA COM ATENÇÃO ANTES DE USAR EM PRODUÇÃO
 *
 * Este script automatiza o login no CR2 via Microsoft SSO para extrair
 * a série de "Evolução da carteira" do dashboard. Diferente do HubSpot
 * (que tem API oficial com token seguro), isso simula um navegador de
 * verdade fazendo login — é inerentemente mais frágil e mais sensível.
 *
 * Só use isso se:
 *
 *   1) A conta usada for uma conta de serviço dedicada (não a conta
 *      pessoal de ninguém do time), com o mínimo de permissão necessária
 *      só pra visualizar o dashboard — nunca a conta de um humano.
 *   2) Essa conta NÃO tiver autenticação em dois fatores (MFA) ativa.
 *      Um fluxo 100% automático não consegue responder a um código
 *      enviado por SMS/app autenticador. Se a política de segurança da
 *      empresa exigir MFA em todas as contas, este script vai falhar de
 *      forma consistente (o que é o comportamento correto — ver ponto 3).
 *   3) As credenciais (CR2_EMAIL / CR2_PASSWORD) forem guardadas como
 *      *secrets* do GitHub, nunca escritas no código.
 *
 * Comportamento em caso de falha: o script SEMPRE encerra com erro e
 * NUNCA escreve dados parciais/inventados no data.json. Se o login for
 * bloqueado (MFA, CAPTCHA, mudança na tela de login da Microsoft), é
 * melhor a automação falhar visivelmente (workflow fica vermelho no
 * GitHub Actions) do que a TV mostrar um número errado sem ninguém notar.
 *
 * Instalação: npm i -D playwright && npx playwright install chromium
 * Variáveis de ambiente necessárias: CR2_EMAIL, CR2_PASSWORD
 * ------------------------------------------------------------------
 */

const { chromium } = require('playwright');

const EMAIL = process.env.CR2_EMAIL;
const PASSWORD = process.env.CR2_PASSWORD;

if (!EMAIL || !PASSWORD) {
  console.error('Erro: defina as variáveis de ambiente CR2_EMAIL e CR2_PASSWORD.');
  process.exit(1);
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  try {
    // 1. Tela de login do CR2
    await page.goto('https://cr2.vixtra.com/pt/login', { waitUntil: 'networkidle' });

    // 2. Botão "Entrar com Microsoft"
    await page.click('text=Entrar com Microsoft');

    // 3. Fluxo de login da Microsoft — ponto mais frágil do script,
    // pois a Microsoft pode alterar essa tela sem aviso.
    await page.waitForSelector('input[type="email"]', { timeout: 15000 });
    await page.fill('input[type="email"]', EMAIL);
    await page.click('input[type="submit"], button[type="submit"]');

    await page.waitForSelector('input[type="password"]', { timeout: 15000 });
    await page.fill('input[type="password"]', PASSWORD);
    await page.click('input[type="submit"], button[type="submit"]');

    // 4. Tela opcional "Continuar conectado?"
    try {
      await page.waitForSelector('input[type="submit"]', { timeout: 8000 });
      await page.click('input[type="submit"]');
    } catch (e) {
      // Tela pode não aparecer — tudo bem, segue o fluxo.
    }

    // 5. Se pedir MFA, CAPTCHA, ou qualquer outra verificação, o
    // redirecionamento para /pt/dash não vai acontecer. Detectamos isso
    // e falhamos explicitamente, sem escrever dado nenhum.
    await page.waitForURL('**/pt/dash', { timeout: 20000 }).catch(() => {
      throw new Error(
        'Login não completou a tempo — provável pedido de MFA, CAPTCHA ou ' +
        'mudança no fluxo de login da Microsoft. Abortando sem escrever dados.'
      );
    });

    // 6. Esperar o gráfico da carteira renderizar
    await page.waitForTimeout(4000);

    // 7. Extrair a série de dados: mesma técnica usada manualmente nesta
    // automação — procurar no SVG do gráfico a prop `data` injetada pelo
    // React (padrão observado no componente de gráfico do CR2).
    const series = await page.evaluate(() => {
      const svgs = Array.from(document.querySelectorAll('svg'));
      for (const svg of svgs) {
        const key = Object.keys(svg).find((k) => k.startsWith('__reactFiber$'));
        if (!key) continue;
        let node = svg[key];
        for (let i = 0; i < 25 && node; i++) {
          const props = node.memoizedProps;
          if (
            props &&
            Array.isArray(props.data) &&
            props.data.length >= 25 &&
            props.data[0] &&
            props.data[0].raw
          ) {
            return props.data;
          }
          node = node.return;
        }
      }
      return null;
    });

    if (!series) {
      throw new Error(
        'Não encontrei a série de dados da carteira na página — o layout do CR2 pode ter mudado. Abortando sem escrever dados.'
      );
    }

    const cleanSeries = series.map((p) => ({ t: p.t, v: p.v }));
    const current = cleanSeries[cleanSeries.length - 1].v;
    const first = cleanSeries[0].v;
    const pctChange = Number((((current - first) / first) * 100).toFixed(2));

    console.log(JSON.stringify({ current, pctChange, series: cleanSeries }, null, 2));
  } finally {
    await browser.close();
  }
}

main().catch((e) => {
  console.error('Erro ao extrair dados do CR2:', e.message);
  process.exit(1);
});
