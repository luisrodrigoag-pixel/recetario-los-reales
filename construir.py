#!/usr/bin/env python3
"""Arma la página del recetario a partir de los archivos de texto.

Por qué existe: el recetario se escribe en markdown, un archivo por receta, porque así
cualquiera de la casa puede agregar una. Pero la familia no va a leer markdown en GitHub:
va a abrir un enlace en el celular. Esto lo convierte en una sola página con dos pestañas
—las recetas y los lugares de Robin Food—, buscador y todo pensado para el pulgar.

Uso:   python3 -I construir.py
Salida: index.html en la raíz, que es lo que publica GitHub Pages.

Qué lee:
  recetas/<sección>/NN-nombre.md   una receta por archivo
  lugares/<ciudad>.md              la lista de dónde comer, por ciudad
  assets/tito.svg                  el dibujo de Tito, que hace dibujar_tito.py
"""
import html
import os
import re
import urllib.parse

RAIZ = os.path.dirname(os.path.abspath(__file__))

# Cómo se llama cada carpeta en la página. Lo que no esté aquí sale con su propio nombre.
SECCIONES = {"mct": "Con aceite MCT", "casa": "De la casa"}


def md(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"<em>\1</em>", t)
    return t


def cuerpo(texto):
    """El markdown de una receta, ya sin su título, convertido a HTML."""
    out, lista, orden = [], [], False

    def cerrar():
        if lista:
            tag = "ol" if orden else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{x}</li>" for x in lista) + f"</{tag}>")
            lista.clear()

    for ln in texto.splitlines():
        s = ln.strip()
        if not s:
            cerrar()
            continue
        if s.startswith("## "):
            cerrar()
            out.append(f"<h3>{md(s[3:])}</h3>")
        elif re.match(r"^\d+\.\s", s):
            if not orden:
                cerrar()
                orden = True
            lista.append(md(re.sub(r"^\d+\.\s", "", s)))
        elif s.startswith("- "):
            if orden:
                cerrar()
                orden = False
            lista.append(md(s[2:]))
        else:
            cerrar()
            orden = False
            out.append(f"<p>{md(s)}</p>")
    cerrar()
    return "".join(out)


def etiquetas(resumen):
    """Las tres cosas que se deciden de un vistazo: qué tan difícil, cuánto tarda, qué tan
    pesada. Salen de la línea de resumen, que ya viene con ese formato."""
    fuera = []
    for trozo in resumen.rstrip(".").split("·"):
        t = trozo.strip()
        if not t:
            continue
        clase = "t"
        if t.lower().startswith(("simple", "fácil")):
            clase = "t ok"
        elif t.lower().startswith(("laborioso", "medio")):
            clase = "t ojo"
        fuera.append((clase, t))
    return fuera


def recetas():
    base = os.path.join(RAIZ, "recetas")
    todo = []
    if not os.path.isdir(base):
        return todo
    for carpeta in sorted(os.listdir(base)):
        ruta = os.path.join(base, carpeta)
        if not os.path.isdir(ruta):
            continue
        fichas = []
        for archivo in sorted(os.listdir(ruta)):
            if not archivo.endswith(".md"):
                continue
            texto = open(os.path.join(ruta, archivo), encoding="utf-8").read()
            m = re.search(r"^# (.+)$", texto, re.M)
            if not m:
                continue
            resto = texto[m.end():].strip()
            resumen = ""
            for ln in resto.splitlines():
                if ln.strip() and not ln.startswith(("#", "-", "*", "1.")):
                    resumen = ln.strip()
                    break
            fichas.append({"id": os.path.splitext(archivo)[0], "titulo": m.group(1).strip(),
                           "resumen": resumen, "html": cuerpo(resto),
                           "etq": etiquetas(re.sub(r"\*\*", "", resumen))})
        if fichas:
            todo.append((SECCIONES.get(carpeta, carpeta.capitalize()), fichas))
    return todo


def lugares():
    """La lista de Robin Food: ciudad, categoría y el lugar con su dirección."""
    base = os.path.join(RAIZ, "lugares")
    orden = ["ciudad-de-mexico.md", "puebla.md", "acapulco.md", "por-probar.md"]
    salida = []
    if not os.path.isdir(base):
        return salida
    archivos = [a for a in orden if os.path.exists(os.path.join(base, a))]
    archivos += [a for a in sorted(os.listdir(base))
                 if a.endswith(".md") and a not in archivos]
    for archivo in archivos:
        texto = open(os.path.join(base, archivo), encoding="utf-8").read()
        m = re.search(r"^# (.+)$", texto, re.M)
        if not m:
            continue
        ciudad, cats, actual = m.group(1).strip(), [], None
        for ln in texto[m.end():].splitlines():
            s = ln.strip()
            if s.startswith("## "):
                actual = (s[3:].strip(), [])
                cats.append(actual)
            elif s.startswith("- ") and actual is not None:
                nombre, _, donde = s[2:].partition("—")
                cats[-1][1].append((nombre.strip(), donde.strip()))
        cats = [c for c in cats if c[1]]
        if cats:
            salida.append((ciudad, cats))
    return salida


def mapa(nombre, donde, ciudad):
    """Enlace a Google Maps: en el celular abre la app directo."""
    q = urllib.parse.quote(f"{nombre} {donde} {ciudad}".strip())
    return f"https://www.google.com/maps/search/?api=1&query={q}"


CSS = """
:root { --navy:#1C2454; --green:#0F5C4E; --teal:#3E8F7F; --ink:#1E2330; --muted:#5E6573;
        --line:#E3E6EC; --paper:#FFFFFF; --soft:#F6F8FA; --canela:#C87B3C; --rosa:#E4636F; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
        --navy:#C3CEFF; --green:#8FE0CB; --teal:#8FE0CB; --ink:#E9EBF3; --muted:#AAB1C3;
        --line:#2B3148; --paper:#11141E; --soft:#1A1F2E; } }
:root[data-theme="dark"] { --navy:#C3CEFF; --green:#8FE0CB; --teal:#8FE0CB; --ink:#E9EBF3;
        --muted:#AAB1C3; --line:#2B3148; --paper:#11141E; --soft:#1A1F2E; }
* { box-sizing:border-box; -webkit-tap-highlight-color:transparent; }
body { margin:0; background:var(--paper); color:var(--ink); line-height:1.5;
       font-family:-apple-system,BlinkMacSystemFont,"Avenir Next","Segoe UI",Roboto,sans-serif;
       font-size:17px; }
.wrap { max-width:720px; margin:0 auto; padding:0 16px; }

header { background:#1C2454; color:#fff; padding:26px 0 22px; }
header .wrap { display:flex; align-items:center; gap:14px; }
header .txt { flex:1; min-width:0; }
header .eyebrow { font-size:11px; letter-spacing:.2em; text-transform:uppercase;
                  color:#9FD3C6; font-weight:700; }
header h1 { margin:4px 0 4px; font-size:28px; line-height:1.1; font-weight:600; color:#fff; }
header p { margin:0; color:#C9CFE3; font-size:14px; }
header img { width:92px; height:auto; flex:none; }

nav.tabs { position:sticky; top:0; z-index:5; background:var(--paper);
           border-bottom:1px solid var(--line); }
nav.tabs .wrap { display:flex; gap:6px; padding-top:8px; }
nav.tabs button { flex:1; border:0; background:none; color:var(--muted); font:inherit;
       font-weight:600; font-size:15px; padding:12px 8px 11px; border-bottom:3px solid transparent;
       cursor:pointer; }
nav.tabs button[aria-selected="true"] { color:var(--navy); border-bottom-color:var(--teal); }

.buscador { margin:16px 0 4px; position:relative; }
.buscador input { width:100%; padding:14px 16px; font-size:16px; border-radius:12px;
       border:1px solid var(--line); background:var(--soft); color:var(--ink); }
.buscador input:focus { outline:2px solid var(--teal); outline-offset:1px; }

h2.sec { font-size:12px; letter-spacing:.14em; text-transform:uppercase; color:var(--muted);
       margin:26px 0 10px; font-weight:700; }
.receta { border:1px solid var(--line); border-radius:14px; margin:0 0 10px;
          background:var(--paper); overflow:hidden; }
.receta > summary { cursor:pointer; padding:15px 17px; list-style:none; }
.receta > summary::-webkit-details-marker { display:none; }
.receta h3 { margin:0; font-size:19px; color:var(--navy); font-weight:600; line-height:1.25; }
.etq { display:flex; flex-wrap:wrap; gap:6px; margin-top:9px; }
.etq span { font-size:12px; padding:3px 9px; border-radius:20px; background:var(--soft);
            color:var(--muted); border:1px solid var(--line); }
.etq span.ok { background:#E8F5F0; color:#0F5C4E; border-color:#C7E6DC; }
.etq span.ojo { background:#FDF0E7; color:#9A5A22; border-color:#F2D9C5; }
:root[data-theme="dark"] .etq span.ok, :root[data-theme="dark"] .etq span.ojo { background:var(--soft); }
.cuerpo { padding:4px 17px 18px; border-top:1px solid var(--line); margin-top:13px; }
.cuerpo h3 { font-size:12px; letter-spacing:.12em; text-transform:uppercase;
             color:var(--green); margin:18px 0 8px; }
.cuerpo p { margin:0 0 11px; }
.cuerpo ul, .cuerpo ol { margin:0 0 14px; padding-left:22px; }
.cuerpo li { margin:0 0 8px; }

.ciudad { margin:26px 0 8px; display:flex; align-items:baseline; gap:8px; }
.ciudad h2 { margin:0; font-size:21px; color:var(--navy); font-weight:600; }
.ciudad span { font-size:13px; color:var(--muted); }
h3.cat { font-size:14px; margin:18px 0 6px; color:var(--green); font-weight:700; }
a.lugar { display:block; padding:11px 14px; border:1px solid var(--line); border-radius:12px;
          margin:0 0 7px; text-decoration:none; color:inherit; background:var(--paper); }
a.lugar b { display:block; font-weight:600; font-size:16px; color:var(--navy); }
a.lugar span { font-size:13px; color:var(--muted); }
a.lugar::after { content:"Mapa ›"; float:right; font-size:12px; color:var(--teal);
                 font-weight:700; margin-top:3px; }

footer { border-top:1px solid var(--line); margin-top:34px; padding:16px 0 60px;
         color:var(--muted); font-size:13px; }
.vacio { color:var(--muted); padding:18px 2px; display:none; }
.oculto { display:none !important; }
"""

JS = """
const tabs = [...document.querySelectorAll('nav.tabs button')];
const paneles = { recetas: document.getElementById('p-recetas'),
                  lugares: document.getElementById('p-lugares') };
tabs.forEach(b => b.addEventListener('click', () => {
  tabs.forEach(o => o.setAttribute('aria-selected', String(o === b)));
  Object.entries(paneles).forEach(([k, el]) => el.classList.toggle('oculto', k !== b.dataset.p));
  caja.placeholder = b.dataset.p === 'recetas'
      ? 'Buscar: plátano, limón, chocolate…' : 'Buscar: tacos, Roma, mariscos…';
  filtrar();
  window.scrollTo({top:0});
}));

const caja = document.getElementById('q');
const vacio = document.querySelector('.vacio');
function filtrar() {
  const t = caja.value.trim().toLowerCase();
  const panel = document.querySelector('[id^=p-]:not(.oculto)');
  let vistas = 0;
  panel.querySelectorAll('.receta, a.lugar').forEach(f => {
    const hay = !t || f.textContent.toLowerCase().includes(t);
    f.classList.toggle('oculto', !hay);
    if (hay) vistas++;
    if (f.tagName === 'DETAILS') f.open = Boolean(t) && hay;
  });
  panel.querySelectorAll('h2.sec, h3.cat, .ciudad').forEach(h => {
    let n = 0, s = h.nextElementSibling;
    while (s && !s.matches('h2.sec, h3.cat, .ciudad')) {
      if ((s.matches('.receta, a.lugar')) && !s.classList.contains('oculto')) n++;
      s = s.nextElementSibling;
    }
    h.classList.toggle('oculto', t !== '' && n === 0);
  });
  vacio.style.display = vistas ? 'none' : 'block';
}
caja.addEventListener('input', filtrar);
"""


def main():
    secs = recetas()
    ciudades = lugares()
    n_rec = sum(len(f) for _, f in secs)
    n_lug = sum(len(l) for _, cats in ciudades for _, l in cats)
    tito = ""
    svg = os.path.join(RAIZ, "assets", "tito.svg")
    if os.path.exists(svg):
        tito = "<img src='assets/tito.svg' alt='Tito' width='92'>"

    p = ["<!doctype html><html lang='es'><head><meta charset='utf-8'>",
         "<meta name='viewport' content='width=device-width, initial-scale=1'>",
         "<title>Recetario de Los Reales</title>",
         "<meta name='description' content='Las recetas de la casa y los lugares de Robin Food.'>",
         "<meta name='theme-color' content='#1C2454'>",
         "<link rel='icon' href='assets/tito-cara.svg'>",
         f"<style>{CSS}</style></head><body>",
         "<header><div class='wrap'><div class='txt'>",
         "<div class='eyebrow'>Los Reales</div><h1>Recetario de la casa</h1>",
         f"<p>{n_rec} recetas y {n_lug} lugares a los que hay que ir.</p>",
         f"</div>{tito}</div></header>",
         "<nav class='tabs'><div class='wrap'>",
         "<button data-p='recetas' aria-selected='true'>Recetas</button>",
         "<button data-p='lugares' aria-selected='false'>Dónde comer</button>",
         "</div></nav><div class='wrap'>",
         "<div class='buscador'><input id='q' type='search' "
         "placeholder='Buscar: plátano, limón, chocolate…' aria-label='Buscar'></div>",
         "<p class='vacio'>No hay nada con eso.</p>",
         "<div id='p-recetas'>"]

    for nombre, fichas in secs:
        p.append(f"<h2 class='sec'>{html.escape(nombre)} · {len(fichas)}</h2>")
        for f in fichas:
            etq = "".join(f"<span class='{c.split(' ',1)[1] if ' ' in c else ''}'>"
                          f"{html.escape(t)}</span>" for c, t in f["etq"])
            p.append(f"<details class='receta' id='{f['id']}'><summary>"
                     f"<h3>{html.escape(f['titulo'])}</h3>"
                     f"<div class='etq'>{etq}</div></summary>"
                     f"<div class='cuerpo'>{f['html']}</div></details>")
    p.append("</div><div id='p-lugares' class='oculto'>")
    for ciudad, cats in ciudades:
        n = sum(len(l) for _, l in cats)
        p.append(f"<div class='ciudad'><h2>{html.escape(ciudad)}</h2>"
                 f"<span>{n} lugares</span></div>")
        for cat, lista in cats:
            p.append(f"<h3 class='cat'>{html.escape(cat)}</h3>")
            for nombre, donde in lista:
                u = mapa(nombre, donde, ciudad if ciudad != "Por probar" else "")
                p.append(f"<a class='lugar' href='{html.escape(u)}' target='_blank' "
                         f"rel='noopener'><b>{html.escape(nombre)}</b>"
                         + (f"<span>{html.escape(donde)}</span>" if donde else "") + "</a>")
    p.append("</div>")
    p.append(f"<footer>{n_rec} recetas · {n_lug} lugares · La lista de dónde comer es la de "
             "Robin Food. Se actualiza desde el repositorio de GitHub.</footer>")
    p.append("</div>")
    p.append(f"<script>{JS}</script></body></html>")

    open(os.path.join(RAIZ, "index.html"), "w", encoding="utf-8").write("".join(p))
    print(f"ok -> index.html ({n_rec} recetas en {len(secs)} secciones, "
          f"{n_lug} lugares en {len(ciudades)} ciudades)")


if __name__ == "__main__":
    main()
