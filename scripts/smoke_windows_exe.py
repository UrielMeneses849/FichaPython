"""Prueba los EXE distribuidos, sus recursos embebidos y la combinación mixta."""
import argparse
import base64
import json
import os
import subprocess
import tempfile
from pathlib import Path

from PyPDF2 import PdfReader

ROOT = Path(__file__).resolve().parents[1]


def smoke(renderer, merger):
    records = json.loads((ROOT / "examples/fichas-mixtas.json").read_text(encoding="utf-8"))["fichas"]
    # Sólo fixture de integración: comprueba inclusión de imagen sin red.
    records[1]["imagen_explorer"] = "data:image/png;base64," + base64.b64encode(
        (ROOT / "assets/web/logo-construleads.png").read_bytes()).decode()
    records[1]["fecha_imagen"] = "2026-09-05"
    with tempfile.TemporaryDirectory(prefix="mensajero-smoke-") as directory:
        working = Path(directory)
        entrada = working / "entrada.json"
        entrada.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
        environment = {**os.environ}
        environment.pop("PLAYWRIGHT_BROWSERS_PATH", None)
        subprocess.run([str(renderer), "OC-EJEMPLO,EX-EJEMPLO", "--datos", str(entrada),
                        "--output-dir", "salida"], cwd=working, env=environment, check=True, timeout=240)
        pdf_dir = working / "salida/pdf"
        originals = [PdfReader(pdf_dir / f"{key}.pdf") for key in ("OC-EJEMPLO", "EX-EJEMPLO")]
        assert "Empresa de demostración" in "\n".join(p.extract_text() for p in originals[0].pages)
        text = "\n".join(p.extract_text() for p in originals[1].pages)
        for expected in ("Inversión estimada", "Imagen Satelital", "16.931700°", "5 sep 2026"):
            assert expected in text, f"Falta texto UTF-8 en EXE: {expected}"
        images = [ref.get_object() for page in originals[1].pages
                  for ref in page["/Resources"]["/XObject"].get_object().values()]
        assert len([image for image in images if image.get("/Subtype") == "/Image"]) >= 2
        subprocess.run([str(merger), "--usuario", "smoke", "--claves", "OC-EJEMPLO,EX-EJEMPLO",
                        "--input-dir", str(pdf_dir), "--output-dir", "combinado"],
                       cwd=working, env=environment, check=True, timeout=120)
        combined = PdfReader(working / "combinado/Reporte_Obras_smoke.pdf")
        assert len(combined.pages) == sum(len(reader.pages) for reader in originals)
        assert [page.extract_text() for page in combined.pages] == [
            page.extract_text() for reader in originals for page in reader.pages]
        print("EXE verificados: dos fichas independientes, acentos, imagen embebida y PDF combinado.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--renderer", type=Path, default=ROOT / "dist/ficha-renderer.exe")
    parser.add_argument("--merger", type=Path, default=ROOT / "dist/pdf-merger.exe")
    args = parser.parse_args()
    smoke(args.renderer.resolve(), args.merger.resolve())
