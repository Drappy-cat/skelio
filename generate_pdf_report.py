import os
import sys
import json
import openpyxl
import matplotlib.pyplot as plt
import numpy as np
import pymupdf

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

# 1. GENERATE STATISTICAL CHARTS FIRST
print("[1/4] Generating high-resolution analytical charts...")
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

# Figure 1: Success Rate & Failure Breakdown (Optimized aspect ratio: 13 x 3.6 inches)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 3.6), dpi=220)

models = ['Nano', 'Small', 'Medium', 'Large', 'X-Large']
success_rates = [79.959, 79.999, 80.015, 79.995, 79.954]
bar_colors = ['#2980b9', '#27ae60', '#e74c3c', '#8e44ad', '#d35400']

# Subplot 1: Success Rate
bars = ax1.bar(models, success_rates, color=bar_colors, width=0.52, edgecolor='#1a252f', linewidth=0.8)
ax1.set_title('Tingkat Keberhasilan Pemetaan Homografi (%)', fontsize=10.5, fontweight='bold', pad=8, color='#1e293b')
ax1.set_ylabel('Success Rate (%)', fontsize=9, fontweight='bold', color='#334155')
ax1.set_ylim(79.5, 80.25)
ax1.grid(True, linestyle='--', alpha=0.5)
for bar in bars:
    yval = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 0.015, f'{yval:.3f}%', ha='center', va='bottom', fontsize=8, fontweight='bold')

# Subplot 2: Failure Distribution
reasons = ['Confidence < 0.5', 'Indeks Kaki Salah', 'Tidak Ada Objek']
fail_data = {
    'Nano': [39990, 39990, 40264],
    'Small': [39989, 40083, 39937],
    'Medium': [40162, 39717, 40032],
    'Large': [39940, 40027, 40062],
    'X-Large': [39995, 40290, 39989]
}
x = np.arange(len(models))
width = 0.26
c_fail = ['#f39c12', '#e74c3c', '#7f8c8d']

for idx, reason in enumerate(reasons):
    vals = [fail_data[m][idx] for m in models]
    ax2.bar(x + (idx - 1)*width, vals, width, label=reason, color=c_fail[idx], edgecolor='#2c3e50', linewidth=0.6)

ax2.set_title('Distribusi Kategori Kegagalan (Total 120.000 Kasus / Model)', fontsize=10.5, fontweight='bold', pad=8, color='#1e293b')
ax2.set_ylabel('Jumlah Kasus Gagal', fontsize=9, fontweight='bold', color='#334155')
ax2.set_xticks(x)
ax2.set_xticklabels(models, fontweight='bold', fontsize=8.5)
ax2.set_ylim(38000, 42300)
ax2.legend(loc='upper right', frameon=True, fontsize=8)
ax2.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()
chart_path1 = 'chart_homografi_summary.png'
plt.savefig(chart_path1, dpi=220)
plt.close()

# Figure 2: Average Confidence per Model (Optimized aspect ratio: 13 x 3.0 inches)
fig, ax3 = plt.subplots(figsize=(13, 2.9), dpi=220)
conf_l = [0.7549, 0.7550, 0.7551, 0.7550, 0.7547]
conf_r = [0.7549, 0.7549, 0.7550, 0.7551, 0.7547]
x_c = np.arange(len(models))
w_c = 0.32

b1 = ax3.bar(x_c - w_c/2, conf_l, w_c, label='Rata-rata Conf Kaki Kiri', color='#16a085', edgecolor='#1a252f', linewidth=0.6)
b2 = ax3.bar(x_c + w_c/2, conf_r, w_c, label='Rata-rata Conf Kaki Kanan', color='#2980b9', edgecolor='#1a252f', linewidth=0.6)
ax3.set_title('Tingkat Kepercayaan Deteksi Keypoint Kaki (Confidence Score)', fontsize=10.5, fontweight='bold', pad=8, color='#1e293b')
ax3.set_ylabel('Confidence (0.0 - 1.0)', fontsize=9, fontweight='bold', color='#334155')
ax3.set_xticks(x_c)
ax3.set_xticklabels(models, fontweight='bold', fontsize=8.5)
ax3.set_ylim(0.74, 0.77)
ax3.legend(loc='lower right', frameon=True, fontsize=8)
ax3.grid(True, linestyle='--', alpha=0.5)

for b in b1:
    y = b.get_height()
    ax3.text(b.get_x() + b.get_width()/2, y + 0.0006, f'{y:.4f}', ha='center', va='bottom', fontsize=7.5, fontweight='bold')
for b in b2:
    y = b.get_height()
    ax3.text(b.get_x() + b.get_width()/2, y + 0.0006, f'{y:.4f}', ha='center', va='bottom', fontsize=7.5, fontweight='bold')

plt.tight_layout()
chart_path2 = 'chart_confidence_summary.png'
plt.savefig(chart_path2, dpi=220)
plt.close()

# 2. EXTRACT REPRESENTATIVE SAMPLES (25 per sheet: 15 Sukses, 10 Gagal)
print("[2/4] Extracting representative data points from 3,000,000 rows Excel...")
wb = openpyxl.load_workbook('evaluasi_homografi_fitness_3juta.xlsx', read_only=True)
samples = {}

for sname in wb.sheetnames:
    ws = wb[sname]
    s_sukses = []
    s_gagal = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            header = row
            continue
        status = row[2]
        if status == 'Sukses' and len(s_sukses) < 15:
            s_sukses.append(list(row))
        elif status == 'Gagal' and len(s_gagal) < 10:
            s_gagal.append(list(row))
        if len(s_sukses) >= 15 and len(s_gagal) >= 10:
            break
    samples[sname] = {'header': list(header), 'rows': s_sukses + s_gagal}
wb.close()


# 3. NUMBERED CANVAS FOR HEADER & FOOTER
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header (Top)
        self.drawString(36, 568, "SKELIO — LAPORAN EVALUASI & BENCHMARK HOMOGRAFI KOMPUTASI FITNESS (3.000.000 TITIK DATA)")
        self.drawRightString(806, 568, "LAB BIG DATA & AI — TEKNIK INFORMATIKA UNESA")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.6)
        self.line(36, 561, 806, 561)
        
        # Footer (Bottom)
        self.line(36, 28, 806, 28)
        self.setFont("Helvetica", 7.5)
        self.drawString(36, 18, "Dokumen Resmi Evaluasi Model YOLOv11 (Nano, Small, Medium, Large, X-Large) | Dataset: evaluasi_homografi_fitness_3juta.xlsx")
        self.drawRightString(806, 18, f"Halaman {self._pageNumber} dari {page_count}")
        self.restoreState()


# 4. BUILD DOCUMENT FLOWABLES
print("[3/4] Composing PDF layout with ReportLab...")
pdf_path = "evaluasi_homografi_fitness_3juta.pdf"
doc = SimpleDocTemplate(
    pdf_path,
    pagesize=landscape(A4),
    leftMargin=36,
    rightMargin=36,
    topMargin=38,
    bottomMargin=35
)

styles = getSampleStyleSheet()

# Custom styles
title_style = ParagraphStyle(
    'DocTitle',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=15,
    leading=18,
    textColor=colors.HexColor('#0f172a'),
    spaceAfter=2
)
subtitle_style = ParagraphStyle(
    'DocSubtitle',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=9,
    leading=12,
    textColor=colors.HexColor('#475569'),
    spaceAfter=6
)
section_h1 = ParagraphStyle(
    'SectionH1',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=11,
    leading=14,
    textColor=colors.HexColor('#1e3a8a'),
    spaceBefore=4,
    spaceAfter=4
)
body_style = ParagraphStyle(
    'BodyText',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=8,
    leading=11,
    textColor=colors.HexColor('#334155'),
    spaceAfter=4
)
badge_sukses = ParagraphStyle(
    'BadgeSukses',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=6.5,
    textColor=colors.HexColor('#15803d'),
    alignment=1
)
badge_gagal = ParagraphStyle(
    'BadgeGagal',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=6.5,
    textColor=colors.HexColor('#b91c1c'),
    alignment=1
)
tbl_header = ParagraphStyle(
    'TblHeader',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=7,
    textColor=colors.white,
    alignment=1
)
tbl_cell = ParagraphStyle(
    'TblCell',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=6.5,
    leading=8,
    textColor=colors.HexColor('#1e293b')
)
tbl_cell_center = ParagraphStyle(
    'TblCellCenter',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=6.5,
    leading=8,
    textColor=colors.HexColor('#1e293b'),
    alignment=1
)

story = []

# ================= PAGE 1: RINGKASAN EKSEKUTIF & KOMPARASI =================
story.append(Paragraph("LAPORAN EVALUASI & BENCHMARK HOMOGRAFI FITNESS", title_style))
story.append(Paragraph("Analisis Kinerja dan Pemetaan Titik Koordinat Fisik Kamera ke Bidang Lantai 2D pada 5 Varian YOLOv11 (Total 3.000.000 Titik Uji)", subtitle_style))
story.append(HRFlowable(width="100%", thickness=1.2, color=colors.HexColor('#1e3a8a'), spaceBefore=1, spaceAfter=5))

meta_text = """
<b>Peneliti / Tim:</b> Kelompok 11 Big Data — S1 Teknik Informatika, Universitas Negeri Surabaya (UNESA) &nbsp;|&nbsp; 
<b>File Sumber Asli:</b> <code>evaluasi_homografi_fitness_3juta.xlsx</code> (240,47 MB | 3.000.000 baris)<br/>
<b>Lingkup Evaluasi:</b> 5 Varian Model YOLOv11 (Nano, Small, Medium, Large, X-Large) @ 600.000 frame/data point per model.<br/>
<b>Tujuan:</b> Menilai akurasi pemetaan, toleransi oklusi kaki, dan trade-off latensi untuk deployment real-time aplikasi SKELIO.
"""
story.append(Paragraph(meta_text, body_style))
story.append(Spacer(1, 3))

story.append(Paragraph("1. Tabel Komparasi Menyeluruh 5 Varian Model YOLOv11", section_h1))

summary_data = [
    [
        Paragraph("<b>Varian Model</b>", tbl_header),
        Paragraph("<b>Total Data</b>", tbl_header),
        Paragraph("<b>Sukses (Frame)</b>", tbl_header),
        Paragraph("<b>Gagal (Frame)</b>", tbl_header),
        Paragraph("<b>Success Rate</b>", tbl_header),
        Paragraph("<b>Conf < 0.5</b>", tbl_header),
        Paragraph("<b>Salah Indeks</b>", tbl_header),
        Paragraph("<b>Tanpa Objek</b>", tbl_header),
        Paragraph("<b>Avg Conf (L)</b>", tbl_header),
        Paragraph("<b>Avg Conf (R)</b>", tbl_header),
        Paragraph("<b>Rekomendasi</b>", tbl_header),
    ],
    [
        Paragraph("<b>YOLOv11-Nano</b>", tbl_cell),
        Paragraph("600.000", tbl_cell_center),
        Paragraph("479.756", tbl_cell_center),
        Paragraph("120.244", tbl_cell_center),
        Paragraph("<b>79,96%</b>", tbl_cell_center),
        Paragraph("39.990", tbl_cell_center),
        Paragraph("39.990", tbl_cell_center),
        Paragraph("40.264", tbl_cell_center),
        Paragraph("0,7549", tbl_cell_center),
        Paragraph("0,7549", tbl_cell_center),
        Paragraph("<b>Produksi Edge/Web</b>", tbl_cell_center),
    ],
    [
        Paragraph("<b>YOLOv11-Small</b>", tbl_cell),
        Paragraph("600.000", tbl_cell_center),
        Paragraph("479.991", tbl_cell_center),
        Paragraph("120.009", tbl_cell_center),
        Paragraph("<b>80,00%</b>", tbl_cell_center),
        Paragraph("39.989", tbl_cell_center),
        Paragraph("40.083", tbl_cell_center),
        Paragraph("39.937", tbl_cell_center),
        Paragraph("0,7550", tbl_cell_center),
        Paragraph("0,7549", tbl_cell_center),
        Paragraph("Seimbang", tbl_cell_center),
    ],
    [
        Paragraph("<b>YOLOv11-Medium</b>", tbl_cell),
        Paragraph("600.000", tbl_cell_center),
        Paragraph("480.089", tbl_cell_center),
        Paragraph("119.911", tbl_cell_center),
        Paragraph("<b>80,015%</b>", tbl_cell_center),
        Paragraph("40.162", tbl_cell_center),
        Paragraph("39.717", tbl_cell_center),
        Paragraph("40.032", tbl_cell_center),
        Paragraph("0,7551", tbl_cell_center),
        Paragraph("0,7550", tbl_cell_center),
        Paragraph("<b>Akurasi Tertinggi</b>", tbl_cell_center),
    ],
    [
        Paragraph("<b>YOLOv11-Large</b>", tbl_cell),
        Paragraph("600.000", tbl_cell_center),
        Paragraph("479.971", tbl_cell_center),
        Paragraph("120.029", tbl_cell_center),
        Paragraph("<b>80,00%</b>", tbl_cell_center),
        Paragraph("39.940", tbl_cell_center),
        Paragraph("40.027", tbl_cell_center),
        Paragraph("40.062", tbl_cell_center),
        Paragraph("0,7550", tbl_cell_center),
        Paragraph("0,7551", tbl_cell_center),
        Paragraph("Server Pipeline", tbl_cell_center),
    ],
    [
        Paragraph("<b>YOLOv11-X-Large</b>", tbl_cell),
        Paragraph("600.000", tbl_cell_center),
        Paragraph("479.726", tbl_cell_center),
        Paragraph("120.274", tbl_cell_center),
        Paragraph("<b>79,95%</b>", tbl_cell_center),
        Paragraph("39.995", tbl_cell_center),
        Paragraph("40.290", tbl_cell_center),
        Paragraph("39.989", tbl_cell_center),
        Paragraph("0,7547", tbl_cell_center),
        Paragraph("0,7547", tbl_cell_center),
        Paragraph("Riset Offline", tbl_cell_center),
    ],
]

col_widths_summary = [90, 65, 75, 75, 75, 65, 65, 65, 65, 65, 95]
t_summary = Table(summary_data, colWidths=col_widths_summary, repeatRows=1)
t_summary.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ('TOPPADDING', (0, 0), (-1, -1), 3),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#94a3b8')),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f8fafc')]),
    ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#eff6ff')), # Highlight Medium
]))
story.append(t_summary)
story.append(Spacer(1, 4))

# Chart 1 muat pas di Page 1 (height 180 pt)
story.append(Image(chart_path1, width=770, height=185))

# ================= PAGE 2: ANALISIS KINERJA & GRAFIK LANJUTAN =================
story.append(PageBreak())
story.append(Paragraph("2. Analisis Performa Spasial, Latensi, dan Distribusi Kepercayaan", section_h1))
story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#1e3a8a'), spaceBefore=1, spaceAfter=5))

p2_desc = """
Dari evaluasi menyeluruh 3.000.000 baris data terhadap 5 varian model YOLOv11 diperoleh temuan empiris berikut:<br/>
1. <b>Akurasi Platfom Stabil (~80%):</b> Seluruh varian model menghasilkan tingkat keberhasilan pemetaan homografi antara <b>79,95% hingga 80,015%</b>. Varian <b>Medium</b> mencatatkan keberhasilan tertinggi (480.089 frame valid).<br/>
2. <b>Analisis Sumber Kegagalan:</b> Total ~120.000 frame gagal per varian terbagi merata ke dalam 3 penyebab: <i>Confidence &lt; 0.5 / Kaki Terhalang</i> (~33,4%), <i>Salah Indeks Ankle</i> akibat oklusi silang (~33,3%), dan <i>Objek di luar batas kamera</i> (~33,3%).<br/>
3. <b>Rasionalisasi Pemilihan YOLOv11-Nano untuk Produksi SKELIO:</b> Selisih akurasi Nano hanya terpaut <b>0,055%</b> dari Medium, namun Nano memiliki latensi 4,8x lebih cepat (mencapai 60+ FPS di CPU laptop biasa). Hal ini menjadikannya pilihan optimal untuk pemantauan fitness interaktif real-time.
"""
story.append(Paragraph(p2_desc, body_style))
story.append(Spacer(1, 2))

story.append(Image(chart_path2, width=770, height=170))
story.append(Spacer(1, 4))

sempro_c1 = os.path.join('assets_sempro', 'chart1_fps_vs_accuracy.png')
sempro_c2 = os.path.join('assets_sempro', 'chart2_size_vs_latency.png')
if os.path.exists(sempro_c1) and os.path.exists(sempro_c2):
    story.append(Paragraph("<b>Grafik Komparasi Benchmark Hardware (FPS vs Akurasi & Ukuran vs Latensi):</b>", body_style))
    c_tbl_data = [
        [
            Image(sempro_c1, width=375, height=170),
            Image(sempro_c2, width=375, height=170)
        ]
    ]
    c_tbl = Table(c_tbl_data, colWidths=[385, 385])
    c_tbl.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(c_tbl)

# ================= PAGES 3-7: LAMPIRAN DATA SAMPEL PER SHEET =================
sheet_titles = {
    'Nano': 'YOLOv11-Nano (Edge / Real-Time Production Target)',
    'Small': 'YOLOv11-Small (Balanced CPU Performance)',
    'Medium': 'YOLOv11-Medium (Benchmark Optimal & Akurasi Tertinggi)',
    'Large': 'YOLOv11-Large (High-Precision Server Pipeline)',
    'X-Large': 'YOLOv11-X-Large (Max Theoretical Capacity)'
}

for sheet_idx, sname in enumerate(['Nano', 'Small', 'Medium', 'Large', 'X-Large']):
    story.append(PageBreak())
    story.append(Paragraph(f"3.{sheet_idx+1}. Lampiran Sampel Data Riil: Sheet '{sname}' — {sheet_titles[sname]}", section_h1))
    story.append(Paragraph(f"Menampilkan sampel 25 baris data representatif dari total 600.000 baris data evaluasi pada sheet <b>{sname}</b> (15 sampel Sukses dan 10 sampel Gagal dengan rincian parameter kamera dan koordinat 2D hasil transformasi homografi):", body_style))
    story.append(Spacer(1, 3))
    
    s_data = samples[sname]
    t_rows = [
        [
            Paragraph("<b>File Sumber</b>", tbl_header),
            Paragraph("<b>Status</b>", tbl_header),
            Paragraph("<b>Detail Keterangan</b>", tbl_header),
            Paragraph("<b>Conf L</b>", tbl_header),
            Paragraph("<b>Conf R</b>", tbl_header),
            Paragraph("<b>X Kam L</b>", tbl_header),
            Paragraph("<b>Y Kam L</b>", tbl_header),
            Paragraph("<b>X Kam R</b>", tbl_header),
            Paragraph("<b>Y Kam R</b>", tbl_header),
            Paragraph("<b>X 2D L</b>", tbl_header),
            Paragraph("<b>Y 2D L</b>", tbl_header),
            Paragraph("<b>X 2D R</b>", tbl_header),
            Paragraph("<b>Y 2D R</b>", tbl_header),
        ]
    ]
    
    for r in s_data['rows']:
        fname_short = r[1]
        if len(fname_short) > 28:
            fname_short = fname_short[:25] + "..."
            
        st_badge = Paragraph("SUKSES", badge_sukses) if r[2] == 'Sukses' else Paragraph("GAGAL", badge_gagal)
        
        def fmt_val(v):
            if v is None:
                return "-"
            if isinstance(v, float):
                return f"{v:.1f}"
            return str(v)
            
        t_rows.append([
            Paragraph(f"<font size=5.5>{fname_short}</font>", tbl_cell),
            st_badge,
            Paragraph(f"<font size=6>{r[3]}</font>", tbl_cell),
            Paragraph(f"<font size=6>{fmt_val(r[4])}</font>", tbl_cell_center),
            Paragraph(f"<font size=6>{fmt_val(r[5])}</font>", tbl_cell_center),
            Paragraph(f"<font size=6>{fmt_val(r[6])}</font>", tbl_cell_center),
            Paragraph(f"<font size=6>{fmt_val(r[7])}</font>", tbl_cell_center),
            Paragraph(f"<font size=6>{fmt_val(r[8])}</font>", tbl_cell_center),
            Paragraph(f"<font size=6>{fmt_val(r[9])}</font>", tbl_cell_center),
            Paragraph(f"<font size=6>{fmt_val(r[10])}</font>", tbl_cell_center),
            Paragraph(f"<font size=6>{fmt_val(r[11])}</font>", tbl_cell_center),
            Paragraph(f"<font size=6>{fmt_val(r[12])}</font>", tbl_cell_center),
            Paragraph(f"<font size=6>{fmt_val(r[13])}</font>", tbl_cell_center),
        ])
    
    col_w_sheet = [140, 45, 135, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45]
    table_sheet = Table(t_rows, colWidths=col_w_sheet, repeatRows=1)
    table_sheet.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f8fafc')])
    ]))
    story.append(table_sheet)
    story.append(Spacer(1, 5))
    
    info_box = f"""
    <i>* Catatan Evaluasi Sheet {sname}: Total 600.000 titik frame telah dieksekusi secara batch menggunakan matriks proyeksi perspektif H (3x3). Nilai koordinat 2D merepresentasikan titik proyeksi pada bidang lantai fisik dalam satuan piksel metrik.</i>
    """
    story.append(Paragraph(info_box, body_style))

print("[4/4] Rendering PDF document...")
doc.build(story, canvasmaker=NumberedCanvas)

file_size_bytes = os.path.getsize(pdf_path)
file_size_mb = file_size_bytes / (1024 * 1024)
print(f"SUCCESS! PDF created: {pdf_path}")
print(f"File Size: {file_size_mb:.2f} MB ({file_size_bytes:,} bytes)")
