import requests
import xml.etree.ElementTree as ET

def obtener_obra(clave):

    url = "https://construleads.com/ws_cl/ws_cl.asmx/ws_CL_sobrasfull_pdf"

    payload = {
        "sClave_obras": clave,
        "sTk": "74611436e643e2c093c4713d44a6c81b1b5e1ba71050731bf45347775b8cc90e"
    }

    response = requests.post(url, data=payload)

    print("STATUS:", response.status_code)
    print("RESPONSE:")
    print(response.text)

    root = ET.fromstring(response.text)

    obra_xml = root.find(".//OBRAS")

    return obra_xml