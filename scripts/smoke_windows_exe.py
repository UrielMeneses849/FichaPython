"""Prueba los EXE con claves y un WS XML local, sin archivos de entrada."""
import argparse
import os
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

from PyPDF2 import PdfReader

ROOT = Path(__file__).resolve().parents[1]


def smoke(renderer, merger):
    requests_seen = []
    image = (ROOT / "assets/web/logo-construleads.png").read_bytes()

    class Service(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            if self.path != "/satelital.png":
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.end_headers()
            self.wfile.write(image)

        def do_POST(self):
            body = parse_qs(self.rfile.read(int(self.headers["Content-Length"])).decode(), keep_blank_values=True)
            key = body.get("sClave_obras", [""])[0]
            contract = {
                "OC-EJEMPLO": ("ws_cl_sobrasficha", "ws_construleads.xml"),
                "EX-EJEMPLO": ("ws_cl_sobrasficha_explorer", "ws_explorer.xml"),
            }.get(key)
            if not contract or self.path != "/ws_cl.asmx/" + contract[0] or body.get("sTk") != ["smoke-token"]:
                self.send_error(400, "Incorrect XML service request")
                return
            requests_seen.append(key)
            xml = (ROOT / "tests/fixtures" / contract[1]).read_text(encoding="utf-8")
            xml = xml.replace("__IMAGE_URL__", f"http://127.0.0.1:{self.server.server_port}/satelital.png")
            self.send_response(200)
            self.send_header("Content-Type", "text/xml; charset=utf-8")
            self.end_headers()
            self.wfile.write(xml.encode("utf-8"))

    server = ThreadingHTTPServer(("127.0.0.1", 0), Service)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with tempfile.TemporaryDirectory(prefix="mensajero-smoke-") as directory:
            working = Path(directory)
            environment = {**os.environ, "BIMSA_TOKEN": "smoke-token",
                           "BIMSA_WS_BASE_URL": f"http://127.0.0.1:{server.server_port}/ws_cl.asmx"}
            environment.pop("PLAYWRIGHT_BROWSERS_PATH", None)
            subprocess.run([str(renderer), "OC-EJEMPLO,EX-EJEMPLO", "--output-dir", "salida"],
                           cwd=working, env=environment, check=True, timeout=240)
            assert requests_seen == ["OC-EJEMPLO", "EX-EJEMPLO"], requests_seen
            assert not list(working.glob("entrada.*")), "El EXE no debe necesitar archivos de entrada"
            pdf_dir = working / "salida/pdf"
            originals = [PdfReader(pdf_dir / f"{key}.pdf") for key in ("OC-EJEMPLO", "EX-EJEMPLO")]
            assert "Empresa de demostración" in "\n".join(p.extract_text() for p in originals[0].pages)
            text = "\n".join(p.extract_text() for p in originals[1].pages)
            for expected in ("Inversión estimada", "Imagen Satelital", "16.931700°", "5 sep 2026"):
                assert expected in text, f"Falta texto UTF-8 en EXE: {expected}"
            images = [ref.get_object() for page in originals[1].pages
                      for ref in page["/Resources"]["/XObject"].get_object().values()]
            assert len([im for im in images if im.get("/Subtype") == "/Image"]) >= 2
            subprocess.run([str(merger), "--usuario", "smoke", "--claves", "OC-EJEMPLO,EX-EJEMPLO",
                            "--input-dir", str(pdf_dir), "--output-dir", "combinado"],
                           cwd=working, env=environment, check=True, timeout=120)
            combined = PdfReader(working / "combinado/Reporte_Obras_smoke.pdf")
            assert [page.extract_text() for page in combined.pages] == [
                page.extract_text() for reader in originals for page in reader.pages]
            print("EXE verificados: sólo claves, consulta XML por fuente, acentos, imagen y combinación.")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--renderer", type=Path, default=ROOT / "dist/ficha-renderer.exe")
    parser.add_argument("--merger", type=Path, default=ROOT / "dist/pdf-merger.exe")
    args = parser.parse_args()
    smoke(args.renderer.resolve(), args.merger.resolve())
