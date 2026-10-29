"""Genera una ficha por clave consultando el XML del WS de la plataforma."""
import argparse
import asyncio
import sys
from pathlib import Path

from parser import obtener_obra, validar_clave
from render import firma_render, generar_pdf
from storage import guardar_metadata, pdf_existe


def argumentos():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("claves", nargs="+", help="Claves Construleads/Explorer separadas por espacios o comas")
    parser.add_argument("--origen", choices=["auto", "construleads", "explorer"], default="auto")
    parser.add_argument("--output-dir", default="output", help="Directorio con subcarpetas pdf/ y html/")
    parser.add_argument("--forzar", action="store_true", help="Regenerar aun cuando la entrada y el motor coincidan")
    args = parser.parse_args()
    return args


async def main(args):
    try:
        claves = list(dict.fromkeys(validar_clave(parte.strip()) for arg in args.claves
                                    for parte in arg.split(",") if parte.strip()))
        if not claves:
            raise ValueError("La entrada no contiene fichas para procesar.")
        firma = firma_render()
    except (ValueError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    pdfs, errores = [], 0
    for clave in claves:
        print(f"\nProcesando: {clave}", flush=True)
        try:
            obra = obtener_obra(clave, args.origen)
            # Una URL/ruta puede conservar su nombre y cambiar de imagen.
            existente = None if args.forzar or obra["imagen_explorer"] else pdf_existe(
                clave, output_dir=args.output_dir, firma=firma, obra=obra)
            if existente:
                print(f"PDF existente: {existente}")
                pdfs.append(existente)
                continue
            pdf = await generar_pdf(clave, obra=obra, output_dir=args.output_dir, base_dir=Path.cwd())
            guardar_metadata(pdf, firma, obra)
            pdfs.append(pdf)
        except Exception as error:
            errores += 1
            print(f"ERROR {clave}: {error}", file=sys.stderr, flush=True)
    print("\nPDFS GENERADOS:")
    for pdf in pdfs:
        print(pdf)
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(argumentos())))
