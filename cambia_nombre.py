#!/usr/bin/env python3
"""
Script de renombrado de fotos y vídeos para Nemo / Terminal.
Realiza renombrado con fecha y hora e incluso añadiendo una descripción en el nombre

Notificación Pasiva (notify-send): Se usa para avisos informativos, inicio/fin de procesos en segundo plano o errores leves donde el usuario no necesita hacer clic ni validar nada.
Diálogo Activo (zenity): Se usa para confirmaciones obligatorias (ej. "¿Desea eliminar 20 archivos?") o para informes finales de resumen estructurados que requieren que el usuario lea y presione "Aceptar".
"""


# Librerías estándar del sistema (sin dependencias externas)
import json        # Parseo nativo de metadatos devueltos por ffprobe
import os          # Operaciones con el sistema operativo
from pathlib import Path # Manejo seguro de rutas de archivos
import re          # Limpieza y formateo de fechas mediante expresiones regulares
import subprocess  # Subprocesos seguros para ejecutar ffprobe, ffmpeg y notify-send
import sys         # Paso de argumentos y control de salidas
import tempfile    # Gestión de archivos temporales con borrado automático



def check_dependencies():
    """Verifica que las herramientas CLI necesarias estén instaladas."""
    # Lo resolveríamos con: sudo apt update && sudo apt install -y exiftool zenity
    for cmd in ["exiftool"]:
        if subprocess.call(["which", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
            print(f"Error: Se requiere '{cmd}' instalado en el sistema.", file=sys.stderr)
            sys.exit(1)

def is_gui_mode():
    """Detecta si el script fue lanzado desde la GUI o sin terminal interactiva."""
    """Determina dinámicamente si hay un canal de entrada interactivo de consola. Si devuelve False, el script sabe automáticamente que fue invocado por un gestor de archivos (GUI) y que debe usar zenity"""
    return not sys.stdin.isatty()


def get_description(gui_mode):
    """Obtiene la descripción del usuario (CLI o GUI con Zenity).
    
    Sanea caracteres conflictivos y distingue entre 'descripción vacía' 
    y 'cancelar operación'.
    """
    prompt_text = "Introduce una descripcion opcional (los espacios se cambiaran por '_'):"
    raw_res = ""

    if gui_mode:
        # Comprobar si zenity está disponible antes de lanzar
        if subprocess.call(["which", "zenity"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
            try:
                # Quitamos stderr=DEVNULL temporalmente para manejar estados de salida limpios
                proc = subprocess.run(
                    ["zenity", "--entry", f"--text={prompt_text}", "--title=Organizador Multimedia"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
                )
                raw_res = proc.stdout.strip()
            except subprocess.CalledProcessError as e:
                # Si el código de salida es 1, el usuario pulsó "Cancelar" o cerró la ventana
                if e.returncode == 1:
                    print("Operacion cancelada por el usuario.", file=sys.stderr)
                    sys.exit(0) # Salida limpia, interrumpe el script
                return ""
    else:
        try:
            raw_res = input(f"{prompt_text}\n(Presiona Ctrl+C para cancelar)\n> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nOperacion cancelada por el usuario.", file=sys.stderr)
            sys.exit(0)

    # === ORDEN CORREGIDO EN cambia_nombre.py ===
    # 1. Primero eliminamos caracteres prohibidos
    sanitized = re.sub(r'[/\\:*?"<>|]', '', raw_res)
    
    # 2. Después cambiamos los espacios por un único guion bajo
    sanitized = re.sub(r'\s+', '_', sanitized)
    
    return sanitized


def get_metadata_date(file_path):
    """Usa exiftool para extraer la fecha de captura original de forma unificada.
    
    Aplica la opción '-api QuickTimeUTC' para corregir el desfase horario de los vídeos.
    """
    # -api QuickTimeUTC reajusta la hora UTC de los MP4/MOV a la hora local del PC ejecutor.
    # Usamos -d para que exiftool devuelva la fecha formateada directamente desde el binario.
    cmd = [
        "exiftool", "-json", "-api", "QuickTimeUTC",
        "-d", "%Y%m%dT%H%M%S", 
        "-DateTimeOriginal", "-CreateDate", "-MediaCreateDate", 
        str(file_path)
    ]
    
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
        data = json.loads(output.decode("utf-8"))[0]
        
        # Exiftool prioriza el orden del comando. Buscamos la primera clave que devuelva.
        for tag in ["DateTimeOriginal", "CreateDate", "MediaCreateDate"]:
            if tag in data:
                # Validamos que cumpla con la estructura básica esperada (ej: 20260603T191249)
                val = str(data[tag])
                if re.match(r'^\d{8}T\d{6}$', val):
                    return val
    except Exception:
        return None
    return None


def show_report(omitted_files, total_processed, gui_mode):
    """Muestra el reporte final al usuario."""
    report_lines = [
        f"Procesados con exito: {total_processed}",
        f"Archivos omitidos (sin metadatos): {len(omitted_files)}"
    ]
    if omitted_files:
        report_lines.append("\nLista de omitidos:")
        report_lines.extend([f"- {os.path.basename(f)}" for f in omitted_files[:15]]) # Mostrar max 15
        if len(omitted_files) > 15:
            report_lines.append(f"... y {len(omitted_files) - 15} mas.")

    report_text = "\n".join(report_lines)
    
    if gui_mode and subprocess.call(["which", "zenity"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
        subprocess.run(["zenity", "--info", f"--text={report_text}", "--title=Resultado del Procesado", "--width=400"])
    else:
        print("\n=== REPORTE FINAL ===")
        print(report_text)


############## Esta función ya no se usa ####################
def process_directory(target_dir, description, dry_run=False):
    """Itera sobre el directorio dato (target_directory) y renombra los archivos en base a metadatos y la descripción proporcionada (description)."""
    """El código implementa un modo nativo de simulación. Puedes clonar un par de imágenes de prueba en un directorio temporal y ejecutar el comando con el flag --dry-run"""
    path = Path(target_dir)
    if not path.is_dir():
        print(f"Error: {target_dir} no es un directorio valido.", file=sys.stderr)
        return [], 0

    omitted = []
    success_count = 0

    # Iterar sobre archivos (filtrando extensiones comunes de imagen/video)
    valid_extensions = {'.jpg', '.jpeg', '.png', '.mp4', '.avi', '.mkv', '.mov', '.mov_'}
    
    for child in path.iterdir():
        if child.is_file() and child.suffix.lower() in valid_extensions:
            date_str = get_metadata_date(child) # Obtenemos los metadatos del fichero que estamos tratando. Si no hay metadatos, llevaremos el fichero al listado de omitidos
            if not date_str:
                omitted.append(str(child))
                continue
            
            # Construir nombre base preliminar
            base_name = f"{date_str}"
            if description:
                base_name += f"_{description}"
            
            ext = child.suffix # Mantiene extension original con su caso original (.PNG, .jpg)
            
            # Control de colisiones (id_secuencia)
            new_path = path / f"{base_name}{ext}"
            counter = 1
            while new_path.exists():
                new_path = path / f"{base_name}_{counter}{ext}"
                counter += 1
            
            # Acción de renombrado / Dry-run
            if dry_run:
                print(f"[DRY-RUN] {child.name} -> {new_path.name}")
                success_count += 1
            else:
                try:
                    child.rename(new_path) # Aquí se renombra el archivo con el patrón obtenido de los metadatos y descripción
                    success_count += 1
                except Exception as e:
                    print(f"Error al renombrar {child.name}: {e}", file=sys.stderr)
                    omitted.append(str(child)+" - "+str(e))

    return omitted, success_count


def get_files_to_process(targets):
    """
    GENERADOR: Aplana la lista de objetivos. 
    Si recibe un directorio, extrae sus archivos válidos. 
    Si recibe un archivo suelto, lo valida y lo entrega.
    """
    valid_extensions = {'.jpg', '.jpeg', '.png', '.mp4', '.avi', '.mkv', '.mov', '.mov_'}
    
    for target in targets:
        path = Path(target)
        if path.is_dir():
            for child in path.iterdir():
                if child.is_file() and child.suffix.lower() in valid_extensions:
                    yield child # Actúa como cinta transportadora (eficiencia de RAM)
        elif path.is_file() and path.suffix.lower() in valid_extensions:
            yield path


def process_targets(targets, description, dry_run=False):
    """Motor unificado que renombra recursivamente consumiendo el generador."""
    omitted = []
    success_count = 0

    # Iteramos sobre el generador, no importa si vinieron de una carpeta o sueltos
    for child in get_files_to_process(targets):
        date_str = get_metadata_date(child)
        if not date_str:
            omitted.append(str(child)+" -- No hay metadatos de fecha")
            continue
        
        base_name = f"{date_str}"
        if description:
            base_name += f"_{description}"
        
        ext = child.suffix
        
        # ATENCIÓN: Usamos child.parent para asegurar que la foto se renombre 
        # exactamente en la carpeta donde reside, sin moverla de sitio.
        new_path = child.parent / f"{base_name}{ext}"
        counter = 1
        
        while new_path.exists():
            new_path = child.parent / f"{base_name}_{counter}{ext}"
            counter += 1
        
        if dry_run:
            print(f"[DRY-RUN] {child.name} -> {new_path.name}")
            success_count += 1
        else:
            try:
                child.rename(new_path)
                success_count += 1
            except IOError:
                print(f"Error al renombrar {child.name}: Permiso denegado", file=sys.stderr)
                omitted.append(str(child)+" -- Permiso denegado")
            except Exception as e:
                print(f"Error al renombrar {child.name}: {e}", file=sys.stderr)
                omitted.append(str(child))


    return omitted, success_count


def cambia_nombre():
    # Comprobar la entrada de argumentos en el log
    print(sys.argv, file=open("/tmp/debug_nemo.log", "w"))

    check_dependencies() #Verifica que las herramientas CLI necesarias estén instaladas.
    
    # Comprobar si se pasa el flag --dry-run
    # El código implementa un modo nativo de simulación. Puedes clonar un par de imágenes de prueba en un directorio temporal y ejecutar el comando con el flag --dry-run
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        sys.argv.remove("--dry-run")

    # Validar argumentos
    if len(sys.argv) < 2:
        print("Uso: python3 cambia_nombre.py <archivo/directorio 1> [archivo 2...] [--dry-run]")
        sys.exit(1)
        
    # sys.argv[1:] captura TODOS los elementos pasados desde la terminal o Nemo
    targets = sys.argv[1:]

    # Comprobar si se ejecuta desde GUI
    gui = is_gui_mode()
    
    # Solicitar descripción por terminal o por GUI
    desc = get_description(gui)
    
    # Ejecutar proceso con el directorio objetivo y la descripción porporcionada.
    # Hay 2 resultados: un listado de ficheros omitidos (porque no tienen metadatos) y un contador de ficheros procesados en total
    omitted, total = process_targets(targets, desc, dry_run=dry_run)
    
    # Mostrar reporte
    show_report(omitted, total, gui)

if __name__ == "__main__":
    cambia_nombre()