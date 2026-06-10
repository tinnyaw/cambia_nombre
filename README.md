# cambia_nombre
Un script ligero, seguro y automatizado en Python para renombrar masivamente fotografías y vídeos utilizando metadatos EXIF y de vídeo unificados. Diseñado para funcionar de manera idéntica desde la terminal o integrado directamente en el menú contextual de tu gestor de archivos (Nemo).


Organizador Multimedia Multi-Distro 📸🎥

Un script ligero, seguro y automatizado en Python para renombrar masivamente fotografías y vídeos utilizando metadatos EXIF y de vídeo unificados. Diseñado para funcionar de manera idéntica desde la terminal o integrado directamente en el menú contextual de tu gestor de archivos favorito (Nemo).

🛠️ Características Principales

Eficiencia de RAM (yield): Implementa un generador perezoso (Lazy evaluation) para procesar directorios masivos sin desbordar la memoria RAM. Perfecto para equipos con recursos limitados (ej. Celeron N5000).

Doble Interfaz Inteligente: Detecta si hay una terminal activa. Si se ejecuta desde el escritorio (Nemo GUI), despliega cuadros de diálogo nativos con Zenity para solicitar información al usuario.

Prevención de Desgaste de SSD: Minimiza accesos y escrituras redundantes. El motor calcula las colisiones y valida formatos en memoria antes de aplicar operaciones en el disco duro.

Tratamiento de Zona Horaria UTC: Ajusta automáticamente la zona horaria nativa de las capturas de vídeo (MP4/MOV que usan UTC) adaptándolas a la hora local del sistema para sincronizarse con tus fotos.

Resolución de Colisiones Atómica: Evita la pérdida de datos. Si dos archivos se capturaron en el mismo segundo exacto, añade y escala sufijos secuenciales (_1, _2, etc.).

📋 Requisitos del Sistema

El script utiliza el intérprete base de Python 3 y utilidades comunes integradas en los repositorios oficiales de Debian/Ubuntu:

Python 3.6+

ExifTool (Motor de metadatos)

Zenity (Interfaz de diálogos ligeros GTK)

Puedes instalar todas las dependencias del sistema con una sola línea:

sudo apt update && sudo apt install -y libimage-exiftool-perl zenity


🚀 Instalación y Despliegue

1. Clonar el repositorio

git clone [https://github.com/tu-usuario/organizador-multimedia.git](https://github.com/tu-usuario/organizador-multimedia.git)
cd organizador-multimedia


2. Dar permisos de ejecución

chmod +x cambia_nombre.py


3. Crear enlace simbólico en el PATH global

Para invocar el comando desde cualquier lugar del sistema (necesario para la integración gráfica):

sudo ln -sf "$(pwd)/cambia_nombre.py" /usr/local/bin/cambia_nombre


🖱️ Integración con Nemo (Linux Mint)

Puedes añadir esta herramienta al menú contextual del botón derecho del ratón al seleccionar cualquier conjunto de archivos o directorios.

Crea un archivo en la ruta de acciones del usuario de Nemo:

nano ~/.local/share/nemo/actions/cambia_nombre.nemo_action


Pega el siguiente contenido:

[Nemo Action]
Name=Cambia nombre (Fechas EXIF)
Comment=Renombra selecciones múltiples por fecha de captura
Exec=cambia_nombre %F
Icon-Name=camera
Selection=any
Extensions=any;
Quote=double


Guarda el archivo (Ctrl+O, Enter, Ctrl+X) y reinicia Nemo para aplicar los cambios instantáneamente:

nemo -q


📖 Manual de Uso (Consola)

Procesar una carpeta completa

cambia_nombre /ruta/a/tus/fotos


Procesar archivos individuales en lote

cambia_nombre foto1.jpg foto2.png video1.mp4


Modo Simulación (Dry-Run)

Para comprobar qué nombres asignará el script sin realizar modificaciones reales en el disco:

cambia_nombre /ruta/a/tus/fotos --dry-run


🧪 Pruebas Unitarias y de Integración

Este proyecto utiliza un entorno de pruebas automatizadas mediante la biblioteca estándar de Python unittest.

Para evitar escrituras innecesarias en tu SSD, las pruebas utilizan entornos de simulación en la memoria RAM (tempfile), los cuales levantan un sistema de archivos virtual, realizan operaciones de renombrado de muestra y se destruyen de manera limpia al finalizar.

Para ejecutar los tests, utiliza el siguiente comando:

python3 -m unittest -v test_cambia_nombre.py


📂 Estructura del Repositorio

├── cambia_nombre.py       # Script principal de automatización
├── test_cambia_nombre.py  # Suite de pruebas unitarias y de integración
└── README.md              # Documentación técnica (este archivo)


🛡️ Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo para más detalles.
