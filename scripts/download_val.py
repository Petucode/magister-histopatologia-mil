import os
import sys
import time
import zipfile
from pathlib import Path
import requests
from tqdm import tqdm

SAVE_DIR = Path(r"c:\Universidad\Magister\20 Noviembre Reunion\data_samples\nct_crc")
SAVE_DIR.mkdir(parents=True, exist_ok=True)

VAL_URL = "https://zenodo.org/records/1214456/files/CRC-VAL-HE-7K.zip"
VAL_ZIP = SAVE_DIR / "CRC-VAL-HE-7K.zip"
VAL_DIR = SAVE_DIR / "CRC-VAL-HE-7K"

def download_file(url, target_path):
    print(f"Iniciando descarga de {url} -> {target_path}")
    headers = {}
    downloaded_bytes = 0
    mode = "wb"
    
    # Soporte para reanudación si existe archivo parcial
    if target_path.exists():
        downloaded_bytes = target_path.stat().st_size
        print(f"Archivo parcial detectado: {downloaded_bytes / (1024*1024):.2f} MB")
        # Verificar tamaño total
        try:
            r_head = requests.head(url, allow_redirects=True, timeout=15)
            total_size = int(r_head.headers.get("content-length", 0))
            if downloaded_bytes == total_size and total_size > 0:
                print("El archivo ZIP ya está completamente descargado.")
                return total_size
            elif downloaded_bytes < total_size:
                headers["Range"] = f"bytes={downloaded_bytes}-"
                mode = "ab"
                print(f"Reanudando desde byte {downloaded_bytes}...")
        except Exception as e:
            print(f"No se pudo consultar encabezado: {e}")

    start_time = time.time()
    with requests.get(url, stream=True, headers=headers, timeout=60) as r:
        if r.status_code == 416: # Range not satisfiable
            print("El rango no es válido, reiniciando descarga completa...")
            mode = "wb"
            downloaded_bytes = 0
            with requests.get(url, stream=True, timeout=60) as r2:
                r2.raise_for_status()
                total = int(r2.headers.get("content-length", 0))
                with open(target_path, mode) as f, tqdm(
                    total=total, initial=0, unit="B", unit_scale=True, unit_divisor=1024, desc=target_path.name
                ) as pbar:
                    for chunk in r2.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
        else:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0)) + downloaded_bytes
            with open(target_path, mode) as f, tqdm(
                total=total, initial=downloaded_bytes, unit="B", unit_scale=True, unit_divisor=1024, desc=target_path.name
            ) as pbar:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

    elapsed = time.time() - start_time
    final_size = target_path.stat().st_size
    print(f"Descarga finalizada: {final_size / (1024*1024):.2f} MB en {elapsed:.1f} s ({final_size / (1024*1024) / max(elapsed, 0.001):.2f} MB/s)")
    return final_size

def extract_val():
    if VAL_DIR.exists() and len(list(VAL_DIR.rglob("*.tif"))) >= 7000:
        print(f"CRC-VAL-HE-7K ya existe con {len(list(VAL_DIR.rglob('*.tif')))} archivos.")
        return

    if not VAL_ZIP.exists():
        download_file(VAL_URL, VAL_ZIP)

    print(f"Verificando contenido de {VAL_ZIP.name}...")
    with zipfile.ZipFile(VAL_ZIP, "r") as zf:
        members = zf.namelist()
        print(f"Archivos en ZIP: {len(members)}. Primeros 5: {members[:5]}")
        # Comprobar si el zip contiene carpeta raíz o no
        has_root_dir = all(m.startswith("CRC-VAL-HE-7K/") or m.startswith("CRC-VAL-HE-7K\\") or m == "CRC-VAL-HE-7K" for m in members if m)
        extract_dest = SAVE_DIR if has_root_dir else VAL_DIR
        print(f"Extrayendo hacia {extract_dest}...")
        for m in tqdm(members, desc="Extrayendo CRC-VAL"):
            zf.extract(m, extract_dest)

    print("Extracción completada exitosamente.")
    if VAL_ZIP.exists():
        VAL_ZIP.unlink()
        print(f"Archivo temporal {VAL_ZIP.name} eliminado.")

    tifs = list(VAL_DIR.rglob("*.tif"))
    print(f"Total imágenes TIFF extraídas en {VAL_DIR}: {len(tifs)}")

if __name__ == "__main__":
    extract_val()
