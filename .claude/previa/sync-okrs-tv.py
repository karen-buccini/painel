#!/usr/bin/env python3
"""Leva os números dos OKRs do artefato da liderança para o painel da TV (data.json) e faz o push.

Fonte da verdade: bloco `const OBJETIVOS = [...]` de painel-okrs-artefato.html.
Destino: slides type 'okr' do data.json (só o campo `krs`, casando pelo `n` do objetivo).
Não mexe em nenhum outro slide, nem no index.html, nem no detalhamento (DET).

    python3 .claude/previa/sync-okrs-tv.py            # atualiza, commita e faz push
    python3 .claude/previa/sync-okrs-tv.py --seco     # só mostra o que mudaria

Autorizado pela Karen em 18/11/2026: toda atualização do artefato da liderança vai para a TV com push direto.
"""
import json, re, subprocess, sys, pathlib, datetime

AQUI = pathlib.Path(__file__).resolve().parent
REPO = AQUI.parent.parent
ARTEFATO = AQUI / 'painel-okrs-artefato.html'
DATA = REPO / 'data.json'
SECO = '--seco' in sys.argv

def git(*args, check=True):
    r = subprocess.run(['git', '-C', str(REPO), *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        sys.exit(f'ERRO no git {" ".join(args)}:\n{r.stdout}{r.stderr}')
    return r.stdout.strip()

# 1. Repositório limpo e na main (para nunca commitar trabalho de outra pessoa/conversa junto).
if git('rev-parse', '--abbrev-ref', 'HEAD') != 'main':
    sys.exit('ERRO: o repositório do painel não está na branch main. Nada foi feito.')
sujos = git('status', '--porcelain', '--untracked-files=no')
if sujos:
    sys.exit(f'ERRO: há mudanças não commitadas no painel da TV; não vou misturar com elas. Nada foi feito.\n{sujos}')
if not SECO:
    git('pull', '--rebase', '-q', 'origin', 'main')

# 2. Lê OBJETIVOS do artefato (avaliado como JavaScript pelo próprio macOS).
html = ARTEFATO.read_text(encoding='utf-8')
m = re.search(r'const OBJETIVOS = (\[.*?\n\]);', html, re.S)
if not m:
    sys.exit('ERRO: não achei o bloco OBJETIVOS no artefato.')
r = subprocess.run(['osascript', '-l', 'JavaScript', '-e', f'JSON.stringify(eval({json.dumps(m.group(1))}))'],
                   capture_output=True, text=True)
if r.returncode != 0:
    sys.exit(f'ERRO ao ler OBJETIVOS: {r.stderr}')
objetivos = {o['n']: o for o in json.loads(r.stdout)}

# 3. Copia os KRs para os slides 'okr' do data.json.
texto = DATA.read_text(encoding='utf-8')
slides = json.loads(texto)
mudou = []
achados = set()
for s in slides:
    if s.get('type') != 'okr':
        continue
    o = objetivos.get(s.get('n'))
    if not o:
        sys.exit(f"ERRO: slide okr n={s.get('n')} não existe no artefato.")
    achados.add(s['n'])
    for i, (antes, depois) in enumerate(zip(s['krs'], o['krs'])):
        if antes != depois:
            mudou.append(f"KR {int(s['n'])}.{i+1} {depois.get('b','')} {depois.get('t','')}: "
                         f"{antes.get('atual')} → {depois.get('atual')}")
    if len(s['krs']) != len(o['krs']):
        mudou.append(f"objetivo {s['n']}: {len(s['krs'])} → {len(o['krs'])} KRs")
    s['krs'] = o['krs']
if achados != set(objetivos):
    sys.exit(f'ERRO: objetivos do artefato {sorted(objetivos)} ≠ slides okr da TV {sorted(achados)}.')

if not mudou:
    print('TV já está igual ao artefato. Nada a fazer.')
    sys.exit(0)
print('Muda na TV:\n  ' + '\n  '.join(mudou))
if SECO:
    sys.exit(0)

# 4. Grava no mesmo formato do merge-and-save.js, commita só o data.json e faz push.
DATA.write_text(json.dumps(slides, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
hoje = datetime.date.today().strftime('%d/%m')
msg = (f'OKRs: atualiza numeros a partir do artefato ({hoje})\n\n' + '\n'.join(mudou) +
       '\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>')
git('add', 'data.json')
git('commit', '-q', '-m', msg)
for tentativa in (1, 2):
    p = subprocess.run(['git', '-C', str(REPO), 'push', '-q', 'origin', 'main'], capture_output=True, text=True)
    if p.returncode == 0:
        print(f'Push feito: {git("log", "-1", "--format=%h %s")}')
        break
    if tentativa == 1:
        git('pull', '--rebase', '-q', 'origin', 'main')
else:
    sys.exit(f'ERRO no push (commit ficou local):\n{p.stderr}')
