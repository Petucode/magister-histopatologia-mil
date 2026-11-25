import os
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
from PIL import Image
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

plt.rcParams['figure.figsize'] = (14, 6)
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
sns.set_theme(style='whitegrid')

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data_samples" / "nct_crc"
VAL_DIR = DATA_DIR / "CRC-VAL-HE-7K"
TRAIN_DIR = DATA_DIR / "NCT-CRC-HE-100K"

FIG_DIR = BASE_DIR / "figures" / "03_NCT_CRC"
FIG_DIR.mkdir(parents=True, exist_ok=True)

TABLAS_DIR = BASE_DIR / "tablas"
TABLAS_DIR.mkdir(parents=True, exist_ok=True)

CLASES_NCT = {
    'ADI':  {'nombre': 'Adipose',                   'desc': 'Tejido adiposo',            'color': '#F4A261'},
    'BACK': {'nombre': 'Background',                'desc': 'Fondo/vacio',                'color': '#8338EC'},
    'DEB':  {'nombre': 'Debris',                    'desc': 'Detritos celulares',         'color': '#888888'},
    'LYM':  {'nombre': 'Lymphocytes',               'desc': 'Linfocitos',                 'color': '#3A86FF'},
    'MUC':  {'nombre': 'Mucus',                     'desc': 'Mucosa',                     'color': '#06D6A0'},
    'MUS':  {'nombre': 'Smooth Muscle',             'desc': 'Musculo liso',               'color': '#E63946'},
    'NORM': {'nombre': 'Normal Colon Mucosa',       'desc': 'Mucosa colonica normal',     'color': '#2A9D8F'},
    'STR':  {'nombre': 'Cancer-associated Stroma',  'desc': 'Estroma asociado a cancer',  'color': '#E9C46A'},
    'TUM':  {'nombre': 'Colorectal Adenocarcinoma', 'desc': 'Adenocarcinoma colorrectal', 'color': '#D62828'},
}

def guardar_subplots_individuales(fig, nombre_base, fig_dir, dpi=150):
    """Guarda cada panel de una figura multi-panel como imagen individual."""
    axes = [ax for ax in fig.axes if ax.get_visible()]
    for i, ax in enumerate(axes):
        extent = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
        bbox = extent.expanded(1.2, 1.2)
        outpath = Path(fig_dir) / f'{nombre_base}_panel_{i+1}.png'
        fig.savefig(outpath, bbox_inches=bbox, dpi=dpi)
    print(f'[OK] {len(axes)} paneles individuales guardados en {Path(fig_dir).name}/{nombre_base}_panel_*.png')

def scan_dataset(root_dir, dataset_name):
    print(f"\n[INFO] Escaneando imagenes en {root_dir} ({dataset_name})...")
    registros = []
    if not root_dir.exists():
        print(f"[WARN] El directorio {root_dir} no existe.")
        return pd.DataFrame()

    for p in root_dir.rglob("*.tif"):
        clase = p.parent.name.upper()
        if clase in CLASES_NCT:
            registros.append({
                'path': str(p),
                'filename': p.name,
                'clase_codigo': clase,
                'clase_nombre': CLASES_NCT[clase]['nombre'],
                'clase_desc': CLASES_NCT[clase]['desc'],
                'dataset': dataset_name,
                'tamaño_kb': p.stat().st_size / 1024.0
            })
    
    df = pd.DataFrame(registros)
    print(f"[OK] Total imagenes encontradas en {dataset_name}: {len(df):,}")
    if len(df) > 0:
        counts = df['clase_codigo'].value_counts()
        for c, n in counts.items():
            print(f"   * {c:<5}: {n:>6,} ({n/len(df)*100:>5.2f}%)")
    return df

def compute_rgb_stats(df, max_samples_per_class=300):
    dataset_name = df['dataset'].iloc[0] if len(df) > 0 else 'Unknown'
    print(f"\n[INFO] Calculando estadisticas RGB para {dataset_name} (muestreo hasta {max_samples_per_class} por clase)...")
    stats_list = []
    
    for codigo, info in CLASES_NCT.items():
        sub_df = df[df['clase_codigo'] == codigo]
        if len(sub_df) == 0:
            continue
        n_sample = min(len(sub_df), max_samples_per_class)
        sampled = sub_df.sample(n=n_sample, random_state=42)
        
        r_means, g_means, b_means = [], [], []
        r_stds, g_stds, b_stds = [], [], []
        
        for path_str in sampled['path']:
            try:
                img = Image.open(path_str).convert('RGB')
                arr = np.asarray(img, dtype=np.float32)
                r_means.append(float(np.mean(arr[:, :, 0])))
                g_means.append(float(np.mean(arr[:, :, 1])))
                b_means.append(float(np.mean(arr[:, :, 2])))
                r_stds.append(float(np.std(arr[:, :, 0])))
                g_stds.append(float(np.std(arr[:, :, 1])))
                b_stds.append(float(np.std(arr[:, :, 2])))
            except Exception as e:
                pass
                
        stats_list.append({
            'dataset': dataset_name,
            'clase_codigo': codigo,
            'clase_nombre': info['nombre'],
            'n_muestreadas': len(r_means),
            'r_media': round(float(np.mean(r_means)), 2),
            'r_std': round(float(np.mean(r_stds)), 2),
            'g_media': round(float(np.mean(g_means)), 2),
            'g_std': round(float(np.mean(g_stds)), 2),
            'b_media': round(float(np.mean(b_means)), 2),
            'b_std': round(float(np.mean(b_stds)), 2),
            'brillo_global': round((float(np.mean(r_means)) + float(np.mean(g_means)) + float(np.mean(b_means))) / 3.0, 2)
        })
    return pd.DataFrame(stats_list)

def plot_distribution(df, dataset_label, filename_base):
    if len(df) == 0:
        return
    conteo = df.groupby(['clase_codigo', 'clase_nombre']).size().reset_index(name='n')
    conteo['porcentaje'] = conteo['n'] / len(df) * 100.0
    conteo['color'] = conteo['clase_codigo'].map(lambda c: CLASES_NCT[c]['color'])
    conteo = conteo.sort_values('n', ascending=True).reset_index(drop=True)

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle(f'Distribucion de Clases - {dataset_label} (N = {len(df):,})', fontsize=16, fontweight='bold')

    # Panel 1: Bar chart horizontal
    ax1 = axes[0]
    bars = ax1.barh(conteo['clase_codigo'], conteo['n'], color=conteo['color'], edgecolor='black', alpha=0.85)
    for bar, pct, n in zip(bars, conteo['porcentaje'], conteo['n']):
        ax1.text(bar.get_width() + (max(conteo['n'])*0.01), bar.get_y() + bar.get_height()/2,
                 f'{n:,} ({pct:.1f}%)', va='center', fontsize=10, fontweight='bold')
    ax1.set_xlabel('Numero de Parches', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Clase Histologica', fontsize=12, fontweight='bold')
    ax1.set_title(f'Conteo por Clase ({dataset_label})', fontsize=13, fontweight='bold')
    ax1.set_xlim(0, max(conteo['n']) * 1.25)
    ax1.grid(axis='x', alpha=0.3)

    # Panel 2: Pie chart
    ax2 = axes[1]
    conteo_desc = conteo.sort_values('n', ascending=False)
    ax2.pie(conteo_desc['n'], labels=conteo_desc['clase_codigo'], colors=conteo_desc['color'],
            autopct='%1.1f%%', startangle=90, wedgeprops=dict(edgecolor='white', linewidth=2))
    ax2.set_title(f'Proporcion Relativa por Clase ({dataset_label})', fontsize=13, fontweight='bold')

    plt.tight_layout()
    comb_path = FIG_DIR / f'{filename_base}.png'
    fig.savefig(str(comb_path), dpi=150, bbox_inches='tight')
    print(f'[OK] Figura guardada: {comb_path}')
    guardar_subplots_individuales(fig, filename_base, FIG_DIR, dpi=150)
    plt.close(fig)

def plot_comparison(df_val, df_train):
    if len(df_val) == 0 or len(df_train) == 0:
        print("[WARN] No se puede generar comparativa: falta alguno de los datasets.")
        return pd.DataFrame()

    c_val = df_val['clase_codigo'].value_counts()
    c_train = df_train['clase_codigo'].value_counts()
    
    clases_orden = list(CLASES_NCT.keys())
    
    data_comp = []
    for c in clases_orden:
        n_v = int(c_val.get(c, 0))
        n_t = int(c_train.get(c, 0))
        pct_v = round(n_v / len(df_val) * 100.0, 2)
        pct_t = round(n_t / len(df_train) * 100.0, 2)
        ratio = round(n_t / max(n_v, 1), 2)
        data_comp.append({
            'clase_codigo': c,
            'nombre': CLASES_NCT[c]['nombre'],
            'descripcion': CLASES_NCT[c]['desc'],
            'n_val': n_v,
            'pct_val': pct_v,
            'n_train': n_t,
            'pct_train': pct_t,
            'diff_pct': round(pct_t - pct_v, 2),
            'ratio_train_val': ratio
        })
    df_comp = pd.DataFrame(data_comp)

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('Comparativa de Distribucion: CRC-VAL-HE-7K (Val) vs NCT-CRC-HE-100K (Train)',
                 fontsize=16, fontweight='bold')

    # Panel 1: Comparativa de porcentajes
    ax1 = axes[0]
    x = np.arange(len(clases_orden))
    width = 0.38
    
    rects1 = ax1.bar(x - width/2, df_comp['pct_val'], width, label=f'Validacion (N={len(df_val):,})',
                     color='#3A86FF', edgecolor='black', alpha=0.85)
    rects2 = ax1.bar(x + width/2, df_comp['pct_train'], width, label=f'Entrenamiento (N={len(df_train):,})',
                     color='#E63946', edgecolor='black', alpha=0.85)
    
    ax1.set_ylabel('Proporcion (%)', fontsize=12, fontweight='bold')
    ax1.set_title('Proporcion de Clases: Val vs Train', fontsize=13, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(clases_orden, fontweight='bold')
    ax1.legend(frameon=True)
    ax1.grid(axis='y', alpha=0.3)
    
    for r in rects1:
        h = r.get_height()
        ax1.annotate(f'{h:.1f}%', xy=(r.get_x() + r.get_width()/2, h), xytext=(0, 3),
                    textcoords="offset points", ha='center', va='bottom', fontsize=8)
    for r in rects2:
        h = r.get_height()
        ax1.annotate(f'{h:.1f}%', xy=(r.get_x() + r.get_width()/2, h), xytext=(0, 3),
                    textcoords="offset points", ha='center', va='bottom', fontsize=8)

    # Panel 2: Conteo absoluto comparado
    ax2 = axes[1]
    rects3 = ax2.bar(x - width/2, df_comp['n_val'], width, label='Val (conteo)', color='#3A86FF', edgecolor='black', alpha=0.85)
    ax2_twin = ax2.twinx()
    rects4 = ax2_twin.bar(x + width/2, df_comp['n_train'], width, label='Train (conteo, eje der.)', color='#D62828', edgecolor='black', alpha=0.85)
    
    ax2.set_ylabel('Conteo Validacion (7K)', fontsize=11, fontweight='bold', color='#3A86FF')
    ax2_twin.set_ylabel('Conteo Entrenamiento (100K)', fontsize=11, fontweight='bold', color='#D62828')
    ax2.set_title('Conteos Absolutos (Ejes Duales)', fontsize=13, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(clases_orden, fontweight='bold')
    ax2.grid(alpha=0.3)
    
    plt.tight_layout()
    outpath = FIG_DIR / 'nct_comparativa_val_vs_train.png'
    fig.savefig(str(outpath), dpi=150, bbox_inches='tight')
    print(f'[OK] Figura comparativa guardada: {outpath}')
    guardar_subplots_individuales(fig, 'nct_comparativa_val_vs_train', FIG_DIR, dpi=150)
    plt.close(fig)

    return df_comp

def plot_samples(df, filename_base='nct_muestras_por_clase'):
    if len(df) == 0:
        return
    fig, axes = plt.subplots(3, 3, figsize=(13, 13))
    fig.suptitle('NCT-CRC-HE - Muestras Histologicas de las 9 Clases Tisulares (224x224 px)',
                 fontsize=16, fontweight='bold', y=0.99)
    
    for idx, (codigo, info) in enumerate(CLASES_NCT.items()):
        ax = axes[idx // 3][idx % 3]
        df_clase = df[df['clase_codigo'] == codigo]
        if len(df_clase) > 0:
            sample_row = df_clase.sample(1, random_state=42).iloc[0]
            try:
                img = Image.open(sample_row['path'])
                ax.imshow(img)
                ax.set_title(f"[{codigo}] {info['nombre']}\n{info['desc']}",
                             fontsize=11, fontweight='bold', color=info['color'])
                ax.axis('off')
            except Exception as e:
                ax.text(0.5, 0.5, f"Error cargando:\n{codigo}", ha='center', va='center')
                ax.axis('off')
        else:
            ax.text(0.5, 0.5, f"Sin imagen:\n{codigo}", ha='center', va='center')
            ax.axis('off')
            
    plt.tight_layout()
    outpath = FIG_DIR / f'{filename_base}.png'
    fig.savefig(str(outpath), dpi=150, bbox_inches='tight')
    print(f'[OK] Cuadricula de muestras guardada: {outpath}')
    guardar_subplots_individuales(fig, filename_base, FIG_DIR, dpi=150)
    plt.close(fig)

def run_analysis():
    print("=" * 70)
    print("ANALISIS COMPLETO NCT-CRC-HE (VALIDACION Y ENTRENAMIENTO)")
    print("=" * 70)

    # 1. Escanear Validacion
    df_val = scan_dataset(VAL_DIR, "CRC-VAL-HE-7K")
    if len(df_val) > 0:
        conteo_val = df_val.groupby(['clase_codigo', 'clase_nombre', 'clase_desc']).size().reset_index(name='n_muestras')
        conteo_val['porcentaje'] = round(conteo_val['n_muestras'] / len(df_val) * 100.0, 2)
        val_excel = TABLAS_DIR / "nct_val_distribucion_real.xlsx"
        conteo_val.to_excel(val_excel, index=False)
        print(f"[OK] Tabla Excel de validacion guardada: {val_excel}")

        # Generar figura validacion
        plot_distribution(df_val, "CRC-VAL-HE-7K (Validacion)", "nct_val_distribucion")
        # Generar muestras por clase
        plot_samples(df_val, "nct_muestras_por_clase")

    # 2. Escanear Entrenamiento
    df_train = scan_dataset(TRAIN_DIR, "NCT-CRC-HE-100K")
    if len(df_train) > 0:
        conteo_train = df_train.groupby(['clase_codigo', 'clase_nombre', 'clase_desc']).size().reset_index(name='n_muestras')
        conteo_train['porcentaje'] = round(conteo_train['n_muestras'] / len(df_train) * 100.0, 2)
        train_excel = TABLAS_DIR / "nct_train_distribucion_real.xlsx"
        conteo_train.to_excel(train_excel, index=False)
        print(f"[OK] Tabla Excel de entrenamiento guardada: {train_excel}")

        # Generar figura entrenamiento
        plot_distribution(df_train, "NCT-CRC-HE-100K (Entrenamiento Completo)", "nct_train_distribucion")

    # 3. Comparativa Completa
    if len(df_val) > 0 and len(df_train) > 0:
        df_comp = plot_comparison(df_val, df_train)
        comp_excel = TABLAS_DIR / "nct_comparativa_completa.xlsx"
        df_comp.to_excel(comp_excel, index=False)
        print(f"[OK] Tabla Excel comparativa guardada: {comp_excel}")

    # 4. Estadisticas RGB
    dfs_to_stat = []
    if len(df_val) > 0:
        dfs_to_stat.append(df_val)
    if len(df_train) > 0:
        dfs_to_stat.append(df_train)

    if dfs_to_stat:
        rgb_dfs = [compute_rgb_stats(d) for d in dfs_to_stat]
        df_rgb = pd.concat(rgb_dfs, ignore_index=True)
        rgb_excel = TABLAS_DIR / "nct_rgb_stats_por_clase.xlsx"
        df_rgb.to_excel(rgb_excel, index=False)
        print(f"[OK] Tabla Excel RGB guardada: {rgb_excel}")

    print("\n[OK] Proceso de analisis finalizado con exito.")

if __name__ == "__main__":
    run_analysis()
