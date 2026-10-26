# Painel TV Vixtra

Acompanhamento da operação comercial da Vixtra, exibido na TV do escritório.

O repositório tem duas coisas: o **painel web**, que roda sozinho numa aba do
navegador e se atualiza sozinho, e a **apresentação em PowerPoint**, para
quando alguém precisar apresentar na mão.

## 1. Painel web

Endereço público: **https://stellaserpejante.github.io/painel-tv-vixtra/**

Basta abrir esse link na TV e deixar em tela cheia. Os slides passam em loop.

- `index.html` — o painel inteiro (visual, animações e lógica de rodízio).
- `data.json` — todos os números e nomes que aparecem na tela.

O `index.html` lê o `data.json` ao carregar. Para mudar qualquer conteúdo,
mexe-se no `data.json`, nunca no HTML.

### O que se atualiza sozinho

De 2 em 2 horas, rotinas do GitHub Actions buscam os dados e reescrevem o
`data.json`:

| Slide | Fonte |
| --- | --- |
| Progresso da meta (valor ativado, clientes ativados) | HubSpot |
| Forecasting closing (quente, morno, top 3) | HubSpot |
| Forecasting por farmer (aumento e renovação) | HubSpot |
| Desempenho — Closing, Parcerias Hunting e Farming | HubSpot |
| Desempenho — Retargeting, Frete e Câmbio | HubSpot |
| Card de crédito aprovado, em Novidades | HubSpot |
| Temperatura de São Paulo, ao lado do relógio | Open-Meteo (direto da TV, a cada 15 min) |

### O que continua manual

Os slides temporários — nova ativação, novo talento, evento — somem da
tela sozinhos na data combinada e, um dia depois, saem também do arquivo,
para o `data.json` não ir crescendo com conteúdo morto.

Aniversariantes do mês, aniversários de casa, novo talento no time, as
novidades da empresa, a celebração de nova ativação, a cotação de moedas e o
gráfico da carteira. Tudo isso se edita direto no `data.json`, pelo próprio
GitHub: abra o arquivo, clique no lápis, altere e confirme em **Commit
changes**. Em um ou dois minutos o painel na TV já mostra o novo conteúdo.

### Fotos das pessoas

As fotos são URLs do Slack gravadas no `data.json`. Quem já apareceu no painel
alguma vez continua com a foto mesmo quando o ranking muda — as rotinas
reaproveitam a foto pelo nome. Quem entra pela primeira vez aparece com as
iniciais até alguém colar a URL da foto no `data.json` uma vez.

### Ligar a atualização automática

As rotinas precisam de um token do HubSpot guardado como segredo do
repositório (nunca dentro do código):

1. **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret**
3. Name: `HUBSPOT_TOKEN` · Secret: o token do app privado do HubSpot
4. **Add secret**

Depois, em **Actions** → *Atualizar dados do HubSpot* → **Run workflow**, para
conferir que roda. A partir daí é automático.

O app privado do HubSpot precisa dos escopos `crm.objects.deals.read` e
`crm.objects.owners.read`.

### As rotinas

- `.github/workflows/update-hubspot.yml` — de 2 em 2 horas.
- `.github/workflows/update-cr2.yml` — **desligada**. O gráfico da carteira vem
  do CR2, que exige login; enquanto não existirem os segredos `CR2_EMAIL` e
  `CR2_PASSWORD`, ela só roda se alguém clicar em *Run workflow*.

### Os scripts

- `scripts/fetch-hubspot.js` — consulta o HubSpot e imprime um JSON.
- `scripts/fetch-cr2.js` — busca a evolução da carteira no CR2.
- `scripts/merge-and-save.js` — aplica esses JSONs por cima do `data.json`,
  preservando tudo que é manual.

Os IDs de pipeline, etapa e propriedade do HubSpot estão no topo do
`fetch-hubspot.js`, com o número do relatório de onde cada um saiu. Se algum
pipeline for recriado lá dentro, é esse bloco que precisa ser atualizado.

## 2. Apresentação em PowerPoint

`apresentacao/TV-Comercial-Vixtra.pptx`

13 slides com o mesmo conteúdo do painel. Cada slide traz na área de notas a
fonte exata do dado, com o número do relatório do HubSpot de onde ele veio. Os
slides de nova ativação e de novo integrante têm animação automática — basta
apresentar (F5) que tudo roda sozinho, sem clique.

Para publicar uma versão nova pelo navegador: abra a pasta `apresentacao`,
clique em **Add file** → **Upload files**, arraste o arquivo e confirme em
**Commit changes**. Mantendo o mesmo nome, o GitHub substitui e guarda a versão
anterior no histórico.

## Créditos

Os desenhos da pasta `emojis/` são do [Twemoji](https://github.com/jdecked/twemoji),
© Twitter, Inc. e outros colaboradores, sob a licença
[CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/).
