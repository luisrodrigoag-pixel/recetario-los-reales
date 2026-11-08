#!/usr/bin/env python3
"""El logo del recetario: Tito con gorro de chef sobre el azulejo de talavera.

Por qué existe: Luis Ro pidió un logo para cuando la página se guarde en la pantalla de
inicio del iPhone. **iOS no acepta SVG en `apple-touch-icon`**, así que no basta con la
carita que ya teníamos: hace falta un PNG cuadrado, y de varios tamaños para que no se vea
pixeleado ni en el teléfono ni en el escritorio.

El azulejo es el mismo que la cabecera de la página, pero dibujado aquí en SVG para que el
ícono no dependa del CSS.

Uso:  python3 -I dibujar_logo.py      -> assets/logo.svg y los PNG (180, 192, 512)
      Necesita Chrome para los PNG; si no está, deja el SVG y avisa.
"""
import os
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.abspath(__file__))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

TALAVERA = "#2B4C8C"
CREMA = "#FFF8EC"
CANELA = "#C87B3C"
CANELA_CLARO = "#DFA163"
PELO = "#F0D9B5"
MARRON = "#95602F"
NEGRO = "#241C16"
TERRACOTA = "#C4572F"


def azulejo(paso=64):
    """El fondo: rombos y puntos, como la cabecera."""
    d = [f"<rect width='512' height='512' fill='{TALAVERA}'/>"]
    for y in range(0, 512 + paso, paso):
        for x in range(0, 512 + paso, paso):
            d.append(f"<circle cx='{x}' cy='{y}' r='7' fill='{CREMA}' opacity='.16'/>")
            d.append(f"<path d='M{x} {y - paso / 2} L{x + paso / 2} {y} L{x} {y + paso / 2} "
                     f"L{x - paso / 2} {y} Z' fill='none' stroke='{CREMA}' "
                     "stroke-width='2' opacity='.13'/>")
    return "".join(d)


def logo():
    p = ["<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 512 512' "
         "role='img' aria-label='Recetario de Los Reales'>", azulejo()]

    # Un plato crema detrás, que separa a Tito del azulejo y le da forma de logo.
    p.append(f"<circle cx='256' cy='268' r='172' fill='{CREMA}' opacity='.14'/>")
    p.append(f"<circle cx='256' cy='268' r='150' fill='{CREMA}'/>")
    p.append(f"<circle cx='256' cy='268' r='150' fill='none' stroke='{TERRACOTA}' "
             "stroke-width='7' opacity='.85'/>")

    # Orejas (van detrás de la cabeza)
    p.append(f"<path d='M150 214 L146 118 L236 186 Z' fill='{CANELA}'/>")
    p.append(f"<path d='M168 200 L166 146 L220 188 Z' fill='{MARRON}'/>")
    p.append(f"<path d='M352 190 L388 108 L400 214 Z' fill='{CANELA}'/>")
    p.append(f"<path d='M362 192 L384 140 L392 200 Z' fill='{MARRON}'/>")

    # Melena y cabeza
    p.append(f"<circle cx='256' cy='288' r='132' fill='{PELO}'/>")
    p.append(f"<circle cx='256' cy='288' r='112' fill='{CANELA_CLARO}'/>")
    p.append(f"<circle cx='256' cy='282' r='98' fill='{CANELA}'/>")
    p.append(f"<ellipse cx='256' cy='336' rx='66' ry='52' fill='{PELO}'/>")
    p.append(f"<ellipse cx='256' cy='328' rx='44' ry='33' fill='{MARRON}' opacity='.45'/>")

    # Ojos
    for x in (214, 298):
        p.append(f"<ellipse cx='{x}' cy='274' rx='19' ry='22' fill='{NEGRO}'/>")
        p.append(f"<circle cx='{x + 7}' cy='266' r='6.5' fill='#FFFFFF' opacity='.92'/>")

    # Nariz y boca
    p.append(f"<path d='M256 318 q22 0 22 14 q0 14 -22 14 q-22 0 -22 -14 q0 -14 22 -14 Z' "
             f"fill='{NEGRO}'/>")
    p.append(f"<path d='M256 346 v10 M256 356 q-19 16 -34 3 M256 356 q19 16 34 3' fill='none' "
             f"stroke='{NEGRO}' stroke-width='7' stroke-linecap='round'/>")

    # Gorro de chef: la banda y el fuelle
    p.append(f"<path d='M198 164 h116 v34 a12 12 0 0 1 -12 12 h-92 a12 12 0 0 1 -12 -12 Z' "
             f"fill='{CREMA}'/>")
    p.append(f"<path d='M198 164 h116' stroke='{TERRACOTA}' stroke-width='6' "
             "stroke-linecap='round'/>")
    p.append(f"<path d='M206 164 q-30 -7 -25 -38 q5 -30 39 -25 q9 -32 36 -32 q27 0 36 32 "
             f"q34 -5 39 25 q5 31 -25 38 Z' fill='{CREMA}'/>")
    p.append("</svg>")
    return "".join(p)


def a_png(svg_path, destino, lado):
    """Chrome rasteriza el SVG al tamaño exacto; sin dependencias de imagen en Python."""
    html = (f"<!doctype html><meta charset='utf-8'>"
            f"<body style='margin:0'><img src='file://{svg_path}' "
            f"style='width:{lado}px;height:{lado}px;display:block'></body>")
    with tempfile.TemporaryDirectory() as tmp:
        pagina = os.path.join(tmp, "p.html")
        open(pagina, "w", encoding="utf-8").write(html)
        r = subprocess.run(
            [CHROME, "--headless", "--disable-gpu", "--no-first-run",
             f"--user-data-dir={os.path.join(tmp, 'perfil')}",
             f"--screenshot={destino}", f"--window-size={lado},{lado}",
             "--default-background-color=00000000", "--hide-scrollbars",
             "--virtual-time-budget=4000", "file://" + pagina],
            capture_output=True, text=True, timeout=120)
        if not os.path.exists(destino):
            sys.exit(f"Chrome no generó {destino}: {r.stderr[-300:]}")


def main():
    destino = os.path.join(RAIZ, "assets")
    os.makedirs(destino, exist_ok=True)
    svg = os.path.join(destino, "logo.svg")
    open(svg, "w", encoding="utf-8").write(logo())
    print("ok -> assets/logo.svg")
    if not os.path.exists(CHROME):
        print("⚠️ sin Chrome: no se generaron los PNG (iOS los necesita)")
        return
    for lado in (180, 192, 512):
        png = os.path.join(destino, f"logo-{lado}.png")
        a_png(svg, png, lado)
        print(f"ok -> assets/logo-{lado}.png ({os.path.getsize(png) // 1024} KB)")


if __name__ == "__main__":
    main()
