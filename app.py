import sys
import asyncio

from storage import pdf_existe
from render import generar_pdf

# =========================
# VALIDAR INPUT
# =========================

if len(sys.argv) < 2:
    print("Debes enviar una o varias claves")
    sys.exit()

# =========================
# SOPORTAR:
# OC1,OC2,OC3
# OC1 OC2 OC3
# =========================

claves = []

for arg in sys.argv[1:]:

    partes = arg.split(",")

    for parte in partes:

        clave = parte.strip()

        if clave:
            claves.append(clave)

# =========================
# PROCESAR
# =========================

async def main():

    pdfs_finales = []

    for clave in claves:

        print(f"\nProcesando: {clave}")

        existe = pdf_existe(clave)

        if existe:

            print(f"PDF existente: {existe}")

            pdfs_finales.append(existe)

        else:

            print("No existe PDF, renderizando...")

            pdf_generado = await generar_pdf(clave)

            if pdf_generado:
                pdfs_finales.append(pdf_generado)

    # =========================
    # RESPUESTA FINAL
    # =========================

    print("\nPDFS GENERADOS:")

    for pdf in pdfs_finales:
        print(pdf)

asyncio.run(main())