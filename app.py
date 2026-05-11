import sys
import asyncio

from storage import pdf_existe
from render import generar_pdf
from merger import merge_pdfs

# =========================
# VALIDAR INPUT
# =========================

if len(sys.argv) < 2:
    print("Debes enviar una o varias claves")
    sys.exit()

claves = []

for arg in sys.argv[1:]:
    claves.extend([
        clave.strip()
        for clave in arg.split(",")
        if clave.strip()
    ])

# =========================
# PROCESAR
# =========================

async def main():

    pdfs_finales = []

    for clave in claves:

        clave = clave.strip()

        print(f"\nProcesando: {clave}")

        existe = pdf_existe(clave)

        if existe:

            print(f"PDF existente: {existe}")

            pdfs_finales.append(existe)

        else:

            print("No existe PDF, renderizando...")

            pdf_generado = await generar_pdf(clave)

            pdfs_finales.append(pdf_generado)

    # =========================
    # SI SOLO ES 1 PDF
    # =========================

    if len(pdfs_finales) == 1:

        print("\nPDF FINAL:")
        print(pdfs_finales[0])

        return

    # =========================
    # MERGE
    # =========================

    merged = merge_pdfs(pdfs_finales)

    print("\nPDF MERGEADO:")
    print(merged)

asyncio.run(main())