import requests
import xml.etree.ElementTree as ET

def obtener_obra(clave):

    url = "https://construleads.com/ws_cl_pruebas/ws_cl.asmx/ws_CL_sobrasfull"

    payload = {
        "sClave_obras": clave,
        "sTk": ""
    }

    response = requests.post(url, data=payload)

    xml_string = response.text

    root = ET.fromstring(xml_string)

    obra_xml = root.find(".//OBRAS")

    return obra_xml