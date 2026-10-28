"""Compara el ETL con el exportador original usando exactamente los mismos datos."""
import argparse
import asyncio
import base64
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from parser import cargar_fichas
from render import generar_pdf, imagen_satelital
from PyPDF2 import PdfReader
from PyPDF2.generic import ContentStream


async def verify(web, entrada, output):
    output.mkdir(parents=True, exist_ok=True)
    fixed_date = "2026-10-28T21:40:00Z"
    records = cargar_fichas(entrada)
    results = []
    for obra in records:
        key = obra["proy_clave"]
        pdf = await generar_pdf(key, obra=obra, base_dir=entrada.parent,
                                output_dir=output / "etl", generated_at=fixed_date)
        satellite = imagen_satelital(obra, entrada.parent)
        with tempfile.TemporaryDirectory() as directory:
            request = Path(directory) / "input.json"
            request.write_text(json.dumps({"obra": obra, "satellite": base64.b64encode(satellite).decode() if satellite else None}))
            reference = output / f"{key}-web.pdf"
            script = f'''
import {{readFile, writeFile}} from 'node:fs/promises';
import {{generarFichaPdf}} from {json.dumps((web / 'src/utils/fichaPdf.js').as_uri())};
const input = JSON.parse(await readFile(process.argv[2], 'utf8'));
const root = {json.dumps(web.as_uri())} + '/';
const font = weight => readFile(new URL(`node_modules/@fontsource/poppins/files/poppins-latin-${{weight}}-normal.woff`, root));
const [regularBytes, mediumBytes, semiBoldBytes, logo] = await Promise.all([
    font(400), font(500), font(600), readFile(new URL('public/logo-construleads.svg', root), 'utf8')]);
const resources = {{regularBytes, mediumBytes, semiBoldBytes,
    logoPng: logo.match(/data:image\\/png;base64,[A-Za-z0-9+/=]+/)[0],
    generatedAt: new Date({json.dumps(fixed_date)})}};
if (input.satellite) resources.satelliteBytes = Buffer.from(input.satellite, 'base64');
await writeFile(process.argv[3], await generarFichaPdf(input.obra, resources));
'''
            runner = Path(directory) / "reference.mjs"
            runner.write_text(script)
            subprocess.run(["node", str(runner), str(request), str(reference)],
                           check=True, env={**os.environ, "TZ": "America/Mexico_City"}, timeout=120)
        expected, actual = PdfReader(reference), PdfReader(pdf)
        assert len(expected.pages) == len(actual.pages), f"Número de páginas distinto en {key}"
        for index, (source, rendered) in enumerate(zip(expected.pages, actual.pages)):
            assert source.mediabox == rendered.mediabox, f"Tamaño de página distinto: {key}/{index + 1}"
            assert ContentStream(source.get_contents(), expected).get_data() == ContentStream(rendered.get_contents(), actual).get_data(), f"Contenido vectorial distinto: {key}/{index + 1}"
            assert source.extract_text() == rendered.extract_text(), f"Texto distinto: {key}/{index + 1}"
        results.append({"clave": key, "paginas": len(actual.pages), "contenido_vectorial_identico": True})
    (output / "parity.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--web", type=Path, required=True)
    parser.add_argument("--datos", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("tmp/parity"))
    args = parser.parse_args()
    asyncio.run(verify(args.web.resolve(), args.datos.resolve(), args.output_dir.resolve()))
