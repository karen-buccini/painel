#!/usr/bin/env python3
"""Gera a versão para a empresa (painel-okrs-publico.html) a partir do artefato da liderança.

Tira tudo o que é do detalhamento (objeto DET, CSS .det/.clic, clique no KR, aviso de clique)
e os comentários internos do código (nomes de empresas, quem informou, regras de apuração).
Fica igual ao que vai para a TV: só os números. Rodar sempre depois de mudar o artefato:

    python3 .claude/previa/gera-publico.py
"""
import re, sys, pathlib

AQUI = pathlib.Path(__file__).resolve().parent
ORIGEM = AQUI / 'painel-okrs-artefato.html'
DESTINO = AQUI / 'painel-okrs-publico.html'

s = ORIGEM.read_text(encoding='utf-8')

def troca(antes, depois, regex=False, flags=0):
    global s
    n = len(re.findall(antes, s, flags)) if regex else s.count(antes)
    if n != 1:
        sys.exit(f'ERRO: esperava 1 ocorrência, achei {n}: {antes[:70]!r}')
    s = re.sub(antes, depois, s, flags=flags) if regex else s.replace(antes, depois)

# 1. Título próprio (para não confundir com o da liderança na galeria).
troca(r'<title>[^<]*</title>', '<title>OKRs Q4 Vixtra</title>', regex=True)

# 2. CSS do detalhamento (do marcador até a última regra .det).
troca(r'/\* ===== Drill-down \(só no artefato\) ===== \*/\n.*?\.det ul\{[^\n]*\n', '', regex=True, flags=re.S)

# 3. Aviso sem a parte do clique.
troca('Clique num KR para ver o que compõe o número · pontos ou ← → trocam de slide', 'Pontos ou ← → trocam de slide')

# 4. Objeto DET inteiro (comentário + linha).
troca(r'// Drill-down \(só no artefato[^\n]*\nconst DET = \{.*?\};\n', '', regex=True, flags=re.S)

# 5. KR não é mais clicável.
troca("const clic = id && DET[id] ? ` clic\" data-kr=\"${id}` : '';", "const clic = '';")

# 6. Seta do teclado não depende mais do painel de detalhe.
troca(" && !document.getElementById('det')", '')

# 7. JS do detalhamento (abreDet, fechaDet, clique, Esc).
troca(r'// ---- Drill-down: clique no KR.*?addEventListener\(\'keydown\', e=>\{ if\(e\.key===\'Escape\'\) fechaDet\(\); \}\);\n', '', regex=True, flags=re.S)

# 8. Comentários internos do script: linhas só de comentário e comentários no fim da linha
#    dentro de OBJETIVOS (lá ficam nomes de empresas e quem informou o número).
ini = s.index('<script>'); fim = s.index('</script>', ini)
js = s[ini:fim]
js = re.sub(r'(?m)^[ \t]*//[^\n]*\n', '', js)
a = js.index('const OBJETIVOS'); b = js.index('\n];', a)
bloco = re.sub(r"(?m)(,|\{|\[)[ \t]*//[^\n]*$", r'\1', js[a:b])
js = js[:a] + bloco + js[b:]
s = s[:ini] + js + s[fim:]

# 8b. Comentários do CSS (/* ... */) também saem.
ini = s.index('<style>'); fim = s.index('</style>', ini)
s = s[:ini] + re.sub(r'/\*.*?\*/\n?', '', s[ini:fim], flags=re.S) + s[fim:]

# 9. Conferência: nada do detalhamento pode sobrar.
for proibido in ('DET', 'abreDet', 'fechaDet', 'det-fundo', 'clic"', 'detalhe ›', 'Drill-down'):
    if proibido in s:
        sys.exit(f'ERRO: sobrou {proibido!r} na versão da empresa')

DESTINO.write_text(s, encoding='utf-8')
print(f'ok: {DESTINO.name} ({len(s):,} bytes)')
