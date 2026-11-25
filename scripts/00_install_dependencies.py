"""
Script de instalación de dependencias para descargas de datasets.
Ejecutar ANTES de los notebooks.
"""
import subprocess, sys

def instalar(paquete):
    print(f"Instalando {paquete}...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", paquete, "-q"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"  ✅ {paquete} instalado")
    else:
        print(f"  ⚠️  {paquete}: {result.stderr[-200:]}")

paquetes = [
    "gdown",           # Google Drive
    "tcia_utils",      # TCIA / CAMELYON16
    "zenodo-get",      # Zenodo (NCT-CRC)
    "h5py",            # Para leer archivos HDF5 de PCam
    "requests",        # HTTP downloads
    "tqdm",            # Progress bars
    "openpyxl",        # Excel export
]

for p in paquetes:
    instalar(p)

print("\n✅ Todas las dependencias instaladas")
