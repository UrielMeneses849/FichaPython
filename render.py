import asyncio
import os
import sys

from pathlib import Path
from playwright.async_api import async_playwright
from jinja2 import Environment, FileSystemLoader

from parser import obtener_obra

# =========================
# PLAYWRIGHT PATH
# =========================

def get_playwright_path():

    # =========================
    # EXE (PYINSTALLER)
    # =========================

    if getattr(sys, 'frozen', False):

        base_path = sys._MEIPASS

    else:

        base_path = os.getcwd()

    return os.path.join(
        base_path,
        "ms-playwright"
    )

# =========================
# HELPERS
# =========================

def extraer_texto(node, tag):

    value = node.findtext(tag)

    if value:
        return value

    return ""

# =========================
# RENDER
# =========================

async def generar_pdf(clave):

    obra_xml = obtener_obra(clave)

    # =========================
    # VALIDAR RESPUESTA WS
    # =========================

    if obra_xml is None:
        print(f"No se encontró información para la clave: {clave}")

        return None

    # =========================
    # COMPAÑIAS
    # =========================

    cias_normalizadas = []

    cias = obra_xml.findall(".//CIAS/CIA")

    for cia in cias:

        contactos = []

        contactos_xml = cia.findall(".//CONTACTOS/CONTACTO")

        for contacto in contactos_xml:

            nombre_completo = (
                (contacto.findtext("cont_nombre") or "") + " " +
                (contacto.findtext("cont_paterno") or "") + " " +
                (contacto.findtext("cont_materno") or "")
            )

            contactos.append({
                "puesto": contacto.findtext("cont_puesto") or "",
                "nombre": nombre_completo.strip(),
                "email": contacto.findtext("cont_email") or ""
            })

        cias_normalizadas.append({
            "nombre": cia.findtext("comp_razon_social") or "",
            "rol": cia.findtext("roco_descripcion") or "",
            "direccion": cia.findtext("sucu_calle") or "",

            "telefono1": cia.findtext("sucu_telefono1") or "",
            "telefono2": cia.findtext("sucu_telefono2") or "",
            "telefono3": cia.findtext("sucu_telefono3") or "",

            "contactos": contactos
        })

    # =========================
    # OBJETO
    # =========================

    obra = {

        "proy_clave":
            extraer_texto(obra_xml, "proy_clave"),

        "proy_nombre":
            extraer_texto(obra_xml, "proy_descripcioncorta"),

        "proy_fechacierre":
            extraer_texto(obra_xml, "proy_fechacierre"),

        "proy_tipoproyectodescripcion":
            extraer_texto(obra_xml, "proy_tipoproyectodescripcion"),

        "proy_fecha_inicio":
            extraer_texto(obra_xml, "proy_fechainicio"),

        "proy_fecha_fin":
            extraer_texto(obra_xml, "proy_fechatermino"),

        "proy_localizacion":
            extraer_texto(obra_xml, "proy_localizacion"),

        "proy_inversion":
            extraer_texto(obra_xml, "proy_inversion"),

        "proy_etapa":
            extraer_texto(obra_xml, "proy_etapa"),

        "esta_descripcion":
            extraer_texto(obra_xml, "esta_descripcion"),

        "muni_descripcion":
            extraer_texto(obra_xml, "muni_descripcion"),

        "sector":
            extraer_texto(obra_xml, "proy_sectordescripcion"),

        "tipo_obra":
            extraer_texto(obra_xml, "tiob_descripcion"),

        "subgenero":
            extraer_texto(obra_xml, "suge_descripcion"),

        "genero":
            extraer_texto(obra_xml, "gene_descripcion"),

        "desa_descripcion":
            extraer_texto(obra_xml, "desa_descripcion"),

        "descripcion":
            extraer_texto(obra_xml, "proy_descripcionlarga"),

        "acabados":
            extraer_texto(obra_xml, "acabados"),

        "observaciones":
            extraer_texto(obra_xml, "observaciones"),

        "descripcionextra":
            extraer_texto(obra_xml, "descripcionextra"),

        "superficie":
            extraer_texto(obra_xml, "proy_superficie_construida"),

        "cias_normalizadas":
            cias_normalizadas
    }

    # =========================
    # CREAR FOLDERS
    # =========================

    Path("output/html").mkdir(parents=True, exist_ok=True)
    Path("output/pdf").mkdir(parents=True, exist_ok=True)

    # =========================
    # JINJA
    # =========================

    env = Environment(
        loader=FileSystemLoader(".")
    )

    template = env.get_template("template.html")

    logo_path = Path("assets/logo_bimsa.png").resolve().as_uri()

    html = template.render(
        obra=obra,
        logo_path=logo_path
    )

    html_path = f"output/html/{clave}.html"

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    # =========================
    # PLAYWRIGHT
    # =========================

    pdf_path = f"output/pdf/{clave}.pdf"

    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = get_playwright_path()

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=True
        )

        page = await browser.new_page()

        html_absoluto = Path(html_path).resolve()

        await page.set_viewport_size({
            "width": 1400,
            "height": 1200
        })

        await page.goto(
            html_absoluto.as_uri()
        )

        await page.pdf(
            path=pdf_path,
            format="A4",
            landscape=True,
            prefer_css_page_size=True,
            print_background=True,
            scale=0.7,
            margin={
                "top": "10mm",
                "right": "5mm",
                "bottom": "10mm",
                "left": "5mm"
            }
        )
        await browser.close()

    print(f"PDF generado: {pdf_path}")

    return pdf_path