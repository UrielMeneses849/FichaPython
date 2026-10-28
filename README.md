# Fichas de Mensajero

Genera fichas Construleads y Explorer desde XML/JSON, utilizando **el mismo
exportador vectorial de Descargar ficha en construleads-web**. Comparte el
formato de página de la plataforma (842 × 1191 puntos), fuentes Poppins,
logo, medidas, colores, tarjetas, fechas, avance, contactos y paginación.
No se imprime una recreación CSS ni se descarga una fuente desde Google.

## Preparar y ejecutar

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
PLAYWRIGHT_BROWSERS_PATH=ms-playwright .venv/bin/python -m playwright install chromium
```

Mensajero entrega un archivo por lote. Puede mezclar ambas fuentes:

```bash
.venv/bin/python app.py --datos examples/fichas-mixtas.json
.venv/bin/python app.py --datos entrada.xml --output-dir salida
.venv/bin/python app.py OC335798,EX000233 --datos entrada.json
```

En Windows, usar `.venv\Scripts\python.exe`; para instalar Chromium definir
`PLAYWRIGHT_BROWSERS_PATH=ms-playwright` en el entorno antes del comando.
El ejecutable empaquetado usa los mismos argumentos:

```text
ficha-renderer.exe --datos C:\Mensajero\entrada.json --output-dir C:\Mensajero\salida
```

La interfaz histórica sigue aceptando varias claves Construleads:

```text
ficha-renderer.exe OC335798 OC332105
ficha-renderer.exe OC335798,OC332105
```

Ambos comandos crean un PDF independiente por clave en `output/pdf/`.
Para mezclar ambas fuentes, `ficha-renderer.exe --datos entrada.json`
procesa todas las fichas del lote; indicar claves además de `--datos`
selecciona cuáles procesar. La combinación en un solo PDF sigue siendo
una operación separada con `pdf-merger.exe`.

Por cada clave se escriben `salida/pdf/CLAVE.pdf`, metadatos de caché y un HTML
autocontenido en `salida/html/CLAVE.html`. El HTML muestra el mismo PDF; no
mantiene una segunda maquetación que pueda desalinearse. Las rutas de salida
son relativas al directorio de ejecución; los recursos del motor siempre
se resuelven desde la instalación, también con PyInstaller.

## Contrato XML/JSON

JSON acepta una ficha, un array o un contenedor `fichas`, `obras`, `OBRAS`,
`datos` o `data`. XML acepta elementos `OBRAS`/`datos`, namespaces, atributos
o elementos, y respuestas ASMX con XML escapado. Los nombres de los campos
son los mismos que en la plataforma. También acepta objetos ya normalizados
como los que consume `generarFichaPdf`.

- Identificador obligatorio: `Clave_Proyecto` o `proy_clave`.
- Fuente: `Origen`/`origen` = `construleads` o `explorer` (`explora` es alias).
  Si falta, una clave `EX...` o una imagen Explorer identifica Explorer.
  `--origen explorer` permite explicitar la fuente de un archivo completo.
- Nombre, publicación, fechas: `Proyecto`, `Fecha_Publicacion`, `Fecha_Inicio`,
  `Fecha_Terminacion` (o sus campos `proy_*` históricos).
- Detalles: `Tipo_Proyecto`, `Etapa`, `Genero`, `Subgenero`, `Estado_Proyecto`,
  `Municipio_Proyecto`, `Localizacion1`, `Inversion`, `Sup_Construida`, `Sector`,
  `Tipo_Obra`, `Tipo_Desarrollo`, `PorcentajeAvance`.
- Construleads: `CIAS/CIA/CONTACTOS/CONTACTO` del XML histórico o
  `cias_normalizadas` del JSON, incluyendo todos los teléfonos/contactos.
- Explorer: `Latitud`, `Longitud`, `Impo_Image_Url` (también `impo_image_url`
  o `imagen_explorer`), y `Fecha_Imagen`. La fecha de imagen no se sustituye
  por la publicación si está ausente. Se muestra `No disponible`, como la web.
- La imagen puede ser una URL HTTP(S), un archivo PNG/JPEG relativo al archivo
  de entrada, una ruta absoluta o un data URI base64. Sin imagen se muestra
  `Sin imagen disponible.`; si se indicó una imagen y falla, la ficha falla.
  Con `URL_Ficha` puede recuperarse el JPEG satelital del PDF del servicio,
  igual que en la web. Con imágenes remotas se necesita acceso de red.
- Información adicional: `Descripcion`/`proy_descripcionlarga`, `acabados`,
  `observaciones`, `descripcionextra`, `caracteristicas`, `actualizacion`,
  `concurso`. Los campos vacíos y el avance desconocido siguen las mismas
  reglas de la plataforma. No se inventan ni se recalculan datos ausentes.

La consulta histórica sigue funcionando con `app.py OC335798` y permite
sobrescribir su token existente mediante `BIMSA_TOKEN`. Ese servicio no
entrega Explorer y omite algunos campos modernos, como el porcentaje de
avance. Para obtener los mismos datos que en la plataforma, Mensajero debe
entregar el XML/JSON de su contrato actual; la maquetación es común.

Claves duplicadas, faltantes o inválidas y XML/JSON mal formado producen
código de salida distinto de cero. Un fallo de una ficha no detiene las demás;
`PDFS GENERADOS:` enumera sólo las rutas disponibles. Un lote parcialmente
fallido también termina con código 1 para que Mensajero pueda detectarlo.

La caché valida contenido del PDF, entrada y versión del motor. Los PDFs de
la plantilla antigua se regeneran. `--forzar` omite la caché. Fichas con una
imagen declarada se regeneran siempre para evitar reutilizar una captura
que haya cambiado conservando la misma URL/ruta.

## Sincronizar con la web

```bash
.venv/bin/python scripts/sync_web_renderer.py ../construleads-web
```

El script importa los tres módulos originales, bibliotecas y recursos de
marca desde un checkout con sus dependencias instaladas. Guarda sus SHA-256
en `assets/web/manifest.json` y crea un adaptador de navegador sin cambiar
las funciones de maquetación. Node/npm no son necesarios al ejecutar el ETL.
Versionar juntos los recursos importados. El workflow Windows ya incluye
la carpeta `assets` en el ejecutable.

## Comprobaciones

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/verify_web_parity.py --web ../construleads-web --datos examples/fichas-mixtas.json
```

La segunda comprobación requiere Node y el checkout web con dependencias.
Genera ambos PDFs con datos y fecha iguales y compara tamaño, número de
páginas, instrucciones vectoriales y texto de todas las páginas. La
ejecución normal y el EXE no dependen de Node ni del checkout web.

Al subir a `main`, GitHub Actions construye `ficha-renderer.exe` y
`pdf-merger.exe`. Antes de publicar el artefacto `BIMSA_FichaTecnica_EXE`,
ejecuta las pruebas de contrato y ambos ejecutables en Windows desde una
carpeta temporal, sin depender del Chromium del checkout. Verifica el lote
mixto, acentos UTF-8, fuentes, una imagen embebida y la combinación de PDFs.
