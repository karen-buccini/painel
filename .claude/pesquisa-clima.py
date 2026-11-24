import sys,json,re
ih, dj = sys.argv[1], sys.argv[2]
s=open(ih,encoding='utf-8').read()
def rep(a,b):
    global s
    assert s.count(a)==1, a[:70]
    s=s.replace(a,b)
rep(""".campanha.halloween{--tema:#FF8A2A;}
""",""".campanha.halloween{--tema:#FF8A2A;}
.campanha.azul{--tema:var(--sky);}
/* QR Code da campanha: quadro branco para o celular ler bem na TV. */
.campanha-qr{flex-shrink:0;background:#fff;border-radius:24px;padding:22px 22px 16px;text-align:center;box-shadow:0 18px 50px rgba(0,0,0,0.35);}
.campanha-qr img{width:300px;height:300px;display:block;image-rendering:pixelated;}
.campanha-qr .rot{margin-top:10px;font-size:20px;font-weight:600;color:#1B2A55;}
.campanha-fatos{display:flex;gap:14px;flex-wrap:wrap;margin-top:24px;}
.campanha-fato{background:rgba(95,192,233,0.10);border:1px solid rgba(95,192,233,0.35);border-radius:14px;padding:12px 18px;}
.campanha-fato .val{display:block;font-size:30px;font-weight:500;color:var(--paper);letter-spacing:-0.01em;}
.campanha-fato .rot{display:block;font-size:16px;color:var(--muted);margin-top:2px;}
""")
rep("""    // aparelho para aparelho (Apple no Mac, Google na Mi Box), imagem não.
    const arte = s.arte || [];""","""    // aparelho para aparelho (Apple no Mac, Google na Mi Box), imagem não.
    // "qr" é o caminho de uma imagem de QR Code (ocupa o lugar da arte), com
    // "qrRotulo" embaixo; "fatos" é uma lista de {val, rot} em destaque.
    const arte = s.arte || [];""")
rep("""          ${s.premio ? `<div class="campanha-premio">""","""          ${s.fatos ? `<div class="campanha-fatos">${s.fatos.map(f=>`<div class="campanha-fato"><span class="val">${f.val}</span><span class="rot">${f.rot}</span></div>`).join('')}</div>` : ''}
          ${s.premio ? `<div class="campanha-premio">""")
rep("""        ${arte.length ? `<div class="campanha-arte">""","""        ${s.qr ? `<div class="campanha-qr"><img src="${s.qr}" alt="QR Code"><div class="rot">${s.qrRotulo || 'Escaneie e responda'}</div></div>`
          : arte.length ? `<div class="campanha-arte">""")
rep("""`<span class="e${i+1}">${desenho(e)}</span>`).join('')}</div>` : ''}""","""`<span class="e${i+1}">${desenho(e)}</span>`).join('')}</div>` : ''}""")
s,n=re.subn(r"(const VERSAO_PAINEL = /\* versao-do-painel \*/ ')[^']*(')", r"\g<1>2026-11-24-04\2", s); assert n==1
open(ih,'w',encoding='utf-8').write(s)

d=json.load(open(dj,encoding='utf-8'))
assert not any(x.get('qr') for x in d)
slide={
  "type":"campanha","duration":18000,"tema":"azul",
  "eyebrow":"People · Pesquisa de clima",
  "titulo":"A Vixtra que a gente quer se constrói <em>ouvindo quem faz ela acontecer.</em>",
  "texto":"Esta pesquisa é o seu espaço para dizer o que funciona e o que pode ser melhor.",
  "fatos":[{"val":"~15 min","rot":"para responder"},{"val":"100%","rot":"anônima"},{"val":"até 27/11","rot":"período para responder"}],
  "chamada":"Sua voz faz a diferença ;)",
  "qr":"qr/pesquisa-clima.png","qrRotulo":"Escaneie e responda",
  "visivelAte":"2026-11-27"
}
i=next(k for k,x in enumerate(d) if x.get('type')=='goal')
d.insert(i,slide)
open(dj,'w',encoding='utf-8').write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print('ok, slide na posição',i)
