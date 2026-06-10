#Ejecutamos con python3 -m unittest -v test_cambia_nombre.py


import unittest
from unittest.mock import patch, MagicMock
import sys
import subprocess
import tempfile
from pathlib import Path

# Importamos las NUEVAS funciones de tu script
from cambia_nombre import get_metadata_date, get_description, get_files_to_process, process_targets

class TestCambiaNombre(unittest.TestCase):

    # ==========================================
    # PRUEBAS 1 a 4 (Funciones inalteradas)
    # ==========================================
    @patch('subprocess.check_output')
    def test_get_metadata_date_success(self, mock_subprocess):
        mock_subprocess.return_value = b'[{"DateTimeOriginal": "20260603T191249"}]'
        result = get_metadata_date("foto_prueba.jpg")
        self.assertEqual(result, "20260603T191249")

    @patch('subprocess.check_output')
    def test_get_metadata_date_missing(self, mock_subprocess):
        mock_subprocess.value = b'[{"SourceFile": "foto_sin_exif.jpg"}]'
        result = get_metadata_date("foto_sin_exif.jpg")
        self.assertIsNone(result)

    @patch('subprocess.run')
    @patch('subprocess.call', return_value=0)
    def test_get_description_gui_spaces_and_chars(self, mock_call, mock_run):
        mock_proc = MagicMock()
        mock_proc.stdout = "  Mi Viaje / Fotos:Familia * "
        mock_run.return_value = mock_proc
        result = get_description(gui_mode=True)
        self.assertEqual(result, "Mi_Viaje_FotosFamilia_")

    @patch('subprocess.run')
    @patch('subprocess.call', return_value=0)
    def test_get_description_gui_cancel(self, mock_call, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(returncode=1, cmd="zenity")
        with self.assertRaises(SystemExit) as cm:
            get_description(gui_mode=True)
        self.assertEqual(cm.exception.code, 0)

    # ==========================================
    # NUEVAS PRUEBAS PARA EL GENERADOR Y EL MOTOR
    # ==========================================
    def test_get_files_to_process_generator(self):
        """5. Prueba que el generador actúe como cinta transportadora ignorando PDF/TXT."""
        # Creamos un directorio temporal efímero y seguro
        with tempfile.TemporaryDirectory() as tmpdirname:
            tmp_dir = Path(tmpdirname)
            
            # Simulamos 3 archivos vacíos (.touch() crea el archivo en el disco)
            (tmp_dir / "foto_valida.jpg").touch()
            (tmp_dir / "documento.pdf").touch() # Extension no permitida
            (tmp_dir / "video.MP4").touch() # Mayúsculas (debería aceptarlo)

            # Modo 1: Le pasamos el directorio (simulando clic derecho en una carpeta en Nemo)
            resultados_dir = list(get_files_to_process([str(tmp_dir)]))
            # De los 3 archivos, solo debe haber atrapado el .jpg y el .MP4
            self.assertEqual(len(resultados_dir), 2)

            # Modo 2: Le pasamos archivos sueltos mezclados (simulando selección múltiple)
            archivos_sueltos = [str(tmp_dir / "documento.pdf"), str(tmp_dir / "foto_valida.jpg")]
            resultados_sueltos = list(get_files_to_process(archivos_sueltos))
            # Solo debe devolver el .jpg y omitir el PDF de forma transparente
            self.assertEqual(len(resultados_sueltos), 1)

    @patch('cambia_nombre.get_metadata_date')
    def test_process_targets_collision(self, mock_date):
        """6. Prueba el motor de colisiones y renombrado sobre archivos temporales reales."""
        with tempfile.TemporaryDirectory() as tmpdirname:
            tmp_dir = Path(tmpdirname)
            
            # Creamos dos archivos. Simularemos que ambos se tomaron en el mismo segundo
            archivo1 = tmp_dir / "foto_a.jpg"
            archivo2 = tmp_dir / "foto_b.jpg"
            archivo1.touch()
            archivo2.touch()

            # Bloqueamos el mock para que ambas fotos devuelvan exactamente la misma fecha
            mock_date.return_value = "20260603T191249"

            # Ejecutamos el motor de renombrado
            omitted, success = process_targets([str(tmp_dir)], "Familia", dry_run=False)

            self.assertEqual(success, 2)
            self.assertEqual(len(omitted), 0)

            # ================= VERIFICACIÓN MÁXIMA =================
            # Comprobamos que el sistema operativo creó los nombres resolviendo la colisión
            self.assertTrue((tmp_dir / "20260603T191249_Familia.jpg").exists())
            self.assertTrue((tmp_dir / "20260603T191249_Familia_1.jpg").exists())

if __name__ == '__main__':
    unittest.main()