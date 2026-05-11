from PyPDF2 import PdfMerger
from datetime import datetime

def merge_pdfs(paths):

    merger = PdfMerger()

    for path in paths:
        merger.append(path)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_path = f"output/merged/merge_{timestamp}.pdf"

    merger.write(output_path)

    merger.close()

    return output_path