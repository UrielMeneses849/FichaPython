# Verificación de fichas de Mensajero

final result: passed

## Referencias y alcance

- Objetivo: PDF exportado de la plataforma, correspondiente a las capturas
  del usuario. No se incluyen controles del modal ni del visor del navegador.
- Referencia real OC335798: `/Users/urielmeneses/Downloads/ficha-OC335798.pdf`.
- Exportador original: `../construleads-web/src/utils/fichaPdf.js`, ejecutado
  directamente con Node para producir las referencias adicionales.
- La entrada OC de QA combina el XML histórico con el nombre y avance 0
  verificados en el PDF actual del usuario. No se infieren esos valores en
  el ETL: Mensajero debe entregarlos en su XML/JSON actual.
- Explorer: datos e imagen de la ficha archivada
  `../construleads-web/tmp/pdfs/homologacion-EX000233.pdf`, normalizados como
  entrada y exportados con el motor actual. La fecha de imagen no estaba
  disponible; se comprueba que no se confunda con la publicación.
- Entrada local: `output/qa/entrada-paridad.json` (incluye el caso extenso).
- Estado: ficha clara, datos cargados, sin filtros ni interacciones de modal.

## Evidencias de comparación

PDF: 842 × 1191 puntos. Rasterización nativa PDFKit a 842 × 1191 píxeles,
misma escala en ambas columnas, sin marco del visor. Cada comparación tiene
1684 × 1191 píxeles: referencia izquierda, ETL derecha. No se comparan
densidades de pantalla diferentes ni capturas con barras del navegador.

- `output/qa/visual/comparacion-OC335798-1.png`
- `output/qa/visual/comparacion-OC335798-2.png`
- `output/qa/visual/comparacion-EX000233-1.png`
- `output/qa/paridad/parity.json`: 2 páginas OC, 1 Explorer y 10 del caso
  extenso, todas con instrucciones vectoriales y texto idénticos.
- Las 13 páginas también produjeron PNGs byte a byte idénticos al original
  al fijar la misma fecha de descarga. OC coincide con la descarga real
  del usuario, no sólo con una referencia creada para la prueba.

Se abrieron juntas las imágenes de ambas versiones para comprobar la
composición completa y los detalles legibles de cabecera, fechas, tarjetas,
contactos, bordes y fotografía. La identidad de los PNG de cada página
confirma también los detalles por debajo de la escala de visualización.

Archivos finales, con hora real de generación, renderizados y abiertos:
`output/qa/visual/final-OC335798-1.png`,
`output/qa/visual/final-OC335798-2.png`,
`output/qa/visual/final-EX000233-1.png`.
El texto coincide con el caso de paridad salvo la hora de descarga.

## Superficies revisadas

- Tipografía: mismos WOFF Poppins 400/500/600, tamaños, interlineados y saltos.
  Texto vectorial seleccionable, sin fuentes remotas ni fallback.
- Espaciado y composición: mismos puntos de página, márgenes, tarjetas,
  columnas, banda curva, contactos de dos columnas y continuaciones.
- Colores: mismos tokens del exportador original. El cambio azul solicitado
  para el mapa permanece limitado al mapa y no altera las fichas.
- Imágenes y marca: mismo PNG original de Construleads; JPEG satelital
  original, sin redibujar el logo ni sustituir imágenes por aproximaciones.
- Texto: formato de fechas es-MX, datos de ambas fuentes, avance 0/19,
  teléfonos/contactos completos, coordenadas, avisos y campos desconocidos.

## Hallazgos e historial

La plantilla anterior difería en logo, color, jerarquía, columnas de empresas,
fechas, avance y paginación. Se sustituyó la impresión CSS por el mismo
exportador vectorial y sus recursos originales. La primera comparación
visual posterior a esa sustitución pasó sin diferencias P0/P1/P2.

La herramienta de paridad necesitó una corrección para leer páginas con un
array de streams PDF. Fue una corrección del comprobador, no de maquetación.
Después se comprobaron las 13 páginas y las capturas finales.

Sin hallazgos visuales pendientes. La segunda página corta de OC335798 es
la paginación de la descarga original y se conserva deliberadamente.

## Validación funcional

- 8 pruebas de contrato XML/JSON, ambos orígenes, cero, aliases, namespaces,
  contactos múltiples, duplicados, clave inválida, datos externos en HTML,
  caché e imagen declarada pero inaccesible: pasan.
- Lote XML OC real y lote JSON mixto con imagen: generan los PDFs esperados.
- Lote parcial: ficha en caché disponible + clave ausente produce código 1,
  conserva la ficha válida y no hace una consulta de red para la clave ausente.
- SHA-256 de todos los módulos y recursos importados: verificados.
- `git diff --check`: sin errores.
- No se compiló ni ejecutó el EXE de Windows en esta máquina macOS.

## Mapa paralelo

- Inversión: `#006080`; Construleads: `#D95B27`; Explora: `#92979E`.
- 7 pruebas de clasificación/inventario, ESLint y diff-check pasan en el
  repositorio web. Se preservaron sus cambios previos.
- Evidencia de Chrome con pines individuales y leyenda:
  `output/qa/mapa-colores.png`.
- Se recargó la pestaña para descartar los SVG anteriores que Fast Refresh
  mantenía en memoria. Después se observaron los pines azules/naranjas/grises.
- Cambio local, sin despliegue.

## Comprobación completada

- [x] Reutilizar exportador y recursos de marca originales.
- [x] Recibir XML/JSON y generar ambas fuentes.
- [x] Comparar las mismas entradas, fecha, páginas, texto y vector.
- [x] Comparar rasterizados y revisar archivos finales.
- [x] Verificar mapa y sus colores en navegador.
