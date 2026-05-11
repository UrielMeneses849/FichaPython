import asyncio
from playwright.async_api import async_playwright
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from parser import obtener_obra

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
            "telefono": cia.findtext("sucu_telefono1") or "",
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

    html_path = f"output/html/ficha_{clave}.html"

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    # =========================
    # PLAYWRIGHT
    # =========================

    pdf_path = f"output/pdf/ficha_{clave}.pdf"

    async with async_playwright() as p:

        browser = await p.chromium.launch()

        page = await browser.new_page()

        html_absoluto = Path(html_path).resolve()

        await page.goto(
            html_absoluto.as_uri()
        )

        await page.pdf(
            path=pdf_path,
            format="A4",
            print_background=True,
            margin={
                "top": "20px",
                "right": "20px",
                "bottom": "20px",
                "left": "20px"
            }
        )

        await browser.close()

    print(f"PDF generado: {pdf_path}")

    return pdf_path