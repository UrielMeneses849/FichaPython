import json
import tempfile
import unittest
from pathlib import Path

from parser import cargar_fichas, leer_json, leer_xml, normalizar_obra, validar_clave
from render import crear_html, imagen_satelital
from storage import guardar_metadata, pdf_existe


class MensajeroContract(unittest.TestCase):
    def test_both_sources_and_zero_progress_survive_json(self):
        obras = cargar_fichas(Path(__file__).parents[1] / "examples/fichas-mixtas.json")
        self.assertEqual([o["origen"] for o in obras], ["construleads", "explorer"])
        self.assertEqual(obras[0]["porcentaje_avance"], 0)
        self.assertEqual(obras[1]["latitud"], "16.931700")
        self.assertEqual(obras[1]["fecha_imagen"], "")
        self.assertEqual(obras[0]["cias_normalizadas"][0]["contactos"][0]["nombre"], "Contacto de prueba")

    def test_historical_xml_multiple_companies_and_contacts(self):
        xml = '''<root><OBRAS><proy_clave>OC123</proy_clave><CIAS>
        <CIA><comp_razon_social>Empresa 1</comp_razon_social><CONTACTOS>
        <CONTACTO><cont_nombre>Ana</cont_nombre><cont_paterno>Pérez</cont_paterno></CONTACTO>
        <CONTACTO><cont_nombre>Juan</cont_nombre></CONTACTO></CONTACTOS></CIA>
        <CIA><comp_razon_social>Empresa 2</comp_razon_social></CIA>
        </CIAS></OBRAS></root>'''
        obra = leer_xml(xml)[0]
        self.assertEqual(len(obra["cias_normalizadas"]), 2)
        self.assertEqual([c["nombre"] for c in obra["cias_normalizadas"][0]["contactos"]], ["Ana Pérez", "Juan"])

    def test_namespaces_attributes_and_escaped_asmx(self):
        xml = '<x:datos xmlns:x="urn:bimsa" Clave_Proyecto="EX123"><x:Latitud>0</x:Latitud><x:Fecha_Imagen>2026-02-09</x:Fecha_Imagen></x:datos>'
        obra = leer_xml(xml)[0]
        self.assertEqual((obra["origen"], obra["latitud"], obra["fecha_imagen"]), ("explorer", "0", "2026-02-09"))
        self.assertEqual(leer_xml('<string>&lt;datos Clave_Proyecto="EX123" /&gt;</string>')[0]["proy_clave"], "EX123")

    def test_origin_override_and_normalized_input(self):
        obra = normalizar_obra({"proy_clave": "CUSTOM123", "origen": "explora", "porcentaje_avance": 0,
                               "fecha_imagen": "2026-01-01", "proy_fechacierre": "2026-10-14"})
        self.assertEqual(obra["origen"], "explorer")
        self.assertEqual(obra["fecha_imagen"], "2026-01-01")
        self.assertEqual(normalizar_obra({"proy_clave": "CUSTOM123"}, "explorer")["origen"], "explorer")

    def test_empty_duplicate_and_invalid_input_fail(self):
        for bad in ("../OC1", "OC1/other", "OC1.html<script>", ""):
            with self.assertRaises(ValueError):
                validar_clave(bad)
        with self.assertRaises(ValueError):
            leer_xml('<row mensaje="sin datos"/>')
        with self.assertRaises(ValueError):
            leer_json(["bad record"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "entrada.json"
            path.write_text(json.dumps([{"clave": "OC1"}, {"clave": "OC1"}]))
            with self.assertRaises(ValueError):
                cargar_fichas(path)

    def test_cache_rejects_old_changed_and_corrupt_pdf(self):
        with tempfile.TemporaryDirectory() as directory:
            pdf = Path(directory) / "pdf/OC1.pdf"
            pdf.parent.mkdir()
            pdf.write_bytes(b"%PDF-fixture")
            obra = {"proy_clave": "OC1", "proy_nombre": "Uno"}
            self.assertIsNone(pdf_existe("OC1", output_dir=directory, firma="v1", obra=obra))
            guardar_metadata(pdf, "v1", obra)
            self.assertEqual(pdf_existe("OC1", output_dir=directory, firma="v1", obra=obra), str(pdf.resolve()))
            self.assertIsNone(pdf_existe("OC1", output_dir=directory, firma="v2", obra=obra))
            self.assertIsNone(pdf_existe("OC1", output_dir=directory, firma="v1", obra={**obra, "proy_nombre": "Dos"}))
            pdf.write_bytes(b"corrupt")
            self.assertIsNone(pdf_existe("OC1", output_dir=directory, firma="v1", obra=obra))

    def test_external_text_cannot_close_template_script(self):
        obra = normalizar_obra({"clave": "OC1", "Proyecto": '</script><script>alert("x")</script>'})
        html = crear_html(obra, Path.cwd())
        self.assertNotIn('</script><script>alert', html)
        self.assertIn('\\u003c/script\\u003e', html)

    def test_declared_but_missing_satellite_is_an_error(self):
        obra = normalizar_obra({"clave": "EX1", "imagen_explorer": "missing-image.jpg"})
        with self.assertRaisesRegex(ValueError, "No fue posible incluir"):
            imagen_satelital(obra, Path(tempfile.gettempdir()))


if __name__ == "__main__":
    unittest.main()
