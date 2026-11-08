# Recetario de Los Reales

Las recetas de la casa, en un solo lugar.

👉 **Para cocinar, abre la página: https://luisrodrigoag-pixel.github.io/recetario-los-reales/**
Se ve bien en el celular, cada receta se despliega y el buscador encuentra por ingrediente.

Este repositorio es el otro lado: aquí viven las recetas en texto, una por archivo, para
poder corregirlas y agregar más sin pelearse con ningún programa.

## Qué hay

| Sección | Recetas |
| --- | --- |
| [Con aceite MCT](recetas/mct) | 9 |

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
