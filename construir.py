#!/usr/bin/env python3
"""Arma la página del recetario a partir de los archivos de texto.

Por qué existe: el recetario se escribe en markdown, un archivo por receta, porque así
cualquiera de la casa puede agregar una. Pero la familia no va a leer markdown en GitHub:
va a abrir un enlace en el celular. Esto lo convierte en una sola página con tres pestañas
—las recetas, la lista del súper y los lugares de Robin Food—, hecha para el pulgar.

Uso:   python3 -I construir.py
Salida: index.html en la raíz, que es lo que publica GitHub Pages.

Qué lee:
  recetas/<sección>/NN-nombre.md   una receta por archivo
  lugares/<ciudad>.md              la lista de dónde comer, por ciudad
  assets/tito.svg                  el dibujo de Tito, que hace dibujar_tito.py
"""
import html
import json
import os
import re
import unicodedata
import urllib.parse

RAIZ = os.path.dirname(os.path.abspath(__file__))

# Cómo se llama cada carpeta en la página. Lo que no esté aquí sale con su propio nombre.
SECCIONES = {"mct": "Con aceite MCT", "casa": "De la casa"}

# Las mismas categorías de las listas del súper que mando los lunes, en el mismo orden.
# El orden importa dos veces: es el orden en que se recorre el súper y el orden en que se
# clasifica, porque "queso de cabra" debe caer en lácteos antes que en proteínas y
# "aceite de oliva" en grasas antes que en despensa.
CATEGORIAS = [
    ("🥛 Lácteos", ["yogur", "leche", "crema", "queso", "ricotta", "jocoque", "brie",
                    "roquefort", "parmesano", "manchego", "cabra", "requeson"]),
    ("🥑 Grasas", ["aceite", "aguacate", "nuez", "nueces", "almendra", "pistache", "avellana",
                   "cacahuate", "tahini", "ajonjoli", "mantequilla", "ghee", "mct", "coco",
                   "aceituna"]),
    ("🥩 Proteínas", ["huevo", "pollo", "res", "cerdo", "pescado", "atun", "camaron", "frijol",
                      "garbanzo", "lenteja", "tofu", "jamon", "tocino", "carne"]),
    ("🌾 Cereales", ["arroz", "quinoa", "farro", "pasta", "paccheri", "rigatoni", "tortilla",
                     "pan", "avena", "camote", "elote", "grano", "harina", "galleta"]),
    ("🍓 Frutas", ["platano", "manzana", "limon", "fresa", "mora", "datil", "arandano",
                   "naranja", "pera", "mango", "uva", "higo"]),
    ("🥬 Verduras", ["coliflor", "betabel", "hongo", "champinon", "portobello", "seta",
                     "cebolla", "ajo", "jitomate", "tomate", "arugula", "endivia", "cilantro",
                     "perejil", "menta", "eneldo", "albahaca", "tomillo", "calabaza",
                     "espinaca", "lechuga", "pepino", "chile", "cebollin", "zanahoria",
                     "apio", "papa"]),
]
CAJON = "🧂 Despensa"       # lo que no cae en ninguna: sal, especias, vinagre, miel…


def sin_acentos(t):
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()


def categoria_de(ingrediente):
    t = sin_acentos(ingrediente)
    for nombre, claves in CATEGORIAS:
        for k in claves:
            if re.search(r"\b" + re.escape(k), t):
                return nombre
    return CAJON


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


def ingredientes_de(texto):
    """Las viñetas que están debajo de '## Ingredientes', tal como se escribieron."""
    m = re.search(r"^## Ingredientes\s*$(.*?)(^## |\Z)", texto, re.M | re.S)
    if not m:
        return []
    return [ln.strip()[2:].strip() for ln in m.group(1).splitlines()
            if ln.strip().startswith("- ")]


def etiquetas(resumen):
    """Las tres cosas que se deciden de un vistazo: qué tan difícil, cuánto tarda y qué tan
    pesada. Salen de la línea de resumen, que ya viene con ese formato."""
    fuera = []
    for trozo in resumen.rstrip(".").split("·"):
        t = trozo.strip()
        if not t:
            continue
        clase = ""
        if t.lower().startswith(("simple", "fácil")):
            clase = "ok"
        elif t.lower().startswith(("laborioso", "medio")):
            clase = "ojo"
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
                           "ing": ingredientes_de(resto),
                           "etq": etiquetas(re.sub(r"\*\*", "", resumen))})
        if fichas:
            todo.append((SECCIONES.get(carpeta, carpeta.capitalize()), fichas))
    return todo


def lugares():
    """La lista de Robin Food: ciudad, categoría y el lugar con su dirección."""
    base = os.path.join(RAIZ, "lugares")
    orden = ["puebla.md", "ciudad-de-mexico.md", "acapulco.md", "por-probar.md"]
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
            salida.append((os.path.splitext(archivo)[0], ciudad, cats))
    return salida


def mapa(nombre, donde, ciudad):
    """Enlace a Google Maps: en el celular abre la app directo."""
    q = urllib.parse.quote(f"{nombre} {donde} {ciudad}".strip())
    return f"https://www.google.com/maps/search/?api=1&query={q}"


CSS = """
:root { --navy:#1C2454; --green:#0F5C4E; --teal:#3E8F7F; --ink:#1E2330; --muted:#5E6573;
        --line:#E3E6EC; --paper:#FFFFFF; --soft:#F6F8FA; --rosa:#E4636F; }
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

header { background:#1C2454; color:#fff; padding:24px 0 20px; }
header .wrap { display:flex; align-items:center; gap:14px; }
header .txt { flex:1; min-width:0; }
header .eyebrow { font-size:11px; letter-spacing:.2em; text-transform:uppercase;
                  color:#9FD3C6; font-weight:700; }
header h1 { margin:4px 0 4px; font-size:27px; line-height:1.1; font-weight:600; color:#fff; }
header p { margin:0; color:#C9CFE3; font-size:14px; }
header img { width:88px; height:auto; flex:none; }

nav.tabs { position:sticky; top:0; z-index:5; background:var(--paper);
           border-bottom:1px solid var(--line); }
nav.tabs .wrap { display:flex; gap:4px; padding-top:6px; }
nav.tabs button { flex:1; border:0; background:none; color:var(--muted); font:inherit;
       font-weight:600; font-size:15px; padding:12px 4px 10px; border-bottom:3px solid transparent;
       cursor:pointer; }
nav.tabs button[aria-selected="true"] { color:var(--navy); border-bottom-color:var(--teal); }
nav.tabs .cuenta { display:inline-block; min-width:19px; padding:0 5px; margin-left:4px;
       background:var(--teal); color:#06231C; border-radius:10px; font-size:12px; }
nav.tabs .cuenta:empty { display:none; }

.buscador { margin:16px 0 4px; }
.buscador input { width:100%; padding:14px 16px; font-size:16px; border-radius:12px;
       border:1px solid var(--line); background:var(--soft); color:var(--ink); }
.buscador input:focus { outline:2px solid var(--teal); outline-offset:1px; }

.chips { display:flex; gap:7px; overflow-x:auto; padding:12px 0 4px; }
.chips button { flex:none; border:1px solid var(--line); background:var(--paper);
      color:var(--muted); border-radius:20px; padding:8px 15px; font:inherit; font-size:14px;
      font-weight:600; cursor:pointer; }
.chips button[aria-pressed="true"] { background:var(--navy); color:#fff; border-color:var(--navy); }
:root[data-theme="dark"] .chips button[aria-pressed="true"] { color:#11141E; }

h2.sec { font-size:12px; letter-spacing:.14em; text-transform:uppercase; color:var(--muted);
       margin:24px 0 10px; font-weight:700; }
.receta { border:1px solid var(--line); border-radius:14px; margin:0 0 10px;
          background:var(--paper); overflow:hidden; }
.receta > summary { cursor:pointer; padding:14px 16px; list-style:none; display:flex;
          gap:12px; align-items:flex-start; }
.receta > summary::-webkit-details-marker { display:none; }
.receta .info { flex:1; min-width:0; }
.receta h3 { margin:0; font-size:19px; color:var(--navy); font-weight:600; line-height:1.25; }
.etq { display:flex; flex-wrap:wrap; gap:6px; margin-top:8px; }
.etq span { font-size:12px; padding:3px 9px; border-radius:20px; background:var(--soft);
            color:var(--muted); border:1px solid var(--line); }
.etq span.ok { background:#E8F5F0; color:#0F5C4E; border-color:#C7E6DC; }
.etq span.ojo { background:#FDF0E7; color:#9A5A22; border-color:#F2D9C5; }
:root[data-theme="dark"] .etq span.ok, :root[data-theme="dark"] .etq span.ojo {
            background:var(--soft); color:var(--ink); border-color:var(--line); }
.add { flex:none; width:42px; height:42px; border-radius:50%; border:1px solid var(--line);
       background:var(--soft); color:var(--navy); font-size:22px; line-height:1; cursor:pointer;
       font-weight:600; }
.add[aria-pressed="true"] { background:var(--teal); border-color:var(--teal); color:#06231C; }
.cuerpo { padding:4px 16px 18px; border-top:1px solid var(--line); margin-top:12px; }
.cuerpo h3 { font-size:12px; letter-spacing:.12em; text-transform:uppercase;
             color:var(--green); margin:18px 0 8px; }
.cuerpo p { margin:0 0 11px; }
.cuerpo ul, .cuerpo ol { margin:0 0 14px; padding-left:22px; }
.cuerpo li { margin:0 0 8px; }

.ciudad { margin:22px 0 8px; display:flex; align-items:baseline; gap:8px; }
.ciudad h2 { margin:0; font-size:21px; color:var(--navy); font-weight:600; }
.ciudad span { font-size:13px; color:var(--muted); }
h3.cat { font-size:14px; margin:18px 0 6px; color:var(--green); font-weight:700; }
a.lugar, .lugar { display:block; padding:11px 14px; border:1px solid var(--line);
          border-radius:12px; margin:0 0 7px; text-decoration:none; color:inherit;
          background:var(--paper); }
.lugar b { display:block; font-weight:600; font-size:16px; color:var(--navy); }
.lugar span { font-size:13px; color:var(--muted); }
a.lugar::after { content:"Mapa ›"; float:right; font-size:12px; color:var(--teal);
                 font-weight:700; margin-top:3px; }

.btn { display:inline-block; border:0; border-radius:12px; padding:13px 18px; font:inherit;
       font-weight:600; font-size:16px; cursor:pointer; background:var(--navy); color:#fff; }
:root[data-theme="dark"] .btn { color:#11141E; }
.btn.sec2 { background:var(--soft); color:var(--ink); border:1px solid var(--line); }
.btn.ancho { display:block; width:100%; margin:10px 0 0; }
form.nuevo { border:1px solid var(--line); border-radius:14px; padding:14px 15px 16px;
       background:var(--soft); margin:12px 0 18px; }
form.nuevo label { display:block; font-size:13px; font-weight:700; color:var(--muted);
       margin:10px 0 5px; }
form.nuevo input, form.nuevo select { width:100%; padding:12px 13px; font-size:16px;
       border-radius:10px; border:1px solid var(--line); background:var(--paper);
       color:var(--ink); }
.hallazgos { margin:10px 0 0; }
.hallazgos button { display:block; width:100%; text-align:left; margin:0 0 6px; padding:11px 13px;
       border:1px solid var(--line); border-radius:10px; background:var(--paper); color:inherit;
       font:inherit; font-size:14px; cursor:pointer; }
.aviso { font-size:13px; color:var(--muted); margin:10px 0 0; }

.lista-cat { font-size:12px; letter-spacing:.1em; text-transform:uppercase; color:var(--green);
       font-weight:700; margin:20px 0 8px; }
label.item { display:flex; gap:11px; align-items:flex-start; padding:10px 12px;
       border:1px solid var(--line); border-radius:11px; margin:0 0 6px; background:var(--paper); }
label.item input { width:22px; height:22px; margin:1px 0 0; flex:none; accent-color:#0F5C4E; }
label.item span { flex:1; }
label.item small { display:block; color:var(--muted); font-size:12px; margin-top:2px; }
label.item.listo span { text-decoration:line-through; color:var(--muted); }

footer { border-top:1px solid var(--line); margin-top:30px; padding:16px 0 70px;
         color:var(--muted); font-size:13px; }
.vacio, .nada { color:var(--muted); padding:16px 2px; }
.oculto { display:none !important; }
"""


JS = r"""
const DATOS = __DATOS__;
const guarda = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
const lee = (k, d) => { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch (e) { return d; } };

let elegidas = lee('recetas-elegidas', []);
let tachados = lee('super-tachado', []);
let nuevos  = lee('lugares-nuevos', []);

/* ---------- pestañas ---------- */
const tabs = [...document.querySelectorAll('nav.tabs button')];
const caja = document.getElementById('q');
const TEXTOS = { recetas:'Buscar: plátano, limón, chocolate…',
                 lugares:'Buscar: tacos, Roma, mariscos…', super:'' };
tabs.forEach(b => b.addEventListener('click', () => {
  tabs.forEach(o => o.setAttribute('aria-selected', String(o === b)));
  document.querySelectorAll('[id^=p-]').forEach(el =>
      el.classList.toggle('oculto', el.id !== 'p-' + b.dataset.p));
  document.querySelector('.buscador').classList.toggle('oculto', b.dataset.p === 'super');
  caja.placeholder = TEXTOS[b.dataset.p] || '';
  filtrar();
  window.scrollTo({ top: 0 });
}));

/* ---------- buscador ---------- */
const vacio = document.querySelector('.vacio');
function filtrar() {
  const panel = document.querySelector('[id^=p-]:not(.oculto)');
  if (!panel || panel.id === 'p-super') { vacio.style.display = 'none'; return; }
  const t = caja.value.trim().toLowerCase();
  let vistas = 0;
  panel.querySelectorAll('.receta, a.lugar').forEach(f => {
    const ciudadOk = !f.dataset.ciudad || ciudad === 'todas' || f.dataset.ciudad === ciudad;
    const hay = ciudadOk && (!t || f.textContent.toLowerCase().includes(t));
    f.classList.toggle('oculto', !hay);
    if (hay) vistas++;
    if (f.tagName === 'DETAILS') f.open = Boolean(t) && hay;
  });
  panel.querySelectorAll('h2.sec, h3.cat, .ciudad').forEach(h => {
    // El encabezado de ciudad cuenta hasta la SIGUIENTE ciudad, no hasta la siguiente
    // categoría: si no, siempre da cero —la categoría viene pegada debajo— y el título
    // de la ciudad se escondía al filtrar.
    const hasta = h.matches('.ciudad') ? '.ciudad' : 'h2.sec, h3.cat, .ciudad';
    let n = 0, s = h.nextElementSibling;
    while (s && !s.matches(hasta)) {
      if (s.matches('.receta, a.lugar') && !s.classList.contains('oculto')) n++;
      s = s.nextElementSibling;
    }
    h.classList.toggle('oculto', n === 0);
  });
  vacio.style.display = vistas ? 'none' : 'block';
}
caja.addEventListener('input', filtrar);

/* ---------- ciudades ---------- */
let ciudad = 'todas';
document.querySelectorAll('.chips button').forEach(b => b.addEventListener('click', () => {
  ciudad = b.dataset.ciudad;
  document.querySelectorAll('.chips button').forEach(o =>
      o.setAttribute('aria-pressed', String(o === b)));
  filtrar();
}));

/* ---------- la lista del súper ---------- */
function pintaLista() {
  const cont = document.getElementById('lista');
  const porCat = {};
  elegidas.forEach(id => {
    const r = DATOS.recetas[id];
    if (!r) return;
    r.ing.forEach(([cat, texto]) => {
      (porCat[cat] = porCat[cat] || []).push([texto, r.titulo]);
    });
  });
  const cats = DATOS.orden.filter(c => porCat[c]);
  if (!cats.length) {
    cont.innerHTML = "<p class='nada'>Todavía no has elegido recetas. Ve a <b>Recetas</b> y " +
      "toca el <b>+</b> de las que vayas a hacer: aquí se junta la lista del súper, " +
      "agrupada como las que manda Lulu.</p>";
    document.getElementById('acciones').classList.add('oculto');
    return;
  }
  let h = '';
  cats.forEach(c => {
    h += `<div class='lista-cat'>${c}</div>`;
    porCat[c].forEach(([texto, de]) => {
      const id = c + '|' + texto + '|' + de;
      const listo = tachados.includes(id);
      h += `<label class='item${listo ? ' listo' : ''}'><input type='checkbox' ` +
           `data-id="${id.replace(/"/g, '&quot;')}"${listo ? ' checked' : ''}>` +
           `<span>${texto}<small>${de}</small></span></label>`;
    });
  });
  cont.innerHTML = h;
  document.getElementById('acciones').classList.remove('oculto');
  cont.querySelectorAll('input').forEach(i => i.addEventListener('change', () => {
    const id = i.dataset.id;
    tachados = i.checked ? [...new Set([...tachados, id])] : tachados.filter(x => x !== id);
    guarda('super-tachado', tachados);
    i.closest('label').classList.toggle('listo', i.checked);
  }));
}

function textoLista() {
  const porCat = {};
  elegidas.forEach(id => {
    const r = DATOS.recetas[id];
    if (!r) return;
    r.ing.forEach(([cat, texto]) => { (porCat[cat] = porCat[cat] || []).push(texto); });
  });
  let t = 'Lista del súper\n';
  DATOS.orden.filter(c => porCat[c]).forEach(c => {
    t += '\n' + c + '\n' + porCat[c].map(x => '• ' + x).join('\n') + '\n';
  });
  t += '\nRecetas: ' + elegidas.map(id => DATOS.recetas[id].titulo).join(', ');
  return t;
}

document.getElementById('compartir').addEventListener('click', async () => {
  const t = textoLista();
  if (navigator.share) { try { await navigator.share({ text: t }); return; } catch (e) {} }
  try { await navigator.clipboard.writeText(t); alert('Lista copiada.'); }
  catch (e) { alert(t); }
});
document.getElementById('limpiar').addEventListener('click', () => {
  if (!confirm('¿Vaciar la lista y desmarcar las recetas?')) return;
  elegidas = []; tachados = [];
  guarda('recetas-elegidas', elegidas); guarda('super-tachado', tachados);
  document.querySelectorAll('.add').forEach(b => b.setAttribute('aria-pressed', 'false'));
  pintaLista(); cuentaTab();
});

document.querySelectorAll('.add').forEach(b => {
  if (elegidas.includes(b.dataset.id)) b.setAttribute('aria-pressed', 'true');
  b.addEventListener('click', e => {
    e.preventDefault(); e.stopPropagation();
    const id = b.dataset.id;
    const puesta = !elegidas.includes(id);
    elegidas = puesta ? [...elegidas, id] : elegidas.filter(x => x !== id);
    b.setAttribute('aria-pressed', String(puesta));
    guarda('recetas-elegidas', elegidas);
    pintaLista(); cuentaTab();
  });
});
function cuentaTab() {
  document.querySelector('nav.tabs .cuenta').textContent = elegidas.length || '';
}

/* ---------- agregar un lugar ---------- */
const form = document.getElementById('f-lugar');
const hallazgos = document.getElementById('hallazgos');
let elegido = null;

document.getElementById('buscar-donde').addEventListener('click', async () => {
  const nombre = form.nombre.value.trim();
  if (!nombre) { form.nombre.focus(); return; }
  hallazgos.innerHTML = "<p class='aviso'>Buscando…</p>";
  const q = encodeURIComponent(nombre + ', ' + form.ciudad.value);
  try {
    const r = await fetch(`https://nominatim.openstreetmap.org/search?format=jsonv2&limit=5&addressdetails=1&q=${q}`,
                          { headers: { 'Accept': 'application/json' } });
    const d = await r.json();
    if (!d.length) {
      // El mapa libre no tiene todos los changarros: probado con cinco de la lista, cuatro
      // salieron y uno no. Para ese caso, el camino de siempre: verlo en Google Maps.
      const u = 'https://www.google.com/maps/search/?api=1&query=' + q;
      hallazgos.innerHTML = "<p class='aviso'>No lo encontré en el mapa abierto. " +
        "Ábrelo en Google Maps, copia la dirección y pégala abajo.</p>" +
        `<a class='btn sec2 ancho' style='text-align:center;text-decoration:none' ` +
        `href='${u}' target='_blank' rel='noopener'>Verlo en Google Maps</a>`;
      return;
    }
    hallazgos.innerHTML = d.map((x, i) =>
      `<button type='button' data-i='${i}'>${x.display_name}</button>`).join('');
    hallazgos.querySelectorAll('button').forEach(b => b.addEventListener('click', () => {
      elegido = d[b.dataset.i];
      const a = elegido.address || {};
      form.donde.value = [[a.road, a.house_number].filter(Boolean).join(' '),
                          a.neighbourhood || a.suburb || a.quarter].filter(Boolean).join(', ')
                         || elegido.display_name.split(',').slice(0, 2).join(',');
      hallazgos.innerHTML = "<p class='aviso'>✓ Dirección tomada del mapa. Corrígela si hace falta.</p>";
    }));
  } catch (e) {
    hallazgos.innerHTML = "<p class='aviso'>No se pudo consultar el mapa. Escribe la " +
      "dirección a mano y mándamelo igual.</p>";
  }
});

form.addEventListener('submit', e => {
  e.preventDefault();
  const n = { nombre: form.nombre.value.trim(), ciudad: form.ciudad.value,
              cat: form.cat.value, donde: form.donde.value.trim() };
  if (!n.nombre) return;
  nuevos = [...nuevos, n];
  guarda('lugares-nuevos', nuevos);
  form.reset(); hallazgos.innerHTML = ''; elegido = null;
  pintaNuevos();
});

function pintaNuevos() {
  const c = document.getElementById('nuevos');
  if (!nuevos.length) { c.innerHTML = ''; return; }
  c.innerHTML = "<h3 class='cat'>Por subir (" + nuevos.length + ")</h3>" +
    nuevos.map(n => `<div class='lugar'><b>${n.nombre}</b><span>${[n.donde, n.ciudad, n.cat]
      .filter(Boolean).join(' · ')}</span></div>`).join('') +
    "<button class='btn ancho' id='mandar'>Mandárselos a Lulu</button>" +
    "<button class='btn sec2 ancho' id='olvidar'>Borrar estos</button>" +
    "<p class='aviso'>Se guardan solo en este teléfono hasta que me los mandes; " +
    "yo verifico la dirección y los subo a la lista de todos.</p>";
  document.getElementById('mandar').addEventListener('click', async () => {
    const t = 'Lugares para el recetario:\n' + nuevos.map(n =>
      `• ${n.nombre} — ${n.donde || 'sin dirección'} (${n.ciudad}${n.cat ? ', ' + n.cat : ''})`).join('\n');
    if (navigator.share) { try { await navigator.share({ text: t }); return; } catch (e) {} }
    try { await navigator.clipboard.writeText(t); alert('Copiado. Pégalo en WhatsApp.'); }
    catch (e) { alert(t); }
  });
  document.getElementById('olvidar').addEventListener('click', () => {
    if (!confirm('¿Borrar los lugares que tienes guardados aquí?')) return;
    nuevos = []; guarda('lugares-nuevos', nuevos); pintaNuevos();
  });
}

pintaLista(); cuentaTab(); pintaNuevos(); filtrar();
"""


def main():
    secs = recetas()
    ciudades = lugares()
    n_rec = sum(len(f) for _, f in secs)
    n_lug = sum(len(l) for _, _, cats in ciudades for _, l in cats)

    datos = {"orden": [c for c, _ in CATEGORIAS] + [CAJON], "recetas": {}}
    for _, fichas in secs:
        for f in fichas:
            datos["recetas"][f["id"]] = {
                "titulo": f["titulo"],
                "ing": [[categoria_de(i), i] for i in f["ing"]]}

    tito = ""
    if os.path.exists(os.path.join(RAIZ, "assets", "tito.svg")):
        tito = "<img src='assets/tito.svg' alt='Tito' width='88'>"

    p = ["<!doctype html><html lang='es'><head><meta charset='utf-8'>",
         "<meta name='viewport' content='width=device-width, initial-scale=1'>",
         "<title>Recetario de Los Reales</title>",
         "<meta name='description' content='Las recetas de la casa, la lista del súper y los "
         "lugares de Robin Food.'>",
         "<meta name='theme-color' content='#1C2454'>",
         "<link rel='icon' href='assets/tito-cara.svg'>",
         "<link rel='apple-touch-icon' href='assets/tito-cara.svg'>",
         f"<style>{CSS}</style></head><body>",
         "<header><div class='wrap'><div class='txt'>",
         "<div class='eyebrow'>Los Reales</div><h1>Recetario de la casa</h1>",
         f"<p>{n_rec} recetas y {n_lug} lugares a los que hay que ir.</p>",
         f"</div>{tito}</div></header>",
         "<nav class='tabs'><div class='wrap'>",
         "<button data-p='recetas' aria-selected='true'>Recetas</button>",
         "<button data-p='super' aria-selected='false'>Mi lista<span class='cuenta'></span></button>",
         "<button data-p='lugares' aria-selected='false'>Dónde comer</button>",
         "</div></nav><div class='wrap'>",
         "<div class='buscador'><input id='q' type='search' "
         "placeholder='Buscar: plátano, limón, chocolate…' aria-label='Buscar'></div>",
         "<p class='vacio oculto'>No hay nada con eso.</p>",
         "<div id='p-recetas'>"]

    for nombre, fichas in secs:
        p.append(f"<h2 class='sec'>{html.escape(nombre)} · {len(fichas)}</h2>")
        for f in fichas:
            etq = "".join(f"<span class='{c}'>{html.escape(t)}</span>" for c, t in f["etq"])
            p.append(
                f"<details class='receta' id='{f['id']}'><summary>"
                f"<div class='info'><h3>{html.escape(f['titulo'])}</h3>"
                f"<div class='etq'>{etq}</div></div>"
                f"<button class='add' data-id='{f['id']}' aria-pressed='false' "
                f"title='Agregar a mi lista del súper'>+</button></summary>"
                f"<div class='cuerpo'>{f['html']}</div></details>")

    # Mi lista del súper
    p.append("</div><div id='p-super' class='oculto'>")
    p.append("<div id='lista'></div>")
    p.append("<div id='acciones' class='oculto'>"
             "<button class='btn ancho' id='compartir'>Compartir la lista</button>"
             "<button class='btn sec2 ancho' id='limpiar'>Vaciar</button>"
             "<p class='aviso'>Lo que tachas se guarda en este teléfono, así que puedes cerrar "
             "la página en el súper y seguir donde ibas.</p></div>")

    # Dónde comer
    p.append("</div><div id='p-lugares' class='oculto'>")
    p.append("<div class='chips'><button data-ciudad='todas' aria-pressed='true'>Todas</button>"
             + "".join(f"<button data-ciudad='{html.escape(cid)}' aria-pressed='false'>"
                       f"{html.escape(nom)}</button>" for cid, nom, _ in ciudades)
             + "</div>")
    p.append("<form class='nuevo' id='f-lugar'>"
             "<label for='n-nombre'>Agregar un lugar</label>"
             "<input id='n-nombre' name='nombre' placeholder='Nombre del lugar' autocomplete='off'>"
             "<label for='n-ciudad'>Ciudad</label>"
             "<select id='n-ciudad' name='ciudad'>"
             + "".join(f"<option>{html.escape(nom)}</option>"
                       for _, nom, _ in ciudades if nom != "Por probar")
             + "<option>Otra</option></select>"
             "<label for='n-cat'>Qué es</label>"
             "<select id='n-cat' name='cat'><option>🌮 Tacos y antojitos</option>"
             "<option>🍽️ Restaurantes</option><option>🦐 Mariscos</option>"
             "<option>🔥 Carnes y brasas</option><option>☕ Café y postres</option>"
             "<option>🍺 Bares y cantinas</option></select>"
             "<button type='button' class='btn sec2 ancho' id='buscar-donde'>"
             "Buscar dónde queda</button>"
             "<div class='hallazgos' id='hallazgos'></div>"
             "<label for='n-donde'>Dirección</label>"
             "<input id='n-donde' name='donde' placeholder='Se llena sola al buscar'>"
             "<button class='btn ancho' type='submit'>Guardar</button>"
             "</form><div id='nuevos'></div>")

    for cid, ciudad, cats in ciudades:
        n = sum(len(l) for _, l in cats)
        p.append(f"<div class='ciudad' data-ciudad='{html.escape(cid)}'>"
                 f"<h2>{html.escape(ciudad)}</h2><span>{n} lugares</span></div>")
        for cat, lista in cats:
            p.append(f"<h3 class='cat'>{html.escape(cat)}</h3>")
            for nombre, donde in lista:
                u = mapa(nombre, donde, ciudad if ciudad != "Por probar" else "")
                p.append(f"<a class='lugar' data-ciudad='{html.escape(cid)}' "
                         f"href='{html.escape(u)}' target='_blank' rel='noopener'>"
                         f"<b>{html.escape(nombre)}</b>"
                         + (f"<span>{html.escape(donde)}</span>" if donde else "") + "</a>")
    p.append("</div>")
    p.append(f"<footer>{n_rec} recetas · {n_lug} lugares · La lista de dónde comer es la de "
             "Robin Food. Se actualiza desde el repositorio de GitHub.</footer>")
    p.append("</div>")
    p.append("<script>" + JS.replace("__DATOS__", json.dumps(datos, ensure_ascii=False))
             + "</script></body></html>")

    open(os.path.join(RAIZ, "index.html"), "w", encoding="utf-8").write("".join(p))
    print(f"ok -> index.html ({n_rec} recetas en {len(secs)} secciones, "
          f"{n_lug} lugares en {len(ciudades)} ciudades)")


if __name__ == "__main__":
    main()
