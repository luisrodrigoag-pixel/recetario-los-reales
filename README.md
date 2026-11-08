# Recetario de Los Reales

Las recetas de la casa, en un solo lugar.

👉 **Para cocinar, abre la página: https://luisrodrigoag-pixel.github.io/recetario-los-reales/**
Se ve bien en el celular, cada receta se despliega y el buscador encuentra por ingrediente.

Este repositorio es el otro lado: aquí viven las recetas en texto, una por archivo, para
poder corregirlas y agregar más sin pelearse con ningún programa.

## Qué hay

| | |
| --- | --- |
| [Desayunos](recetas/desayunos) | 3 |
| [De diario](recetas/diario) | 12 — pollo, pescado, res, albóndigas, milanesas y el arroz rojo |
| [Sopas y caldos](recetas/sopas) | 2 |
| [Verduras y ensaladas](recetas/casa) | 12 vegetarianas |
| [Postres y antojos](recetas/postres) | 3 |
| [Con aceite MCT](recetas/mct) | 9, empezando por cómo se usa el aceite |
| [Dónde comer](lugares) | 81 lugares de la lista de Robin Food, por ciudad |

Cada receta trae su estimado por porción y qué tan laboriosa es. El orden de las secciones lo
fija el diccionario `SECCIONES` de `construir.py`; una carpeta que no esté ahí sale al final
con su propio nombre, así que agregar una sección nunca rompe la página.

La página tiene tres pestañas:

- **Recetas.** Cada una con su etiqueta de qué tan laboriosa es, cuánto trabajo activo pide y
  las calorías por porción.
- **Mi lista.** Se marcan las recetas con el botón **+** y se arma la lista del súper, agrupada
  en las mismas categorías de las listas de los lunes (proteínas, cereales, frutas, lácteos,
  grasas, verduras y despensa), diciendo de qué receta sale cada cosa. Se va tachando en el
  súper y se guarda en ese teléfono. **No se suman cantidades de recetas distintas** —media
  taza de una y dos cucharadas de otra no se pueden sumar sin inventar—, así que cada renglón
  conserva su medida.
- **Dónde comer.** Los lugares por ciudad, cada uno con su enlace a Google Maps, y un
  formulario para agregar uno nuevo: se escribe el nombre, se busca solo en el mapa abierto
  para traer la dirección y queda guardado en el teléfono hasta que se lo manden a Lulu, que
  lo verifica y lo sube a la lista de todos.

## Cómo se agrega una receta

1. Un archivo nuevo en `recetas/<sección>/NN-nombre-de-la-receta.md`.
2. Se escribe con esta forma, que es la que entiende la página:

```markdown
# Nombre de la receta

Una línea diciendo qué es o cuándo se come. Esta línea sale en el índice.

**Rinde:** 4 porciones · **Tiempo:** 20 minutos

## Ingredientes
- 2 tazas de algo
- 1 cucharada de otra cosa

## Cómo se hace
1. Primer paso.
2. Segundo paso.

## Notas
Lo que uno aprende haciéndola: el truco, el error común, qué se puede cambiar.
```

3. Se vuelve a armar la página:

```bash
python3 -I construir.py
```

4. Se sube el cambio y la página se actualiza sola en unos minutos.

Para abrir una sección nueva —postres, sopas, lo que sea— basta con crear la carpeta dentro
de `recetas/` y ponerle su nombre bonito en el diccionario `SECCIONES` de `construir.py`.

## Las notas importan

La parte de **Notas** es la que hace que una receta sirva la segunda vez: por qué el plátano
va bien maduro, por qué el agua del hummus va fría, por qué el aceite entra antes que el
jitomate. Si al cocinar descubren algo, vale la pena anotarlo ahí.

## Dónde comer

La pestaña de lugares sale de `lugares/<ciudad>.md`, con esta forma:

```markdown
# Puebla

## 🌮 Tacos y antojitos
- Nombre del lugar — dirección
```

Es la lista de Robin Food que Luis Ro tiene en sus notas. Si se agrega un lugar ahí, hay que
agregarlo aquí también (o pedírmelo y yo lo paso).

## Tito

El dibujo del encabezado es Tito, el perro de la casa, ilustrado en vectores a partir de su
foto con `dibujar_tito.py`. No es una foto convertida: son formas dibujadas a mano, con sus
colores y sus proporciones —volpino canela, melena crema, orejas paradas, cola en pompón y su
pechera rosa—. Para cambiarlo, se edita ese script y se vuelve a correr:

```bash
python3 -I dibujar_tito.py && python3 -I construir.py
```

## Como app en el teléfono

Al abrir el enlace en el iPhone, *Compartir › Agregar a pantalla de inicio*: queda con el logo
y abre sin la barra del navegador, como una app. Eso lo dan `manifest.webmanifest` y las metas
que escribe `construir.py`.

**⚠️ iOS no acepta SVG en `apple-touch-icon`.** Por eso el logo se genera también en PNG:
`dibujar_logo.py` dibuja el SVG —Tito con gorro de chef sobre el azulejo de talavera— y lo
rasteriza con Chrome a 180, 192 y 512 px. Si se cambia el logo:

```bash
python3 -I dibujar_logo.py && python3 -I construir.py
```
