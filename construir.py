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

# Cómo se llama cada carpeta en la página y en qué orden sale. Lo que no esté aquí va al
# final, con el nombre de su carpeta: así, agregar una sección nueva nunca rompe la página.
SECCIONES = {"desayunos": "Desayunos", "diario": "De diario", "sopas": "Sopas y caldos",
             "casa": "Verduras y ensaladas", "postres": "Postres y antojos",
             "mct": "Con aceite MCT"}
ORDEN = list(SECCIONES)

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
    carpetas = [c for c in ORDEN if os.path.isdir(os.path.join(base, c))]
    carpetas += [c for c in sorted(os.listdir(base))
                 if os.path.isdir(os.path.join(base, c)) and c not in carpetas]
    for carpeta in carpetas:
        ruta = os.path.join(base, carpeta)
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
/* Cocina de casa: papel crema, terracota, olivo y un azulejo de talavera poblana en la
   cabecera. Las animaciones son todas de transform y opacity —las dos cosas que el
   navegador mueve sin recalcular la página— y se apagan solas si el teléfono pide menos
   movimiento. Ni una imagen de fondo: el azulejo son degradados. */
:root { --tinta:#2B2420; --muted:#7A6A5C; --papel:#FBF7F0; --tarjeta:#FFFFFF;
        --linea:#E7DDCE; --suave:#F4EDE1;
        --terracota:#C4572F; --olivo:#4F6B4A; --talavera:#2B4C8C; --mostaza:#D99B2B;
        --sombra:0 1px 2px rgba(74,56,40,.06), 0 6px 18px rgba(74,56,40,.05); }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
        --tinta:#F0E7DC; --muted:#B5A795; --papel:#17140F; --tarjeta:#201B16;
        --linea:#362E26; --suave:#241E18;
        --terracota:#E88A62; --olivo:#9BBF91; --talavera:#8FB0EE; --mostaza:#EFC069;
        --sombra:0 1px 2px rgba(0,0,0,.4); } }
:root[data-theme="dark"] { --tinta:#F0E7DC; --muted:#B5A795; --papel:#17140F;
        --tarjeta:#201B16; --linea:#362E26; --suave:#241E18; --terracota:#E88A62;
        --olivo:#9BBF91; --talavera:#8FB0EE; --mostaza:#EFC069;
        --sombra:0 1px 2px rgba(0,0,0,.4); }
* { box-sizing:border-box; -webkit-tap-highlight-color:transparent; }
body { margin:0; background:var(--papel); color:var(--tinta); line-height:1.5;
       font-family:-apple-system,BlinkMacSystemFont,"Avenir Next","Segoe UI",Roboto,sans-serif;
       font-size:17px; }
.serif { font-family:"Iowan Old Style","Palatino","Georgia",serif; }
.wrap { max-width:720px; margin:0 auto; padding:0 16px; }

/* --- Cabecera con azulejo --- */
header { position:relative; background:var(--talavera); color:#FFF8EC; padding:26px 0 22px;
         overflow:hidden; }
header::before { content:""; position:absolute; inset:0; opacity:.34;
  background-image:
    radial-gradient(circle at 50% 50%, rgba(255,248,236,.5) 1.6mm, transparent 1.7mm),
    repeating-linear-gradient(45deg, rgba(255,248,236,.16) 0 2px, transparent 2px 13px),
    repeating-linear-gradient(-45deg, rgba(255,248,236,.16) 0 2px, transparent 2px 13px);
  background-size:26px 26px, 26px 26px, 26px 26px; }
header .wrap { position:relative; display:flex; align-items:center; gap:14px; }
header .txt { flex:1; min-width:0; }
header .eyebrow { font-size:11px; letter-spacing:.24em; text-transform:uppercase;
                  color:#FFD9A8; font-weight:700; }
header h1 { margin:5px 0 5px; font-size:30px; line-height:1.05; font-weight:600;
            color:#FFF8EC; letter-spacing:-.01em; }
header p { margin:0; color:#DCE6FA; font-size:14px; }
.tito { position:relative; width:96px; flex:none; }
.tito img { width:96px; height:auto; display:block; }
.anim .tito img { animation:entra-tito .7s cubic-bezier(.2,.9,.3,1.2) both; }
.vapor { position:absolute; left:14px; top:-14px; width:60px; height:30px; opacity:.85; }
.vapor span { position:absolute; bottom:0; width:7px; height:7px; border-radius:50%;
              background:#FFF8EC; opacity:0; animation:vapor 3.4s ease-in-out infinite; }
.vapor span:nth-child(1) { left:4px;  animation-delay:0s; }
.vapor span:nth-child(2) { left:24px; animation-delay:1.1s; }
.vapor span:nth-child(3) { left:44px; animation-delay:2.2s; }
@keyframes vapor {
  0%   { transform:translateY(6px) scale(.6); opacity:0; }
  25%  { opacity:.75; }
  100% { transform:translateY(-24px) scale(1.5); opacity:0; } }
@keyframes entra-tito { from { transform:translateY(10px) rotate(-6deg); opacity:0; } }

/* --- Pestañas --- */
nav.tabs { position:sticky; top:0; z-index:5; background:var(--papel);
           border-bottom:1px solid var(--linea); }
nav.tabs .wrap { display:flex; gap:4px; padding-top:6px; }
nav.tabs button { flex:1; border:0; background:none; color:var(--muted); font:inherit;
       font-weight:600; font-size:15px; padding:12px 4px 10px; border-bottom:3px solid transparent;
       cursor:pointer; transition:color .18s ease; }
nav.tabs button[aria-selected="true"] { color:var(--terracota);
       border-bottom-color:var(--terracota); }
nav.tabs .cuenta { display:inline-block; min-width:19px; padding:0 5px; margin-left:4px;
       background:var(--terracota); color:#FFF8EC; border-radius:10px; font-size:12px;
       animation:pop .3s cubic-bezier(.2,.9,.3,1.5); }
nav.tabs .cuenta:empty { display:none; }
@keyframes pop { from { transform:scale(.4); } }

.buscador { margin:16px 0 4px; }
.buscador input { width:100%; padding:14px 16px 14px 44px; font-size:16px; border-radius:14px;
       border:1px solid var(--linea); background:var(--tarjeta) url("data:image/svg+xml,\
%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%237A6A5C'\
 stroke-width='2'%3E%3Ccircle cx='11' cy='11' r='7'/%3E%3Cpath d='M20 20l-3.5-3.5'/%3E%3C/svg%3E")
       14px 50% / 18px no-repeat; color:var(--tinta); transition:border-color .18s ease; }
.buscador input:focus { outline:none; border-color:var(--olivo);
       box-shadow:0 0 0 3px rgba(79,107,74,.15); }

.chips { display:flex; gap:7px; overflow-x:auto; padding:12px 0 4px; }
.chips button { flex:none; border:1px solid var(--linea); background:var(--tarjeta);
      color:var(--muted); border-radius:20px; padding:8px 15px; font:inherit; font-size:14px;
      font-weight:600; cursor:pointer; transition:transform .15s ease, background .15s ease; }
.chips button:active { transform:scale(.95); }
.chips button[aria-pressed="true"] { background:var(--olivo); color:#FFF8EC;
      border-color:var(--olivo); }

/* --- Recetas --- */
h2.sec { font-size:12px; letter-spacing:.16em; text-transform:uppercase; color:var(--muted);
       margin:26px 0 10px; font-weight:700; display:flex; align-items:center; gap:10px; }
h2.sec::after { content:""; flex:1; height:1px; background:var(--linea); }
.receta { border:1px solid var(--linea); border-radius:16px; margin:0 0 10px;
          background:var(--tarjeta); box-shadow:var(--sombra);
          }
.anim .receta { animation:sube .45s ease both; animation-delay:calc(var(--i, 0) * 45ms); }
@keyframes sube { from { transform:translateY(10px); opacity:0; } }
.receta > summary { cursor:pointer; padding:15px 16px; list-style:none; display:flex;
          gap:12px; align-items:flex-start; }
.receta > summary::-webkit-details-marker { display:none; }
.receta .info { flex:1; min-width:0; }
.receta h3 { margin:0; font-size:20px; color:var(--tinta); font-weight:600; line-height:1.22;
          font-family:"Iowan Old Style","Palatino","Georgia",serif; }
.receta[open] { border-color:var(--terracota); }
.etq { display:flex; flex-wrap:wrap; gap:6px; margin-top:9px; }
.etq span { font-size:12px; padding:3px 10px; border-radius:20px; background:var(--suave);
            color:var(--muted); }
.etq span.ok { background:rgba(79,107,74,.14); color:var(--olivo); font-weight:600; }
.etq span.ojo { background:rgba(196,87,47,.13); color:var(--terracota); font-weight:600; }
.add { flex:none; width:44px; height:44px; border-radius:50%; border:1px solid var(--linea);
       background:var(--suave); color:var(--terracota); font-size:23px; line-height:1;
       cursor:pointer; font-weight:600; transition:transform .18s cubic-bezier(.2,.9,.3,1.6),
       background .18s ease, color .18s ease; }
.add:active { transform:scale(.88); }
.add[aria-pressed="true"] { background:var(--olivo); border-color:var(--olivo); color:#FFF8EC;
       transform:scale(1.06); }
.cuerpo { padding:2px 16px 18px; border-top:1px solid var(--linea); margin-top:13px; }
.receta[open] .cuerpo { animation:abre .28s ease both; }
@keyframes abre { from { transform:translateY(-6px); opacity:0; } }
.cuerpo h3 { font-size:12px; letter-spacing:.14em; text-transform:uppercase;
             color:var(--terracota); margin:18px 0 8px; font-weight:700; }
.cuerpo p { margin:0 0 11px; }
.cuerpo ul, .cuerpo ol { margin:0 0 14px; padding-left:4px; list-style:none; counter-reset:paso; }
.cuerpo ul li { margin:0 0 8px; padding-left:20px; position:relative; }
.cuerpo ul li::before { content:""; position:absolute; left:3px; top:.62em; width:7px;
       height:7px; border-radius:50%; background:var(--mostaza); }
.cuerpo ol li { margin:0 0 11px; padding-left:34px; position:relative; counter-increment:paso; }
.cuerpo ol li::before { content:counter(paso); position:absolute; left:0; top:0; width:24px;
       height:24px; border-radius:50%; background:var(--suave); color:var(--terracota);
       font-size:13px; font-weight:700; display:grid; place-items:center; }

/* --- Lugares --- */
.ciudad { margin:24px 0 8px; display:flex; align-items:baseline; gap:8px; }
.ciudad h2 { margin:0; font-size:23px; color:var(--tinta); font-weight:600;
       font-family:"Iowan Old Style","Palatino","Georgia",serif; }
.ciudad span { font-size:13px; color:var(--muted); }
h3.cat { font-size:14px; margin:18px 0 7px; color:var(--olivo); font-weight:700; }
a.lugar, .lugar { display:block; padding:12px 14px; border:1px solid var(--linea);
          border-radius:14px; margin:0 0 7px; text-decoration:none; color:inherit;
          background:var(--tarjeta); transition:transform .15s ease, border-color .15s ease; }
a.lugar:active { transform:scale(.99); border-color:var(--terracota); }
.lugar b { display:block; font-weight:600; font-size:16px; color:var(--tinta); }
.lugar span { font-size:13px; color:var(--muted); }
a.lugar::after { content:"Mapa ›"; float:right; font-size:12px; color:var(--terracota);
                 font-weight:700; margin-top:3px; }

/* --- Botones y formulario --- */
.btn { display:inline-block; border:0; border-radius:14px; padding:14px 18px; font:inherit;
       font-weight:600; font-size:16px; cursor:pointer; background:var(--terracota);
       color:#FFF8EC; transition:transform .15s ease, filter .15s ease; }
.btn:active { transform:scale(.97); filter:brightness(.95); }
.btn.sec2 { background:var(--suave); color:var(--tinta); border:1px solid var(--linea); }
.btn.ancho { display:block; width:100%; margin:10px 0 0; }
form.nuevo { border:1px solid var(--linea); border-radius:16px; padding:15px 15px 17px;
       background:var(--suave); margin:12px 0 18px; }
form.nuevo label { display:block; font-size:13px; font-weight:700; color:var(--muted);
       margin:11px 0 5px; }
form.nuevo input, form.nuevo select { width:100%; padding:13px; font-size:16px;
       border-radius:12px; border:1px solid var(--linea); background:var(--tarjeta);
       color:var(--tinta); }
.hallazgos { margin:10px 0 0; }
.hallazgos button { display:block; width:100%; text-align:left; margin:0 0 6px; padding:11px 13px;
       border:1px solid var(--linea); border-radius:12px; background:var(--tarjeta);
       color:inherit; font:inherit; font-size:14px; cursor:pointer; }
.aviso { font-size:13px; color:var(--muted); margin:10px 0 0; }

/* --- La lista del súper --- */
.lista-cat { font-size:12px; letter-spacing:.14em; text-transform:uppercase; color:var(--olivo);
       font-weight:700; margin:22px 0 8px; display:flex; align-items:center; gap:10px; }
.lista-cat::after { content:""; flex:1; height:1px; background:var(--linea); }
label.item { display:flex; gap:12px; align-items:flex-start; padding:11px 13px;
       border:1px solid var(--linea); border-radius:13px; margin:0 0 6px;
       background:var(--tarjeta); transition:opacity .2s ease, background .2s ease; }
label.item input { width:22px; height:22px; margin:1px 0 0; flex:none; accent-color:#4F6B4A; }
label.item span { flex:1; transition:opacity .2s ease; }
label.item small { display:block; color:var(--muted); font-size:12px; margin-top:2px; }
label.item.listo { background:var(--suave); }
label.item.listo span { text-decoration:line-through; opacity:.55; }

footer { border-top:1px solid var(--linea); margin-top:32px; padding:16px 0 70px;
         color:var(--muted); font-size:13px; }
.vacio, .nada { color:var(--muted); padding:16px 2px; }
.oculto { display:none !important; }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation:none !important; transition:none !important; } }
@media print {
  *, *::before, *::after { animation:none !important; transition:none !important; }
  header::before, .vapor { display:none; } }
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
document.body.classList.add('anim');
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
        # El vapor son tres puntos que suben; cuesta menos que cualquier imagen animada.
        tito = ("<div class='tito'><div class='vapor'><span></span><span></span>"
                "<span></span></div><img src='assets/tito.svg' alt='Tito' width='96'></div>")

    p = ["<!doctype html><html lang='es'><head><meta charset='utf-8'>",
         "<meta name='viewport' content='width=device-width, initial-scale=1'>",
         "<title>Recetario de Los Reales</title>",
         "<meta name='description' content='Las recetas de la casa, la lista del súper y los "
         "lugares de Robin Food.'>",
         "<meta name='theme-color' content='#2B4C8C'>",
         # Para que al guardarla en la pantalla de inicio abra como app y no como pestaña.
         # ⚠️ iOS NO acepta SVG en apple-touch-icon: ahí va el PNG de 180 sí o sí.
         "<link rel='manifest' href='manifest.webmanifest'>",
         "<link rel='icon' href='assets/logo.svg'>",
         "<link rel='icon' type='image/png' sizes='192x192' href='assets/logo-192.png'>",
         "<link rel='apple-touch-icon' href='assets/logo-180.png'>",
         "<meta name='apple-mobile-web-app-capable' content='yes'>",
         "<meta name='mobile-web-app-capable' content='yes'>",
         "<meta name='apple-mobile-web-app-title' content='Recetario'>",
         "<meta name='apple-mobile-web-app-status-bar-style' content='black-translucent'>",
         f"<style>{CSS}</style></head><body>",
         "<header><div class='wrap'><div class='txt'>",
         "<div class='eyebrow'>Los Reales</div><h1 class='serif'>Recetario de la casa</h1>",
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
        for i, f in enumerate(fichas):
            etq = "".join(f"<span class='{c}'>{html.escape(t)}</span>" for c, t in f["etq"])
            # --i escalona la entrada; se corta en 8 para que la última no se haga esperar.
            p.append(
                f"<details class='receta' id='{f['id']}' style='--i:{min(i, 8)}'><summary>"
                f"<div class='info'><h3>{html.escape(f['titulo'])}</h3>"
                f"<div class='etq'>{etq}</div></div>"
                # La ficha de cómo usar el aceite no es una receta: no lleva botón de
                # agregar, porque no tiene nada que mandar a la lista del súper.
                + (f"<button class='add' data-id='{f['id']}' aria-pressed='false' "
                   f"title='Agregar a mi lista del súper'>+</button>" if f["ing"] else "")
                + "</summary>"
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
