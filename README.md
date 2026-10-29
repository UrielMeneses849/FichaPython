# Fichas de Mensajero

El ejecutable recibe únicamente las claves de los proyectos, consulta su XML
en el mismo WS que la plataforma y genera un PDF independiente por clave.
No se necesita preparar JSON, XML ni otros archivos de entrada.

```bat
ficha-renderer.exe OC335798,EX001065
```

También admite espacios o una mezcla de ambos separadores:

```bat
ficha-renderer.exe OC335798 EX001065 OC332105
```

Procesa las claves una por una, en el orden indicado, y produce:

```text
output/pdf/OC335798.pdf
output/pdf/EX001065.pdf
output/pdf/OC332105.pdf
```

Las claves repetidas se procesan una sola vez. Si una consulta falla,
continúa con las demás y termina con código 1 para señalar el fallo parcial.

## Consulta del XML

Utiliza `https://www.construleads.com/ws_new_cl/ws_cl.asmx`:

- Claves `EX...`: `ws_cl_sobrasficha_explorer`.
- Las demás claves Construleads: `ws_cl_sobrasficha`.

Se envía `sClave_obras` y el token de aplicación del servicio; los campos
`sId_usuario` y `sId_session` se envían vacíos. Ambas consultas se verificaron
contra el WS real con `OC335798` y `EX001065`, sin sesión de navegador.
El XML actual incluye los campos de avance e imagen que faltaban en el
servicio histórico. Las imágenes Explorer se descargan desde la URL del XML.
No se inventan valores faltantes ni se toma la publicación como fecha de imagen.

Se necesita conexión al WS y al servidor de imágenes. La configuración
predeterminada está incluida en el EXE. Las variables `BIMSA_TOKEN` y
`BIMSA_WS_BASE_URL` permiten sustituir la configuración del servicio; no son
necesarias para la ejecución normal. `--origen explorer`/`construleads`
permite explicitar la fuente de un lote si sus claves no siguen el prefijo.

## Opciones y combinación

```bat
ficha-renderer.exe OC335798,EX001065 --output-dir C:\Mensajero\salida
ficha-renderer.exe OC335798,EX001065 --forzar
pdf-merger.exe --usuario 123 --claves OC335798,EX001065 --input-dir output/pdf --output-dir output/combinados
```

El combinador genera `Reporte_Obras_123.pdf` en el directorio indicado.
La combinación es una operación separada; el generador conserva las fichas
individuales. Cada ficha también deja una vista HTML y metadatos de caché
generados automáticamente. La caché valida entrada, versión y contenido;
una imagen declarada se vuelve a consultar para no reutilizar una captura vieja.

## Desarrollo y compilación

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
PLAYWRIGHT_BROWSERS_PATH=ms-playwright .venv/bin/python -m playwright install chromium
.venv/bin/python app.py OC335798,EX001065
.venv/bin/python -m unittest discover -s tests -v
```

En Windows, usar `.venv\Scripts\python.exe` y definir la variable
`PLAYWRIGHT_BROWSERS_PATH=ms-playwright` antes de instalar Chromium.

Al subir a `main`, Actions construye ambos EXE y los ejecuta en Windows.
La prueba invoca el renderer con dos claves desde una carpeta vacía y un
WS XML controlado, comprueba la ruta de consulta de cada fuente, acentos,
imagen embebida y combinación, sin archivos de datos ni conexión a producción.
Sólo publica el artefacto `BIMSA_FichaTecnica_EXE` si todo termina correctamente.

## Maquetación

Se usa el mismo exportador vectorial de Descargar ficha en la plataforma:
842 × 1191 puntos, Poppins, logo, colores, tarjetas, formatos y paginación.
Los recursos están incluidos en el EXE; no necesita Node ni Google Fonts.
Para actualizar el exportador desde el checkout web con dependencias:

```bash
.venv/bin/python scripts/sync_web_renderer.py ../construleads-web
```

Las utilidades de paridad y normalización de archivos de `scripts/` son
herramientas de QA; no forman parte de la llamada de producción de Mensajero.
