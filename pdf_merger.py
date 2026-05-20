import sys
from pathlib import Path
from datetime import datetime
import os
import argparse

from PyPDF2 import PdfMerger

# =========================
# ARGUMENTOS
# =========================

parser = argparse.ArgumentParser()

parser.add_argument(
    "--usuario",
    required=True
)

parser.add_argument(
    "--claves",
    required=True
)

parser.add_argument(
    "--input-dir",
    required=True
)

parser.add_argument(
    "--output-dir",
    required=True
)

args = parser.parse_args()

usuario_id = args.usuario
input_dir = args.input_dir
output_dir = args.output_dir
print(f"Usuario recibido: {usuario_id}")
print(f"Claves recibidas: {args.claves}")
print(f"Input dir: {input_dir}")
print(f"Output dir: {output_dir}")

claves = []

for parte in args.claves.split(","):

    clave = parte.strip()

    if clave:
        claves.append(clave)

# =========================
# PATHS
# =========================

pdf_folder = Path(input_dir)
merged_folder = Path(output_dir)

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

output_path = merged_folder / f"Reporte_Obras_{usuario_id}.pdf"

# =========================
# SOBREESCRIBIR SI EXISTE
# =========================

if output_path.exists():

    os.remove(output_path)

    print(f"Archivo anterior eliminado: {output_path}")

with open(output_path, "wb") as f:

    merger.write(f)

merger.close()

# =========================
# RESPUESTA FINAL
# =========================

print("\nMERGE GENERADO:")
print(output_path)