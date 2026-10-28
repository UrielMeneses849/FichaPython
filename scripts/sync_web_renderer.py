"""Importa el exportador de la web sin requerir Node al ejecutar Mensajero."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sync(source):
    destination = ROOT / "assets" / "web"
    destination.mkdir(parents=True, exist_ok=True)
    modules = ["fichaMetadata.js", "projectType.js", "fichaPdf.js"]
    source_files = {name: source / "src" / "utils" / name for name in modules}
    libraries = {
        "pdf-lib.min.js": source / "node_modules/pdf-lib/dist/pdf-lib.min.js",
        "fontkit.umd.min.js": source / "node_modules/@pdf-lib/fontkit/dist/fontkit.umd.min.js",
        "pdf-lib.LICENSE": source / "node_modules/pdf-lib/LICENSE.md",
        "fontkit.NOTICE.md": source / "node_modules/@pdf-lib/fontkit/README.md",
        "poppins.LICENSE": source / "node_modules/@fontsource/poppins/LICENSE",
    }
    # Leer primero: una dependencia faltante no debe dejar una importación parcial.
    contents = {name: path.read_bytes() for name, path in {**source_files, **libraries}.items()}
    for weight in (400, 500, 600):
        name = f"poppins-latin-{weight}-normal.woff"
        contents[name] = (source / "node_modules/@fontsource/poppins/files" / name).read_bytes()
    svg = (source / "public/logo-construleads.svg").read_text(encoding="utf-8")
    import base64
    contents["logo-construleads.png"] = base64.b64decode(re.search(r"data:image/png;base64,([A-Za-z0-9+/=]+)", svg)[1])
    engine = contents["fichaPdf.js"].decode()
    imports = re.findall(r"^import\s[\s\S]*?;", engine, flags=re.MULTILINE)
    if len(imports) != 4:
        raise ValueError("Cambiaron los imports del exportador web; revisar el adaptador antes de sincronizar.")
    engine = re.sub(r"^import\s[\s\S]*?;\n", "", engine, flags=re.MULTILINE)
    helpers = "\n".join(contents[name].decode() for name in modules[:2])
    body = re.sub(r"\bexport (?=(?:async )?(?:function|const))", "", helpers + "\n" + engine)
    contents["engine.js"] = (
        "// Generado por scripts/sync_web_renderer.py. No editar a mano.\n"
        "(() => {\nconst { PDFDocument, PDFName, PDFRawStream, PDFString, rgb } = PDFLib;\n"
        + body + "\nglobalThis.FichaPdf = { generarFichaPdf };\n})();\n"
    ).encode()
    for name, content in contents.items():
        (destination / name).write_bytes(content)
    manifest = {"source": "construleads-web/src/utils/fichaPdf.js", "files": {
        name: hashlib.sha256(content).hexdigest() for name, content in contents.items()
    }}
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Exportador web sincronizado en {destination}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Directorio de construleads-web con npm install realizado")
    sync(parser.parse_args().source.resolve())
