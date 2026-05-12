import sys
from pathlib import Path
from datetime import datetime

from PyPDF2 import PdfMerger

# =========================
# VALIDAR INPUT
# =========================

if len(sys.argv) < 2:
    print("Debes enviar una o varias claves")
    sys.exit()

# =========================
# SOPORTAR:
# OC1,OC2
# OC1 OC2
# =========================

claves = []

for arg in sys.argv[1:]:

    partes = arg.split(",")

    for parte in partes:

        clave = parte.strip()

        if clave:
            claves.append(clave)

# =========================
# PATHS
# =========================

pdf_folder = Path("output/pdf")
merged_folder = Path("output/merged")

merged_folder.mkdir(
    parents=True,
    exist_ok=True
)

# =========================
# BUSCAR PDFs
# =========================

pdfs_encontrados = []

for clave in claves:

    pdf_path = pdf_folder / f"{clave}.pdf"

    if pdf_path.exists():

        print(f"PDF encontrado: {pdf_path}")

        pdfs_encontrados.append(pdf_path)

    else:

        print(f"PDF no encontrado: {clave}")

# =========================
# VALIDAR PDFs
# =========================

if len(pdfs_encontrados) == 0:

    print("No hay PDFs para mergear")
    sys.exit()

# =========================
# MERGE
# =========================

merger = PdfMerger()

for pdf in pdfs_encontrados:

    merger.append(str(pdf))

timestamp = datetime.now().strftime(
    "%Y%m%d_%H%M%S"
)

output_path = merged_folder / f"merge_{timestamp}.pdf"

with open(output_path, "wb") as f:

    merger.write(f)

merger.close()

# =========================
# RESPUESTA FINAL
# =========================

print("\nMERGE GENERADO:")
print(output_path)