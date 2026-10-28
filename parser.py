"""Contratos de ficha de la plataforma y entrada de Mensajero (XML/JSON)."""
import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

# Los nombres y su prioridad corresponden a solicitarFichaDatos de la web.
FIELDS = {
    "proy_clave": ["Clave_Proyecto", "clave"],
    "proy_nombre": ["proy_descripcioncorta", "Proyecto"],
    "proy_fechacierre": ["Fecha_Publicacion"],
    "proy_tipoproyectodescripcion": ["Tipo_Proyecto"],
    "proy_fecha_inicio": ["proy_fechainicio", "Fecha_Inicio"],
    "proy_fecha_fin": ["proy_fechatermino", "Fecha_Terminacion"],
    "proy_localizacion": ["Localizacion1"], "proy_inversion": ["Inversion"],
    "proy_etapa": ["Etapa"], "esta_descripcion": ["Estado_Proyecto"],
    "muni_descripcion": ["Municipio_Proyecto", "Municipio"],
    "sector": ["proy_sectordescripcion", "Sector"],
    "latitud": ["proy_ubicacionlatitud", "Latitud", "Latitude", "latitude", "lat"],
    "longitud": ["proy_ubicacionlongitud", "Longitud", "Longitude", "longitude", "lng", "lon"],
    "tipo_obra": ["tiob_descripcion", "Tipo_Obra"],
    "subgenero": ["suge_descripcion", "Subgenero"], "genero": ["gene_descripcion", "Genero"],
    "desa_descripcion": ["Tipo_Desarrollo"], "descripcion": ["proy_descripcionlarga", "Descripcion"],
    "acabados": [], "observaciones": [], "descripcionextra": [],
    "superficie": ["proy_superficie_construida", "Sup_Construida"],
    "caracteristicas": [], "actualizacion": [], "concurso": [],
    "porcentaje_avance": ["PorcentajeAvance", "Porcentaje_Avance", "Avance_Estimado", "Avance", "porcentajeAvance"],
    "imagen_explorer": ["imagenExplorer", "impo_image_url", "Impo_Image_Url", "Imagen_URL", "Image_URL"],
    "fecha_imagen": ["fechaImagen", "Fecha_Imagen", "impo_fecha_imagen", "impo_image_date"],
    "urlFicha": ["URL_Ficha", "Url_Ficha", "url_ficha", "Ficha_URL", "PDF", "Url_PDF"],
}


def validar_clave(clave):
    clave = str(clave).strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", clave):
        raise ValueError(f"Clave de ficha inválida: {clave!r}")
    return clave


def primero(record, *names):
    for name in names:
        value = record.get(name)
        if value is not None and str(value).strip():
            return value.strip() if isinstance(value, str) else value
    return ""


def lista(value):
    if isinstance(value, list):
        return value
    return [value] if isinstance(value, dict) else []


def normalizar_compania(company):
    contacts = company.get("contactos", company.get("CONTACTOS", []))
    if isinstance(contacts, dict) and "CONTACTO" in contacts:
        contacts = contacts["CONTACTO"]
    return {
        "nombre": primero(company, "nombre", "comp_razon_social"),
        "rol": primero(company, "rol", "roco_descripcion"),
        "direccion": primero(company, "direccion", "sucu_calle"),
        **{f"telefono{i}": primero(company, f"telefono{i}", f"sucu_telefono{i}") for i in (1, 2, 3)},
        "contactos": [{
            "puesto": primero(contact, "puesto", "cont_puesto"),
            "nombre": primero(contact, "nombre") or " ".join(str(primero(contact, tag)) for tag in
                ("cont_nombre", "cont_paterno", "cont_materno") if primero(contact, tag)),
            "email": primero(contact, "email", "cont_email"),
        } for contact in lista(contacts)],
    }


def normalizar_obra(record, origen="auto"):
    if not isinstance(record, dict):
        raise ValueError("Cada ficha debe ser un objeto con una clave y sus campos.")
    obra = {field: primero(record, field, *aliases) for field, aliases in FIELDS.items()}
    obra["proy_clave"] = validar_clave(obra["proy_clave"])
    raw_origin = origen if origen != "auto" else primero(record, "origen", "Origen", "sourceOrigin")
    raw_origin = str(raw_origin).strip().lower()
    if raw_origin and raw_origin not in ("explorer", "explora", "construleads"):
        raise ValueError(f"Origen no reconocido: {raw_origin}")
    obra["origen"] = ("explorer" if raw_origin in ("explorer", "explora") else "construleads") if raw_origin else (
        "explorer" if obra["imagen_explorer"] or obra["proy_clave"].upper().startswith("EX") else "construleads")
    companies = record.get("cias_normalizadas", record.get("CIAS", []))
    if isinstance(companies, dict) and "CIA" in companies:
        companies = companies["CIA"]
    obra["cias_normalizadas"] = [normalizar_compania(company) for company in lista(companies)]
    return obra


def xml_record(node):
    record = dict(node.attrib)
    for child in node:
        name = child.tag.split("}")[-1]
        value = xml_record(child) if len(child) or child.attrib else (child.text or "").strip()
        if name in record:
            record[name] = record[name] + [value] if isinstance(record[name], list) else [record[name], value]
        else:
            record[name] = value
    return record


def leer_xml(texto, origen="auto"):
    try:
        root = ET.fromstring(texto)
        if not len(root) and (root.text or "").strip().startswith("<"):
            root = ET.fromstring(root.text)
    except ET.ParseError as error:
        raise ValueError("La entrada no contiene XML válido.") from error
    candidates = [node for node in root.iter() if any(
        name.split("}")[-1] in ("proy_clave", "Clave_Proyecto", "clave")
        for name in [*node.attrib, *(child.tag for child in node)])]
    if not candidates:
        message = next((node.attrib.get("mensaje") or node.attrib.get("Mensaje") for node in root.iter()
                        if node.attrib.get("mensaje") or node.attrib.get("Mensaje")), "sin datos")
        raise ValueError(f"El servicio o archivo no contiene fichas: {message}")
    return [normalizar_obra(xml_record(node), origen) for node in candidates]


def leer_json(value, origen="auto"):
    if isinstance(value, list):
        return [normalizar_obra(record, origen) for record in value]
    if not isinstance(value, dict):
        raise ValueError("JSON debe contener una ficha o una lista de fichas.")
    if any(key in value for key in ("proy_clave", "Clave_Proyecto", "clave")):
        return [normalizar_obra(value, origen)]
    for key in ("obras", "OBRAS", "datos", "fichas", "data"):
        if key in value:
            return leer_json(value[key], origen)
    raise ValueError("No se encontraron fichas en el JSON.")


def cargar_fichas(path, origen="auto"):
    text = Path(path).read_text(encoding="utf-8-sig")
    obras = leer_xml(text, origen) if text.lstrip().startswith("<") else leer_json(json.loads(text), origen)
    keys = [obra["proy_clave"] for obra in obras]
    if len(keys) != len(set(keys)):
        raise ValueError("La entrada contiene claves duplicadas; enviar una ficha por clave.")
    return obras


def obtener_obra(clave, origen="auto"):
    """Compatibilidad con la consulta histórica por clave, sin sesión web."""
    clave = validar_clave(clave)
    if origen == "explorer" or (origen == "auto" and clave.upper().startswith("EX")):
        raise ValueError("Para Explorer, Mensajero debe proporcionar XML/JSON con --datos archivo.")
    response = requests.post(
        "https://construleads.com/ws_cl/ws_cl.asmx/ws_CL_sobrasfull_pdf",
        data={"sClave_obras": clave, "sTk": os.environ.get("BIMSA_TOKEN", "74611436e643e2c093c4713d44a6c81b1b5e1ba71050731bf45347775b8cc90e")},
        timeout=(15, 60),
    )
    response.raise_for_status()
    obras = leer_xml(response.content, origen)
    obra = next((obra for obra in obras if obra["proy_clave"] == clave), None)
    if obra is None:
        raise ValueError(f"El servicio no devolvió la clave solicitada: {clave}")
    return obra
