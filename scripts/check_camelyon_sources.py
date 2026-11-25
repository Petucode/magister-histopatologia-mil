import requests

# Buscar archivos CAMELYON16 en Zenodo y otras fuentes
print("=== Buscando CAMELYON16 en Zenodo ===")
r = requests.get('https://zenodo.org/api/records/7667205')
if r.status_code == 200:
    data = r.json()
    title = data.get('metadata', {}).get('title', '?')
    print('Titulo:', title)
    files = data.get('files', [])
    for f in files[:10]:
        key = f.get('key', '?')
        size_mb = f.get('size', 0) / 1024 / 1024
        print(f'  {key} - {size_mb:.1f} MB')
else:
    print('Error:', r.status_code)

# Buscar en Kaggle para CAMELYON
print()
print("=== Buscando WSI slides disponibles ===")

# Intentar acceso a CAMELYON16 en Kaggle histopathologic cancer detection
# (que es exactamente PCam = parches de CAMELYON16)
kaggle_datasets = [
    'andrewmvd/camelyon-patch-classification',
    'histopathologiccancerdetection/histopathologic-cancer-detection',  
]
print("Datasets Kaggle posibles:")
for ds in kaggle_datasets:
    print(f"  kaggle datasets download -d {ds}")
