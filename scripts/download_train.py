import os
import sys
import time
import zipfile
from pathlib import Path
import requests
from tqdm import tqdm

SAVE_DIR = Path(r"c:\Universidad\Magister\20 Noviembre Reunion\data_samples\nct_crc")
SAVE_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_URL = "https://zenodo.org/records/1214456/files/NCT-CRC-HE-100K.zip"
TRAIN_ZIP = SAVE_DIR / "NCT-CRC-HE-100K.zip"
TRAIN_DIR = SAVE_DIR / "NCT-CRC-HE-100K"

def download_file(url, target_path):
    print(f"Iniciando descarga de {url} -> {target_path}")
    headers = {}
    downloaded_bytes = 0
    mode = "wb"
    
    # Soporte para reanudación si existe archivo parcial
    if target_path.exists():
        downloaded_bytes = target_path.stat().st_size
        print(f"Archivo parcial detectado: {downloaded_bytes / (1024*1024):.2f} MB")
        try:
            r_head = requests.head(url, allow_redirects=True, timeout=20)
            total_size = int(r_head.headers.get("content-length", 0))
            if downloaded_bytes == total_size and total_size > 0:
                print("El archivo ZIP ya está completamente descargado.")
                return total_size
            elif downloaded_bytes < total_size:
                headers["Range"] = f"bytes={downloaded_bytes}-"
                mode = "ab"
                print(f"Reanudando descarga desde byte {downloaded_bytes}...")
        except Exception as e:
            print(f"No se pudo consultar encabezado: {e}")

    start_time = time.time()
    with requests.get(url, stream=True, headers=headers, timeout=120) as r:
        if r.status_code == 416: # Range not satisfiable
            print("El rango solicitado no es válido, reiniciando descarga completa...")
            mode = "wb"
            downloaded_bytes = 0
            with requests.get(url, stream=True, timeout=120) as r2:
                r2.raise_for_status()
                total = int(r2.headers.get("content-length", 0))
                with open(target_path, mode) as f, tqdm(
                    total=total, initial=0, unit="B", unit_scale=True, unit_divisor=1024, desc=target_path.name
                ) as pbar:
                    for chunk in r2.iter_content(chunk_size=2*1024*1024):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
        else:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0)) + downloaded_bytes
            with open(target_path, mode) as f, tqdm(
                total=total, initial=downloaded_bytes, unit="B", unit_scale=True, unit_divisor=1024, desc=target_path.name
            ) as pbar:
                for chunk in r.iter_content(chunk_size=2*1024*1024):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

    elapsed = time.time() - start_time
    final_size = target_path.stat().st_size
    print(f"Descarga finalizada: {final_size / (1024*1024):.2f} MB ({final_size / (1024*1024*1024):.2f} GB) en {elapsed:.1f} s ({final_size / (1024*1024) / max(elapsed, 0.001):.2f} MB/s)")
    return final_size

def extract_train():
    if TRAIN_DIR.exists() and len(list(TRAIN_DIR.rglob("*.tif"))) >= 100000:
        print(f"NCT-CRC-HE-100K ya existe con {len(list(TRAIN_DIR.rglob('*.tif')))} archivos.")
        return

    if not TRAIN_ZIP.exists():
        download_file(TRAIN_URL, TRAIN_ZIP)

    print(f"Verificando contenido de {TRAIN_ZIP.name}...")
    with zipfile.ZipFile(TRAIN_ZIP, "r") as zf:
        members = zf.namelist()
        print(f"Total entradas en ZIP: {len(members):,}. Primeras 5: {members[:5]}")
        has_root_dir = all(m.startswith("NCT-CRC-HE-100K/") or m.startswith("NCT-CRC-HE-100K\\") or m == "NCT-CRC-HE-100K" for m in members if m)
        extract_dest = SAVE_DIR if has_root_dir else TRAIN_DIR
        print(f"Extrayendo hacia {extract_dest}...")
        
        # Extracción por bloques para reportar avance cada 5,000 archivos
        total_files = len(members)
        for i, m in enumerate(members):
            zf.extract(m, extract_dest)
            if (i + 1) % 5000 == 0 or (i + 1) == total_files:
                print(f"Extrayendo: {i + 1:,}/{total_files:,} archivos ({(i + 1)/total_files*100:.1f}%)")

    print("Extracción completada exitosamente.")
    if TRAIN_ZIP.exists():
        TRAIN_ZIP.unlink()
        print(f"Archivo temporal {TRAIN_ZIP.name} eliminado para ahorrar espacio en disco.")

    tifs = list(TRAIN_DIR.rglob("*.tif"))
    print(f"Total imágenes TIFF extraídas en {TRAIN_DIR}: {len(tifs):,}")

if __name__ == "__main__":
    extract_train()
