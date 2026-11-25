"""
Analisis de coordenadas CAMELYON16 descargadas de Kaggle.
Muestra la estructura de parches por WSI y estadisticas.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

COORDS_DIR = Path(r'c:\Universidad\Magister\20 Noviembre Reunion\data_samples\camelyon16\coords\CAMELYON16_FULL')
MASKS_DIR  = Path(r'c:\Universidad\Magister\20 Noviembre Reunion\data_samples\camelyon16\masks')
FIG_DIR    = Path(r'c:\Universidad\Magister\20 Noviembre Reunion\figures\05_CAMELYON16')
TABLAS_DIR = Path(r'c:\Universidad\Magister\20 Noviembre Reunion\tablas')
FIG_DIR.mkdir(parents=True, exist_ok=True)

def guardar_subplots_individuales(fig, nombre_base, fig_dir, dpi=150):
    axes = [ax for ax in fig.axes if ax.get_visible()]
    for i, ax in enumerate(axes):
        extent = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
        bbox = extent.expanded(1.2, 1.2)
        outpath = Path(fig_dir) / f'{nombre_base}_panel_{i+1}.png'
        fig.savefig(outpath, bbox_inches=bbox, dpi=dpi)
    print(f'Paneles individuales guardados: {len(axes)}')

# =============================================================
# 1. EXPLORAR ESTRUCTURA DE COORDENADAS
# =============================================================
print("=== Estructura de coordenadas CAMELYON16 ===\n")

records = []
for wsi_dir in sorted(COORDS_DIR.iterdir()):
    if wsi_dir.is_dir():
        coords_file = wsi_dir / 'coords.npy'
        if coords_file.exists():
            coords = np.load(coords_file)
            is_tumor = 'Tumor' in wsi_dir.name or 'tumor' in wsi_dir.name
            records.append({
                'WSI': wsi_dir.name,
                'Tipo': 'Tumor' if is_tumor else 'Normal',
                'N_Parches': len(coords),
                'Coord_Min_X': int(coords[:, 0].min()) if len(coords) > 0 else 0,
                'Coord_Max_X': int(coords[:, 0].max()) if len(coords) > 0 else 0,
                'Coord_Min_Y': int(coords[:, 1].min()) if len(coords) > 0 else 0,
                'Coord_Max_Y': int(coords[:, 1].max()) if len(coords) > 0 else 0,
            })

df_coords = pd.DataFrame(records)
print(df_coords.head(10).to_string(index=False))
print(f"\nTotal WSIs: {len(df_coords)}")
print(f"Normales: {(df_coords['Tipo']=='Normal').sum()}")
print(f"Tumor:    {(df_coords['Tipo']=='Tumor').sum()}")
print(f"Total parches: {df_coords['N_Parches'].sum():,}")
print(f"Parches por WSI: {df_coords['N_Parches'].mean():.0f} (mean)")

# Guardar tabla
df_coords.to_excel(TABLAS_DIR / 'camelyon16_coords_por_wsi.xlsx', index=False)
print("Excel guardado: camelyon16_coords_por_wsi.xlsx")

# =============================================================
# 2. FIGURA: Distribución de parches por WSI
# =============================================================
fig, axes = plt.subplots(1, 2, figsize=(16, 7))
fig.suptitle('CAMELYON16 — Análisis de Parches Extraídos por WSI\n(Coordenadas @ 224×224 px, 20x)', 
             fontsize=14, fontweight='bold')

# Panel 1: Barras por tipo
colors = {'Normal': '#2A9D8F', 'Tumor': '#E63946'}
for tipo, grp in df_coords.groupby('Tipo'):
    ax = axes[0]
    bars = ax.bar(grp['WSI'].str[:15], grp['N_Parches'], 
                  color=colors[tipo], alpha=0.85, label=tipo, edgecolor='white', linewidth=0.5)
axes[0].set_title('Número de Parches por WSI', fontweight='bold')
axes[0].set_ylabel('N° Parches (224×224 px)')
axes[0].set_xlabel('WSI (nombre)')
axes[0].tick_params(axis='x', rotation=90, labelsize=5)
axes[0].legend()
axes[0].grid(axis='y', alpha=0.3)

# Panel 2: Resumen por tipo
resumen = df_coords.groupby('Tipo').agg(
    N_WSI=('WSI', 'count'),
    Total_Parches=('N_Parches', 'sum'),
    Media_Parches=('N_Parches', 'mean'),
    Max_Parches=('N_Parches', 'max'),
).reset_index()

x = range(len(resumen))
bars2 = axes[1].bar([r['Tipo'] for _, r in resumen.iterrows()], 
                    resumen['Total_Parches'],
                    color=[colors[t] for t in resumen['Tipo']],
                    edgecolor='black', linewidth=0.8, width=0.5)
axes[1].bar_label(bars2, fmt='%,.0f', padding=5, fontsize=12, fontweight='bold')
axes[1].set_title('Total Parches por Clase', fontweight='bold')
axes[1].set_ylabel('Total Parches')
for i, (_, row) in enumerate(resumen.iterrows()):
    axes[1].text(i, row['Total_Parches'] * 0.5, 
                f"N WSIs: {int(row['N_WSI'])}\nMedia: {row['Media_Parches']:.0f}",
                ha='center', va='center', color='white', fontweight='bold', fontsize=11)
axes[1].grid(axis='y', alpha=0.3)

plt.tight_layout()
fig.savefig(FIG_DIR / 'camelyon16_distribucion_parches.png', dpi=150, bbox_inches='tight')
guardar_subplots_individuales(fig, 'camelyon16_distribucion_parches', FIG_DIR)
plt.close(fig)
print("Figura guardada: camelyon16_distribucion_parches.png")

# =============================================================
# 3. FIGURA: Mapa de coordenadas de una WSI de ejemplo
# =============================================================
# Tomar la primera WSI de tumor con mas parches
tumor_wsis = df_coords[df_coords['Tipo'] == 'Tumor'].sort_values('N_Parches', ascending=False)
normal_wsis = df_coords[df_coords['Tipo'] == 'Normal'].sort_values('N_Parches', ascending=False)

fig2, axes2 = plt.subplots(1, 2, figsize=(16, 8))
fig2.suptitle('CAMELYON16 — Mapa Espacial de Coordenadas de Parches\n(Localización en la WSI gigapíxel)', 
              fontsize=13, fontweight='bold')

for idx, (ax, row, color, label) in enumerate(zip(
    axes2,
    [tumor_wsis.iloc[0], normal_wsis.iloc[0]],
    ['#E63946', '#2A9D8F'],
    ['Tumor (Positiva)', 'Normal (Negativa)']
)):
    wsi_name = row['WSI']
    coords_file = COORDS_DIR / wsi_name / 'coords.npy'
    coords = np.load(coords_file)
    
    # Muestra aleatoria si hay muchos parches
    if len(coords) > 5000:
        idx_sample = np.random.choice(len(coords), 5000, replace=False)
        coords_plot = coords[idx_sample]
        title_extra = f' (5000/{len(coords):,} mostrados)'
    else:
        coords_plot = coords
        title_extra = ''
    
    ax.scatter(coords_plot[:, 0], coords_plot[:, 1], 
               c=color, s=1, alpha=0.5)
    ax.set_title(f'{label}\n{wsi_name}{title_extra}\n{len(coords):,} parches totales', 
                 fontweight='bold', fontsize=11)
    ax.set_xlabel('Coordenada X (píxeles)')
    ax.set_ylabel('Coordenada Y (píxeles)')
    ax.invert_yaxis()  # Coordenadas de imagen (Y hacia abajo)
    ax.grid(alpha=0.3)
    
    # Agregar parche de leyenda
    patch = mpatches.Patch(color=color, label=f'{len(coords):,} parches 224×224px')
    ax.legend(handles=[patch], loc='upper right')

plt.tight_layout()
fig2.savefig(FIG_DIR / 'camelyon16_mapa_coords.png', dpi=150, bbox_inches='tight')
guardar_subplots_individuales(fig2, 'camelyon16_mapa_coords', FIG_DIR)
plt.close(fig2)
print("Figura guardada: camelyon16_mapa_coords.png")

# =============================================================
# 4. ESTADISTICAS DE MASCARAS XML
# =============================================================
xml_files = list(MASKS_DIR.rglob('*.xml'))
print(f"\nMascaras XML de tumor encontradas: {len(xml_files)}")
df_masks = pd.DataFrame([{
    'Archivo': f.name,
    'WSI_ID': f.stem,
    'Tamano_KB': round(f.stat().st_size / 1024, 1)
} for f in sorted(xml_files)])
df_masks.to_excel(TABLAS_DIR / 'camelyon16_mascaras_xml.xlsx', index=False)
print("Excel guardado: camelyon16_mascaras_xml.xlsx")

print("\n=== RESUMEN CAMELYON16 ===")
print(f"Total WSIs con coordenadas: {len(df_coords)}")
print(f"Total parches (224x224): {df_coords['N_Parches'].sum():,}")
print(f"Mascaras de anotacion: {len(xml_files)} archivos XML")
print(f"Figuras: {len(list(FIG_DIR.glob('*.png')))} guardadas")
