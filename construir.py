#!/usr/bin/env python3
"""Arma el index.html del recetario a partir de las recetas en markdown.

Por qué existe: el recetario se escribe en markdown, un archivo por receta, porque así
cualquiera de la casa puede agregar una desde el teléfono. Pero la familia no va a leer
markdown en GitHub: va a abrir un enlace. Este script convierte las recetas en una sola
página con índice y buscador, hecha para el celular.

Uso:   python3 -I construir.py
Salida: index.html en la raíz, que es lo que publica GitHub Pages.

Para agregar una receta: un archivo nuevo en recetas/<sección>/NN-nombre.md con un título
`# Así`, y volver a correr esto. Las secciones salen de los nombres de las carpetas.
"""
import html
import os
import re

RAIZ = os.path.dirname(os.path.abspath(__file__))
SECCIONES = {"mct": "Con aceite MCT"}       # carpeta -> cómo se llama en la página


def md(t):
    """Markdown mínimo: el que de verdad usan las recetas."""
    t = html.escape(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"<em>\1</em>", t)
    return t


def cuerpo(texto):
    """Convierte el markdown de una receta en HTML, sin el título."""
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


def leer():
    todo = []
    base = os.path.join(RAIZ, "recetas")
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
            titulo = m.group(1).strip()
            resto = texto[m.end():].strip()
            resumen = ""
            for ln in resto.splitlines():
                if ln.strip() and not ln.startswith(("#", "-", "*")):
                    resumen = ln.strip()
                    break
            fichas.append({"id": os.path.splitext(archivo)[0], "titulo": titulo,
                           "resumen": resumen, "html": cuerpo(resto)})
        if fichas:
            todo.append((SECCIONES.get(carpeta, carpeta.capitalize()), fichas))
    return todo


CSS = """
:root { --navy:#1C2454; --green:#0F5C4E; --teal:#3E8F7F; --ink:#1E2330; --muted:#5E6573;
        --line:#E3E6EC; --paper:#FFFFFF; --soft:#F6F8FA; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
        --navy:#AFC0FF; --green:#7FD6C0; --teal:#7FD6C0; --ink:#E8EAF2; --muted:#A7AEC0;
        --line:#2A3048; --paper:#12151F; --soft:#1A1F2E; } }
:root[data-theme="dark"] { --navy:#AFC0FF; --green:#7FD6C0; --teal:#7FD6C0; --ink:#E8EAF2;
        --muted:#A7AEC0; --line:#2A3048; --paper:#12151F; --soft:#1A1F2E; }
* { box-sizing:border-box; }
body { margin:0; background:var(--paper); color:var(--ink); line-height:1.5;
       font-family:-apple-system,BlinkMacSystemFont,"Avenir Next","Segoe UI",Roboto,sans-serif; }
header { background:var(--navy); color:#fff; padding:40px 16px 34px; }
header .wrap { max-width:760px; margin:0 auto; }
header .eyebrow { font-size:12px; letter-spacing:.2em; text-transform:uppercase;
                  color:#9FD3C6; font-weight:600; margin-bottom:10px; }
header h1 { margin:0 0 8px; font-size:34px; line-height:1.1; font-weight:600; color:#fff; }
header p { margin:0; color:#D6DAEA; font-size:15px; max-width:52ch; }
main { max-width:760px; margin:0 auto; padding:0 16px 80px; }
.buscador { margin:22px 0 10px; }
.buscador input { width:100%; padding:13px 15px; font-size:16px; border-radius:10px;
       border:1px solid var(--line); background:var(--soft); color:var(--ink); }
.buscador input:focus { outline:2px solid var(--teal); outline-offset:1px; }
h2.sec { font-size:13px; letter-spacing:.14em; text-transform:uppercase; color:var(--muted);
       margin:30px 0 12px; font-weight:600; }
.receta { border:1px solid var(--line); border-radius:12px; margin:0 0 12px;
          background:var(--paper); overflow:hidden; }
.receta > summary { cursor:pointer; padding:16px 18px; list-style:none; }
.receta > summary::-webkit-details-marker { display:none; }
.receta h3 { margin:0; font-size:19px; color:var(--navy); font-weight:600; }
.receta .resumen { margin:4px 0 0; color:var(--muted); font-size:14px; }
.cuerpo { padding:0 18px 18px; border-top:1px solid var(--line); margin-top:14px; }
.cuerpo h3 { font-size:13px; letter-spacing:.1em; text-transform:uppercase;
             color:var(--green); margin:18px 0 8px; }
.cuerpo p { margin:0 0 10px; }
.cuerpo ul, .cuerpo ol { margin:0 0 12px; padding-left:22px; }
.cuerpo li { margin:0 0 6px; }
footer { border-top:1px solid var(--line); margin-top:40px; padding-top:18px;
         color:var(--muted); font-size:13px; }
.vacio { color:var(--muted); padding:18px 2px; display:none; }
"""

JS = """
const caja = document.getElementById('q');
const fichas = [...document.querySelectorAll('.receta')];
const vacio = document.querySelector('.vacio');
caja.addEventListener('input', () => {
  const t = caja.value.trim().toLowerCase();
  let vistas = 0;
  fichas.forEach(f => {
    const hay = !t || f.textContent.toLowerCase().includes(t);
    f.style.display = hay ? '' : 'none';
    if (hay) vistas++;
    if (t && hay) f.open = true;
    if (!t) f.open = false;
  });
  document.querySelectorAll('h2.sec').forEach(h => {
    let n = 0, s = h.nextElementSibling;
    while (s && s.tagName !== 'H2') { if (s.style.display !== 'none') n++; s = s.nextElementSibling; }
    h.style.display = n ? '' : 'none';
  });
  vacio.style.display = vistas ? 'none' : 'block';
});
"""


def main():
    secciones = leer()
    total = sum(len(f) for _, f in secciones)
    partes = ["<!doctype html><html lang='es'><head><meta charset='utf-8'>",
              "<meta name='viewport' content='width=device-width, initial-scale=1'>",
              "<title>Recetario de Los Reales</title>",
              "<meta name='description' content='Las recetas de la casa, en un solo lugar.'>",
              f"<style>{CSS}</style></head><body>",
              "<header><div class='wrap'><div class='eyebrow'>Los Reales</div>",
              "<h1>Recetario de la casa</h1>",
              "<p>Las recetas que vamos juntando. Se abre cada una para ver ingredientes y "
              "preparación, y el buscador encuentra por ingrediente.</p></div></header><main>",
              "<div class='buscador'><input id='q' type='search' "
              "placeholder='Buscar: plátano, limón, chocolate…' aria-label='Buscar receta'>"
              "</div><p class='vacio'>No hay ninguna receta con eso.</p>"]
    for nombre, fichas in secciones:
        partes.append(f"<h2 class='sec'>{html.escape(nombre)} · {len(fichas)}</h2>")
        for f in fichas:
            partes.append(
                f"<details class='receta' id='{f['id']}'><summary>"
                f"<h3>{html.escape(f['titulo'])}</h3>"
                f"<p class='resumen'>{html.escape(f['resumen'])}</p></summary>"
                f"<div class='cuerpo'>{f['html']}</div></details>")
    partes.append(f"<footer>{total} recetas · Se actualiza desde el repositorio de GitHub."
                  "</footer></main>")
    partes.append(f"<script>{JS}</script></body></html>")
    salida = os.path.join(RAIZ, "index.html")
    open(salida, "w", encoding="utf-8").write("".join(partes))
    print(f"ok -> index.html ({total} recetas en {len(secciones)} sección/es)")


if __name__ == "__main__":
    main()
