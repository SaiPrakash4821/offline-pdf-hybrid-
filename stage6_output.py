"""Stage6: PDF report generation (simple)"""
import os, json
from datetime import datetime
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    HAS_REPORTLAB = True
except Exception:
    HAS_REPORTLAB = False


def generate_pdf(summary_text, outpath, title='Summary Report'):
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    if HAS_REPORTLAB:
        try:
            doc = SimpleDocTemplate(outpath, pagesize=A4)
            styles = getSampleStyleSheet()
            elems = []
            for para in summary_text.split('\n'):
                if para.strip():
                    elems.append(Paragraph(para, styles['BodyText']))
                    elems.append(Spacer(1, 6))
            doc.build(elems)
            print('PDF written to', outpath)
            return
        except Exception:
            print('ReportLab PDF generation failed; falling back to plain text file.')

    # fallback: write plain text file with .pdf extension (readers will still open it as text)
    try:
        with open(outpath, 'w', encoding='utf-8') as f:
            f.write(summary_text)
        print('Saved summary as plain text at', outpath)
    except Exception as e:
        print('Failed to save output PDF/text:', e)



# """Stage 6: PDF report generation (formatted and readable)"""
# import os
# from datetime import datetime
# from reportlab.lib.pagesizes import A4
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.lib import colors
# import textwrap

# def generate_pdf(summary_text, outpath, title='Summary Report'):
#     os.makedirs(os.path.dirname(outpath), exist_ok=True)
#     doc = SimpleDocTemplate(outpath, pagesize=A4)
#     styles = getSampleStyleSheet()

#     # 🔧 Improved visual design
#     styles.add(ParagraphStyle(name='Title', fontSize=18, leading=22, alignment=1,
#                               spaceAfter=20, textColor=colors.darkblue))
#     styles.add(ParagraphStyle(name='Body', fontSize=11, leading=18, spaceAfter=12, alignment=4))
#     styles.add(ParagraphStyle(name='Meta', fontSize=9, leading=12, textColor=colors.grey))

#     elems = []
#     elems.append(Paragraph("📘 " + title, styles['Title']))
#     elems.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Meta']))
#     elems.append(Spacer(1, 12))

#     # 🔧 Wrapped paragraphs for better layout
#     for paragraph in textwrap.wrap(summary_text, width=400):
#         elems.append(Paragraph(paragraph.strip(), styles['Body']))
#         elems.append(Spacer(1, 8))

#     doc.build(elems)
#     print(f"✅ PDF successfully written to: {outpath}")

