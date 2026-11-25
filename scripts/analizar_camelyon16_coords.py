"""
Analisis de coordenadas CAMELYON16 descargadas de Kaggle.
Muestra la estructura de parches por WSI y estadisticas.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

BASE_DIR   = Path(__file__).resolve().parent.parent
COORDS_DIR = BASE_DIR / 'data_samples' / 'camelyon16' / 'coords' / 'CAMELYON16_FULL'
MASKS_DIR  = BASE_DIR / 'data_samples' / 'camelyon16' / 'masks'
FIG_DIR    = BASE_DIR / 'figures' / '05_CAMELYON16'
TABLAS_DIR = BASE_DIR / 'tablas'
FIG_DIR.mkdir(parents=True, exist_ok=True)
TABLAS_DIR.mkdir(parents=True, exist_ok=True)

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
            # coords tiene columnas [level, x, y]
            is_tumor = 'tumor' in wsi_dir.name.lower()
            is_test  = 'test' in wsi_dir.name.lower()
            tipo     = 'Tumor' if is_tumor else ('Test' if is_test else 'Normal')
            records.append({
                'WSI': wsi_dir.name,
                'Tipo': tipo,
                'Split': 'Test' if is_test else 'Train',
                'N_Parches': int(len(coords)),
                'Nivel_Resolucion': int(coords[0, 0]) if len(coords) > 0 else -1,
                'Coord_Min_X': int(coords[:, 1].min()) if len(coords) > 0 else 0,
                'Coord_Max_X': int(coords[:, 1].max()) if len(coords) > 0 else 0,
                'Coord_Min_Y': int(coords[:, 2].min()) if len(coords) > 0 else 0,
                'Coord_Max_Y': int(coords[:, 2].max()) if len(coords) > 0 else 0,
            })

df_coords = pd.DataFrame(records)
print(df_coords.head(10).to_string(index=False))
print(f"\nTotal WSIs: {len(df_coords)}")
print(f"Normales: {(df_coords['Tipo']=='Normal').sum()}")
print(f"Tumor:    {(df_coords['Tipo']=='Tumor').sum()}")
print(f"Test:     {(df_coords['Tipo']=='Test').sum()}")
print(f"Total parches: {df_coords['N_Parches'].sum():,}")
print(f"Parches por WSI: {df_coords['N_Parches'].mean():.0f} (mean)")

# Guardar tabla
df_coords.to_excel(TABLAS_DIR / 'camelyon16_coords_por_wsi.xlsx', index=False)
print("Excel guardado: camelyon16_coords_por_wsi.xlsx")

# =============================================================
# 2. FIGURA: Distribución de parches por WSI
# =============================================================
fig, axes = plt.subplots(1, 2, figsize=(17, 7), gridspec_kw={'width_ratios': [2.0, 1.1]})
fig.suptitle('CAMELYON16 — Analisis de Parches Extraidos por WSI (224x224 px @ 20x)',
             fontsize=14, fontweight='bold')

# Panel 1: Barras ordenadas por volumen tisular y cohorte
colors = {'Normal': '#2A9D8F', 'Tumor': '#E63946', 'Test': '#3498DB'}
df_sorted = df_coords.sort_values('N_Parches', ascending=False).reset_index(drop=True)
bar_colors = [colors[t] for t in df_sorted['Tipo']]
axes[0].bar(np.arange(len(df_sorted)), df_sorted['N_Parches'],
            color=bar_colors, width=1.0, alpha=0.88, edgecolor='none')
axes[0].set_title('Parches por WSI (399 laminas ordenadas de mayor a menor)', fontweight='bold')
axes[0].set_ylabel('N Parches (224x224 px)')
axes[0].set_xlabel('Indice de WSI (ordenadas por carga tisular)')
legend_handles = [
    mpatches.Patch(color=colors['Normal'], label=f"Normal Train ({(df_coords['Tipo']=='Normal').sum()} WSIs)"),
    mpatches.Patch(color=colors['Tumor'], label=f"Tumor Train ({(df_coords['Tipo']=='Tumor').sum()} WSIs)"),
    mpatches.Patch(color=colors['Test'], label=f"Test Ciego ({(df_coords['Tipo']=='Test').sum()} WSIs)"),
]
axes[0].legend(handles=legend_handles, loc='upper right')
axes[0].grid(axis='y', alpha=0.3)

# Panel 2: Resumen por cohorte
resumen = df_coords.groupby('Tipo').agg(
    N_WSI=('WSI', 'count'),
    Total_Parches=('N_Parches', 'sum'),
    Media_Parches=('N_Parches', 'mean'),
    Max_Parches=('N_Parches', 'max'),
).reset_index()

bars2 = axes[1].bar(resumen['Tipo'], resumen['Total_Parches'],
                    color=[colors[t] for t in resumen['Tipo']],
                    edgecolor='black', linewidth=0.8, width=0.55)
for bar, (_, row) in zip(bars2, resumen.iterrows()):
    h = bar.get_height()
    axes[1].text(bar.get_x() + bar.get_width() / 2, h + df_coords['N_Parches'].sum() * 0.01,
                 f"{int(h):,}", ha='center', va='bottom', fontsize=10, fontweight='bold')
    axes[1].text(bar.get_x() + bar.get_width() / 2, h * 0.5,
                 f"WSIs: {int(row['N_WSI'])}\nMedia: {row['Media_Parches']:.0f}",
                 ha='center', va='center', color='white', fontweight='bold', fontsize=10)
axes[1].set_ylim(0, resumen['Total_Parches'].max() * 1.15)
axes[1].set_title('Total de Parches por Cohorte', fontweight='bold')
axes[1].set_ylabel('Total Parches')
axes[1].grid(axis='y', alpha=0.3)

plt.tight_layout()
fig.savefig(FIG_DIR / 'camelyon16_distribucion_parches.png', dpi=150, bbox_inches='tight')
guardar_subplots_individuales(fig, 'camelyon16_distribucion_parches', FIG_DIR)
plt.close(fig)
print("Figura guardada: camelyon16_distribucion_parches.png")

# =============================================================
# 3. FIGURA: Mapa de coordenadas de una WSI de ejemplo
# =============================================================
tumor_wsis = df_coords[df_coords['Tipo'] == 'Tumor'].sort_values('N_Parches', ascending=False)
normal_wsis = df_coords[df_coords['Tipo'] == 'Normal'].sort_values('N_Parches', ascending=False)

fig2, axes2 = plt.subplots(1, 2, figsize=(16, 8))
fig2.suptitle('CAMELYON16 — Mapa Espacial 2D de Coordenadas de Parches\n(Grid Nivel 17, 224x224 px @ 20x)',
              fontsize=13, fontweight='bold')

for idx, (ax, row, color, label) in enumerate(zip(
    axes2,
    [normal_wsis.iloc[0], tumor_wsis.iloc[0]],
    ['#2A9D8F', '#E63946'],
    ['Normal (Negativa)', 'Tumor (Positiva)']
)):
    wsi_name = row['WSI']
    coords_file = COORDS_DIR / wsi_name / 'coords.npy'
    coords = np.load(coords_file)

    ax.scatter(coords[:, 1], coords[:, 2],
               c=color, s=2.2, alpha=0.55, edgecolors='none')
    ax.set_title(f'{label}\n{wsi_name}\n{len(coords):,} parches totales',
                 fontweight='bold', fontsize=11)
    ax.set_xlabel('Coordenada Grid X (Nivel 17)')
    ax.set_ylabel('Coordenada Grid Y (Nivel 17)')
    ax.invert_yaxis()
    ax.set_aspect('equal')
    ax.grid(alpha=0.3)

    patch = mpatches.Patch(color=color, label=f'{len(coords):,} parches 224x224px')
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
