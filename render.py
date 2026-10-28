"""Ejecuta el mismo exportador vectorial de la plataforma dentro de Chromium."""
import base64
import asyncio
import hashlib
import io
import json
import os
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests
from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.async_api import async_playwright
from PyPDF2 import PdfReader

from parser import obtener_obra, validar_clave

ASSET_ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
WEB_ROOT = ASSET_ROOT / "assets" / "web"


def get_playwright_path():
    return os.environ.get("PLAYWRIGHT_BROWSERS_PATH", str(ASSET_ROOT / "ms-playwright"))


def firma_render():
    digest = hashlib.sha256()
    digest.update(b"mensajero-web-vector-v1")
    for path in [ASSET_ROOT / "template.html", ASSET_ROOT / "render.py", ASSET_ROOT / "parser.py",
                 *sorted(WEB_ROOT.glob("*"))]:
        if path.is_file():
            digest.update(path.name.encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def leer_recurso(location, base_dir):
    if location.startswith("data:"):
        header, value = location.split(",", 1)
        return base64.b64decode(value, validate=True) if ";base64" in header else unquote(value).encode("latin1")
    parsed = urlparse(location)
    if parsed.scheme in ("http", "https"):
        with requests.get(location, timeout=(15, 60), stream=True) as response:
            response.raise_for_status()
            content = bytearray()
            for chunk in response.iter_content(65536):
                content.extend(chunk)
                if len(content) > 30 * 1024 * 1024:
                    raise ValueError("La imagen de la ficha excede 30 MB.")
            return bytes(content)
    if parsed.scheme == "file":
        return Path(unquote(parsed.path)).read_bytes()
    if parsed.scheme and len(parsed.scheme) != 1:
        raise ValueError(f"Protocolo de recurso no soportado: {parsed.scheme}")
    path = Path(location)
    return (path if path.is_absolute() else base_dir / path).read_bytes()


def imagen_satelital(obra, base_dir):
    location = str(obra.get("imagen_explorer") or "").strip()
    if not location:
        return None
    try:
        content = leer_recurso(location, base_dir)
        if content.startswith((b"\x89PNG\r\n\x1a\n", b"\xff\xd8")):
            return content
        raise ValueError("La imagen satelital debe ser PNG o JPEG.")
    except (requests.RequestException, OSError, ValueError) as error:
        if not obra.get("urlFicha"):
            raise ValueError(f"No fue posible incluir la imagen de {obra['proy_clave']}: {error}") from error
        reader = PdfReader(io.BytesIO(leer_recurso(str(obra["urlFicha"]), base_dir)))
        images = []
        for page in reader.pages:
            resources = page["/Resources"].get_object()
            xobjects = resources.get("/XObject")
            if not xobjects:
                continue
            for ref in xobjects.get_object().values():
                image = ref.get_object()
                if (image.get("/Subtype") == "/Image" and image.get("/Filter") == "/DCTDecode"
                        and image.get("/Width", 0) >= 300 and image.get("/Height", 0) >= 200):
                    images.append((image["/Width"] * image["/Height"], image.get_data()))
        if not images:
            raise ValueError("El PDF del servicio no contiene una imagen satelital válida.") from error
        return max(images, key=lambda item: item[0])[1]


def crear_html(obra, base_dir, generated_at=None):
    resources = {name: base64.b64encode((WEB_ROOT / file).read_bytes()).decode() for name, file in {
        "regularBytes": "poppins-latin-400-normal.woff",
        "mediumBytes": "poppins-latin-500-normal.woff",
        "semiBoldBytes": "poppins-latin-600-normal.woff",
    }.items()}
    resources["logoPng"] = "data:image/png;base64," + base64.b64encode((WEB_ROOT / "logo-construleads.png").read_bytes()).decode()
    satellite = imagen_satelital(obra, base_dir)
    if satellite:
        resources["satelliteBytes"] = base64.b64encode(satellite).decode()
    payload = json.dumps({"obra": obra, "resources": resources, "generatedAt": generated_at}, ensure_ascii=True)
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    env = Environment(loader=FileSystemLoader(ASSET_ROOT), autoescape=select_autoescape(["html"]))
    return env.get_template("template.html").render(
        clave=obra["proy_clave"], payload=payload,
        pdf_lib=(WEB_ROOT / "pdf-lib.min.js").read_text(encoding="utf-8"),
        fontkit=(WEB_ROOT / "fontkit.umd.min.js").read_text(encoding="utf-8"),
        engine=(WEB_ROOT / "engine.js").read_text(encoding="utf-8"),
    )


async def generar_pdf(clave, *, obra=None, output_dir="output", base_dir=None, generated_at=None):
    clave = validar_clave(clave)
    obra = obra if obra is not None else obtener_obra(clave)
    if obra["proy_clave"] != clave:
        raise ValueError(f"La ficha recibida no corresponde a {clave}.")
    output = Path(output_dir).resolve()
    html_path = output / "html" / f"{clave}.html"
    pdf_path = output / "pdf" / f"{clave}.pdf"
    html_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    html = crear_html(obra, Path(base_dir or Path.cwd()), generated_at)
    html_path.write_text(html, encoding="utf-8")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = get_playwright_path()
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        try:
            page = await browser.new_page(timezone_id="America/Mexico_City")
            await page.goto(html_path.as_uri(), wait_until="load")
            encoded = await asyncio.wait_for(page.evaluate("() => window.fichaBase64()"), timeout=120)
            content = base64.b64decode(encoded, validate=True)
            if not content.startswith(b"%PDF-"):
                raise ValueError("El exportador no devolvió un PDF válido.")
            temporary = pdf_path.with_suffix(".pdf.tmp")
            temporary.write_bytes(content)
            temporary.replace(pdf_path)
        finally:
            await browser.close()
    print(f"PDF generado: {pdf_path}")
    return str(pdf_path)
