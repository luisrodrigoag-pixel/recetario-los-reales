#!/usr/bin/env python3
"""Dibuja a Tito en vectores, a partir de su foto.

Tito es el perro de la casa: volpino italiano, pelo largo color canela, hocico con antifaz
más oscuro, pecho y patas color crema, cola en pompón sobre el lomo, pechera rosa con gris.
Esto no es una foto convertida: es una ilustración hecha a mano con las proporciones y los
colores sacados de `Foto Tito 2026-09-10.jpg`.

El pelo esponjado se calcula —una circunferencia a la que se le mueve el radio en ondas—
porque a mano quedan picos irregulares y se ve sucio.

Uso:  python3 -I dibujar_tito.py        -> assets/tito.svg y assets/tito-cara.svg
"""
import math
import os

RAIZ = os.path.dirname(os.path.abspath(__file__))

CANELA = "#C87B3C"       # el cuerpo
CANELA_CLARO = "#DFA163"  # melena y lomo donde pega la luz
CREMA = "#F0D9B5"        # hocico, pecho, patas, cola
MARRON = "#95602F"       # sombras y el antifaz del hocico
NEGRO = "#241C16"
ROSA = "#E4636F"         # la pechera
GRIS = "#5F6B7A"


def pelo(cx, cy, r, picos, hondo, giro=0.0, pasos=360):
    """Circunferencia con el radio ondulado: el pelo largo visto de lejos."""
    d = []
    for i in range(pasos + 1):
        a = 2 * math.pi * i / pasos
        rr = r + hondo * math.sin(picos * a + giro)
        x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
        d.append(("M" if i == 0 else "L") + f"{x:.1f},{y:.1f}")
    return " ".join(d) + " Z"


def cuerpo_entero():
    p = []
    p.append("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 240 230' "
             "role='img' aria-label='Tito, el perro de la casa'>")

    # Cola: pompón echado sobre el lomo, que es lo primero que se le reconoce.
    p.append(f"<path d='{pelo(66, 112, 30, 15, 2.4, 0.5)}' fill='{CREMA}'/>")
    p.append(f"<path d='{pelo(66, 112, 20, 13, 2.0, 1.2)}' fill='#FFFFFF' opacity='.45'/>")

    # Cuerpo
    p.append(f"<path d='{pelo(120, 150, 52, 22, 2.2, 0.3)}' fill='{CANELA}'/>")
    p.append("<ellipse cx='120' cy='140' rx='44' ry='36' fill='%s'/>" % CANELA_CLARO)

    # Patas delanteras
    for x in (104, 140):
        p.append(f"<rect x='{x}' y='172' width='20' height='34' rx='10' fill='{CREMA}'/>")
    # Pata trasera que asoma
    p.append(f"<ellipse cx='80' cy='190' rx='15' ry='11' fill='{CREMA}'/>")

    # Melena del cuello, más clara: el collar de pelo del volpino
    p.append(f"<path d='{pelo(134, 112, 40, 20, 2.6, 0.9)}' fill='{CREMA}'/>")

    # Pechera rosa con la hebilla gris, cruzando el pecho por debajo de la melena
    p.append(f"<path d='M100 146 q22 12 46 2 l5 17 q-24 11 -47 -1 Z' fill='{ROSA}'/>")
    p.append(f"<path d='M100 146 q22 12 46 2' fill='none' stroke='{GRIS}' "
             "stroke-width='5' stroke-linecap='round'/>")
    p.append(f"<rect x='114' y='152' width='17' height='13' rx='3' fill='{GRIS}'/>")

    # Cabeza
    p.append(f"<path d='{pelo(140, 82, 45, 22, 2.4, 0.2)}' fill='{CANELA_CLARO}'/>")

    # Orejas triangulares, pequeñas y paradas
    p.append(f"<path d='M112 56 L116 24 L140 50 Z' fill='{CANELA}'/>")
    p.append(f"<path d='M118 52 L121 33 L133 49 Z' fill='{MARRON}'/>")
    p.append(f"<path d='M166 52 L177 26 L184 58 Z' fill='{CANELA}'/>")
    p.append(f"<path d='M169 52 L176 35 L180 54 Z' fill='{MARRON}'/>")

    # Cara: frente canela y el morro crema
    p.append(f"<ellipse cx='142' cy='84' rx='40' ry='36' fill='{CANELA}'/>")
    p.append(f"<ellipse cx='146' cy='98' rx='26' ry='21' fill='{CREMA}'/>")
    # El antifaz: la zona oscura alrededor del hocico
    p.append(f"<ellipse cx='150' cy='94' rx='17' ry='13' fill='{MARRON}' opacity='.55'/>")

    # Ojos
    for x in (131, 165):
        p.append(f"<ellipse cx='{x}' cy='79' rx='7.5' ry='8.5' fill='{NEGRO}'/>")
        p.append(f"<circle cx='{x + 2.5}' cy='76' r='2.4' fill='#FFFFFF' opacity='.9'/>")

    # Nariz y boca
    p.append(f"<path d='M150 92 q8 0 8 5 q0 5 -8 5 q-8 0 -8 -5 q0 -5 8 -5 Z' fill='{NEGRO}'/>")
    p.append(f"<path d='M150 102 v4 M150 106 q-7 6 -13 1 M150 106 q7 6 13 1' fill='none' "
             f"stroke='{NEGRO}' stroke-width='2.4' stroke-linecap='round'/>")
    p.append("</svg>")
    return "".join(p)


def solo_cara():
    """La carita sola, para el ícono y la pestaña del navegador."""
    p = ["<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 120' "
         "role='img' aria-label='Tito'>",
         f"<path d='{pelo(60, 64, 46, 22, 2.4, 0.2)}' fill='{CREMA}'/>",
         f"<path d='M28 38 L34 10 L56 34 Z' fill='{CANELA}'/>",
         f"<path d='M34 35 L37 19 L50 34 Z' fill='{MARRON}'/>",
         f"<path d='M86 36 L96 10 L104 42 Z' fill='{CANELA}'/>",
         f"<path d='M88 36 L95 20 L99 39 Z' fill='{MARRON}'/>",
         f"<ellipse cx='60' cy='64' rx='40' ry='37' fill='{CANELA_CLARO}'/>",
         f"<ellipse cx='60' cy='60' rx='34' ry='30' fill='{CANELA}'/>",
         f"<ellipse cx='60' cy='80' rx='24' ry='19' fill='{CREMA}'/>",
         f"<ellipse cx='60' cy='77' rx='16' ry='12' fill='{MARRON}' opacity='.5'/>"]
    for x in (45, 75):
        p.append(f"<ellipse cx='{x}' cy='58' rx='7' ry='8' fill='{NEGRO}'/>")
        p.append(f"<circle cx='{x + 2.4}' cy='55' r='2.3' fill='#FFFFFF' opacity='.9'/>")
    p.append(f"<path d='M60 74 q8 0 8 5 q0 5 -8 5 q-8 0 -8 -5 q0 -5 8 -5 Z' fill='{NEGRO}'/>")
    p.append(f"<path d='M60 84 v4 M60 88 q-7 6 -13 1 M60 88 q7 6 13 1' fill='none' "
             f"stroke='{NEGRO}' stroke-width='2.4' stroke-linecap='round'/>")
    p.append("</svg>")
    return "".join(p)


def main():
    destino = os.path.join(RAIZ, "assets")
    os.makedirs(destino, exist_ok=True)
    for nombre, svg in (("tito.svg", cuerpo_entero()), ("tito-cara.svg", solo_cara())):
        open(os.path.join(destino, nombre), "w", encoding="utf-8").write(svg)
        print("ok ->", os.path.join("assets", nombre))


if __name__ == "__main__":
    main()
