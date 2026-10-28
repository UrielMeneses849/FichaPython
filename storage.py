"""Caché versionada: una ficha antigua no sustituye una nueva plantilla/entrada."""
import hashlib
import json
from pathlib import Path


def firma_entrada(obra):
    return hashlib.sha256(json.dumps(obra, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def pdf_existe(clave, *, output_dir="output", firma=None, obra=None):
    path = Path(output_dir).resolve() / "pdf" / f"{clave}.pdf"
    meta = path.with_suffix(".meta.json")
    if not firma or not path.is_file() or not meta.is_file():
        return None
    try:
        metadata = json.loads(meta.read_text())
        if metadata["renderer"] != firma or metadata["entrada"] != firma_entrada(obra):
            return None
        if metadata["pdf"] != hashlib.sha256(path.read_bytes()).hexdigest():
            return None
        return str(path)
    except (OSError, ValueError, KeyError):
        return None


def guardar_metadata(pdf, firma, obra):
    path = Path(pdf)
    path.with_suffix(".meta.json").write_text(json.dumps({
        "renderer": firma, "entrada": firma_entrada(obra),
        "pdf": hashlib.sha256(path.read_bytes()).hexdigest(),
    }, indent=2) + "\n")
