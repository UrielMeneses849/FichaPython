import os
os.makedirs("output/pdf", exist_ok=True)
os.makedirs("output/html", exist_ok=True)
PDF_DIR = "output/pdf"

def pdf_existe(clave):

    path = f"{PDF_DIR}/{clave}.pdf"

    if os.path.exists(path):
        return path

    return None