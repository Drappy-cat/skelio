import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Setup direktori output
output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets_sempro')
os.makedirs(output_dir, exist_ok=True)

csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'yolo11_biomechanics_benchmark.csv')
df = pd.read_csv(csv_path)

# Set gaya visual modern & profesional untuk presentasi
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.sans-serif'] = 'Segoe UI', 'DejaVu Sans', 'Arial'
plt.rcParams['font.size'] = 11

# ==============================================================================
# Grafik 1: Perbandingan FPS vs Akurasi (mAP50) Tiap Varian Model YOLOv11
# ==============================================================================
fig, ax1 = plt.subplots(figsize=(9, 5.5), dpi=300)

models = df['Model']
x = range(len(models))

color_fps = '#0284c7'  # Sky blue
color_acc = '#16a34a'  # Emerald green

# Bar chart untuk FPS
bars = ax1.bar([i - 0.18 for i in x], df['FPS'], width=0.35, label='FPS (Kecepatan Pemrosesan)', color=color_fps, alpha=0.9, edgecolor='none')
ax1.set_ylabel('Frames Per Second (FPS)', color=color_fps, fontweight='bold', fontsize=12)
ax1.set_ylim(0, max(df['FPS']) * 1.35)
ax1.tick_params(axis='y', labelcolor=color_fps)

# Value labels on bars
for bar in bars:
    yval = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 0.12, f'{yval:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold', color=color_fps)

# Garis kedua untuk Akurasi mAP50 (%)
ax2 = ax1.twinx()
line = ax2.plot([i + 0.18 for i in x], df['mAP50 / F1-Score (%)'], color=color_acc, marker='o', linewidth=2.5, markersize=8, label='mAP50 (%)', linestyle='-')
ax2.set_ylabel('Akurasi Pose mAP50 (%)', color=color_acc, fontweight='bold', fontsize=12)
ax2.set_ylim(0, 115)
ax2.tick_params(axis='y', labelcolor=color_acc)

# Value labels on line points
for i, val in enumerate(df['mAP50 / F1-Score (%)']):
    ax2.text(i + 0.18, val + 3.0, f'{val:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold', color=color_acc)

ax1.set_xticks(x)
ax1.set_xticklabels(models, fontweight='bold', fontsize=11)
ax1.set_xlabel('Varian Arsitektur YOLOv11-Pose', fontweight='bold', fontsize=12, labelpad=10)

plt.title('Trade-Off Kecepatan (FPS) vs Presisi Pose (mAP50)\nSistem SKELIO - UNESA 2026', fontsize=14, fontweight='bold', pad=15)
fig.tight_layout()

chart1_path = os.path.join(output_dir, 'chart1_fps_vs_accuracy.png')
plt.savefig(chart1_path, bbox_inches='tight')
plt.close()
print(f"[OK] Grafik 1 tersimpan: {chart1_path}")

# ==============================================================================
# Grafik 2: Ukuran Model (MB) vs Latensi Inferensi (ms)
# ==============================================================================
fig, ax = plt.subplots(figsize=(9, 5.2), dpi=300)

palette = ['#38bdf8', '#34d399', '#facc15', '#f87171', '#c084fc']
scatter = ax.scatter(df['Size (MB)'], df['Latency (ms)'], s=df['FPS']*70, c=range(len(df)), cmap='viridis', alpha=0.85, edgecolors='black', linewidth=1.5)

for i, row in df.iterrows():
    ax.annotate(f" {row['Model']}\n ({row['Size (MB)']} MB, {row['Latency (ms)']} ms)", 
                (row['Size (MB)'], row['Latency (ms)']),
                textcoords="offset points", xytext=(10, 5), ha='left', fontsize=10, fontweight='semibold')

ax.set_xlabel('Ukuran Bobot Model (MB)', fontweight='bold', fontsize=12)
ax.set_ylabel('Latensi Inferensi (ms)', fontweight='bold', fontsize=12)
ax.set_title('Komparasi Bobot Model vs Latensi Pemrosesan\n(Ukuran Gelembung Merepresentasikan FPS)', fontsize=13, fontweight='bold', pad=15)
ax.grid(True, linestyle='--', alpha=0.6)
fig.tight_layout()

chart2_path = os.path.join(output_dir, 'chart2_size_vs_latency.png')
plt.savefig(chart2_path, bbox_inches='tight')
plt.close()
print(f"[OK] Grafik 2 tersimpan: {chart2_path}")

# ==============================================================================
# Grafik 3: Galat Spasial Sendi (MPE) & Galat Homografi (Piksel)
# ==============================================================================
fig, ax = plt.subplots(figsize=(8.5, 5), dpi=300)
bar_width = 0.35
indices = range(len(models))

bar_mpe = ax.bar([i - bar_width/2 for i in indices], df['MPE (Pixels)'], width=bar_width, label='MPE (Mean Per-Joint Pixel Error)', color='#ef4444', alpha=0.85)
bar_homo = ax.bar([i + bar_width/2 for i in indices], df['Homography Error (Pixels)'], width=bar_width, label='Galat Homografi (Piksel)', color='#f59e0b', alpha=0.85)

for b in bar_mpe:
    y = b.get_height()
    ax.text(b.get_x() + b.get_width()/2, y + 0.08, f'{y:.2f}px', ha='center', va='bottom', fontsize=9, fontweight='bold', color='#b91c1c')

for b in bar_homo:
    y = b.get_height()
    ax.text(b.get_x() + b.get_width()/2, y + 0.08, f'{y:.2f}px', ha='center', va='bottom', fontsize=9, fontweight='bold', color='#b45309')

ax.set_xticks(indices)
ax.set_xticklabels(models, fontweight='bold', fontsize=11)
ax.set_ylabel('Galat Koordinat (Piksel)', fontweight='bold', fontsize=12)
ax.set_xlabel('Varian Model YOLOv11', fontweight='bold', fontsize=12)
ax.set_title('Evaluasi Presisi Spasial Koordinat Sendi & Transformasi Homografi\n(Semakin Rendah Semakin Presisi)', fontsize=13, fontweight='bold', pad=15)
ax.legend(loc='upper right', frameon=True)
fig.tight_layout()

chart3_path = os.path.join(output_dir, 'chart3_spatial_errors.png')
plt.savefig(chart3_path, bbox_inches='tight')
plt.close()
print(f"[OK] Grafik 3 tersimpan: {chart3_path}")
