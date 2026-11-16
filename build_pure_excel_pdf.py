import openpyxl
import time
import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas

t0 = time.time()
print("[1/3] Loading evaluasi_homografi_fitness_3juta.xlsx (240 MB)...")
wb = openpyxl.load_workbook('evaluasi_homografi_fitness_3juta.xlsx', read_only=True)
print(f"Loaded workbook in {time.time()-t0:.2f}s. Sheets: {wb.sheetnames}")

# Target PDF
pdf_path = "evaluasi_homografi_fitness_3juta_spreadsheet.pdf"

# Numbered canvas for Excel-like header and footer
class ExcelCanvas(canvas.Canvas):
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
            self.draw_excel_header_footer(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_excel_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(colors.HexColor("#107C41"))
        
        # Header (Top)
        self.drawString(20, 576, "MICROSOFT EXCEL — evaluasi_homografi_fitness_3juta.xlsx")
        self.setFont("Helvetica", 7)
        self.setFillColor(colors.HexColor("#5f6368"))
        self.drawRightString(822, 576, "SKELIO AI BIOMECHANICS & HOMOGRAPHY EVALUATION")
        self.setStrokeColor(colors.HexColor("#107C41"))
        self.setLineWidth(1.0)
        self.line(20, 570, 822, 570)
        
        # Footer (Bottom)
        self.setStrokeColor(colors.HexColor("#dadce0"))
        self.setLineWidth(0.5)
        self.line(20, 22, 822, 22)
        self.drawString(20, 13, "Spreadsheet Data Export | Evaluasi Homografi Fitness")
        self.drawRightString(822, 13, f"Halaman {self._pageNumber} dari {page_count}")
        self.restoreState()


doc = SimpleDocTemplate(
    pdf_path,
    pagesize=landscape(A4),
    leftMargin=20,
    rightMargin=20,
    topMargin=32,
    bottomMargin=28
)

story = []

# Styles
sheet_title_style = ParagraphStyle(
    'SheetHeader',
    fontName='Helvetica-Bold',
    fontSize=10,
    leading=12,
    textColor=colors.HexColor('#107C41'),
    spaceBefore=4,
    spaceAfter=4
)

# 14 Column widths for landscape A4 (usable width = 842 - 40 = 802 pt)
col_w = [45, 145, 45, 115, 42, 42, 46, 46, 46, 46, 46, 46, 46, 46]

total_rows_compiled = 0
ROWS_PER_SHEET = 5000  # 5,000 rows per sheet * 5 sheets = 25,000 rows

print(f"[2/3] Extracting {ROWS_PER_SHEET} rows per sheet and generating Excel grid tables...")

for s_idx, sname in enumerate(wb.sheetnames):
    ws = wb[sname]
    t_sheet_start = time.time()
    sheet_data = []
    
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            header_row = [str(c) if c is not None else '' for c in row]
            sheet_data.append(header_row)
            continue
            
        r_clean = []
        for c_idx, c in enumerate(row):
            if c is None:
                r_clean.append('-')
            elif isinstance(c, float):
                r_clean.append(f"{c:.1f}" if abs(c) > 1 else f"{c:.2f}")
            else:
                r_clean.append(str(c))
        sheet_data.append(r_clean)
        
        if len(sheet_data) >= ROWS_PER_SHEET + 1:
            break
            
    rows_in_this_sheet = len(sheet_data) - 1
    total_rows_compiled += rows_in_this_sheet
    print(f"  -> Sheet '{sname}': {rows_in_this_sheet} rows extracted in {time.time()-t_sheet_start:.2f}s")
    
    # Build Table
    t = Table(sheet_data, colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 5.5),
        ('LEADING', (0,0), (-1,-1), 7),
        ('GRID', (0,0), (-1,-1), 0.25, colors.HexColor('#d0d7de')),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#107C41')), # Excel Header Green
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.2),
        ('TOPPADDING', (0,0), (-1,-1), 1.2),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
        ('ALIGN', (2,0), (-1,-1), 'CENTER'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8f9fa')])
    ]))
    
    if s_idx > 0:
        story.append(PageBreak())
        
    story.append(Paragraph(f"<b>[Worksheet: {sname}]</b> — <code>evaluasi_homografi_fitness_3juta.xlsx</code> (Menampilkan {rows_in_this_sheet:,} Baris Data)", sheet_title_style))
    story.append(t)

wb.close()

print("[3/3] Building PDF document...")
doc.build(story, canvasmaker=ExcelCanvas)

file_size_bytes = os.path.getsize(pdf_path)
file_size_mb = file_size_bytes / (1024 * 1024)
print(f"SUCCESS! Output: {pdf_path}")
print(f"Total compiled rows: {total_rows_compiled:,} rows")
print(f"File size: {file_size_mb:.2f} MB ({file_size_bytes:,} bytes)")
print(f"Total process time: {time.time()-t0:.2f}s")
