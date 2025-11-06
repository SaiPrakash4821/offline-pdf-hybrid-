"""Stage 1: Multi-engine PDF extraction with OCR fallback."""

import os, re, json
try:
    import fitz
except Exception:
    fitz = None
try:
    import pdfplumber
except Exception:
    pdfplumber = None
from PyPDF2 import PdfReader
from pdfminer.high_level import extract_text as pdfminer_extract
from pdf2image import convert_from_path
import pytesseract
try:
    import camelot
except Exception:
    camelot = None
try:
    import tabula
except Exception:
    tabula = None


def fix_text_formatting(text: str) -> str:
    if not text:
        return ''
    text = re.sub(r'-\\n\\s*', '', text)
    text = re.sub(r'(?<!\\n)\\n(?!\\n)', ' ', text)
    text = re.sub(r'\\n{2,}', '\\\\n\\\\n', text)
    return text.strip()


def extract_text_pymupdf(path, page_number):
    if not fitz:
        return ''
    try:
        doc = fitz.open(path)
        page = doc.load_page(page_number)
        text = page.get_text('text')
        doc.close()
        return text or ''
    except Exception:
        return ''


def extract_text_pdfplumber(path, page_number):
    if not pdfplumber:
        return ''
    try:
        with pdfplumber.open(path) as pdf:
            page = pdf.pages[page_number]
            return page.extract_text() or ''
    except Exception:
        return ''


def extract_text_pypdf2(path, page_number):
    try:
        reader = PdfReader(path)
        return reader.pages[page_number].extract_text() or ''
    except Exception:
        return ''


def extract_text_pdfminer(path, page_number):
    try:
        return pdfminer_extract(path, page_numbers=[page_number]) or ''
    except Exception:
        return ''


# def ocr_page(path, page_number, dpi=300, lang='eng'):
#     try:
#         images = convert_from_path(path, dpi=dpi, first_page=page_number+1, last_page=page_number+1)
#         if images:
#             text = pytesseract.image_to_string(images[0], lang=lang)
#             return text or ''
#     except Exception:
#         return ''
#     return ''
from pdf2image import convert_from_path
import pytesseract

def ocr_page(path, page_number, dpi=300, lang="eng"):
    """Convert a PDF page to text using OCR when normal extraction fails."""
    try:
        images = convert_from_path(path, dpi=dpi, first_page=page_number + 1, last_page=page_number + 1)
        text = pytesseract.image_to_string(images[0], lang=lang)
        return text
    except Exception as e:
        print(f"OCR failed on page {page_number+1}: {e}")
        return ""



def extract_tables_camelot(path, page_num):
    if not camelot:
        return []
    try:
        tables = camelot.read_pdf(path, pages=str(page_num+1), flavor='stream')
        return [t.df.to_csv(index=False) for t in tables]
    except Exception:
        return []


def extract_tables_tabula(path, page_num):
    if not tabula:
        return []
    try:
        tables = tabula.read_pdf(path, pages=page_num+1, multiple_tables=True)
        csvs = []
        for t in tables:
            try:
                csvs.append(t.to_csv(index=False))
            except Exception:
                pass
        return csvs
    except Exception:
        return []


def extract_pdf(path: str):
    print(f'Processing: {path}')
    out = {'file': os.path.basename(path), 'pages': []}
    page_count = None
    if fitz:
        try:
            doc = fitz.open(path)
            page_count = doc.page_count
            doc.close()
        except Exception:
            page_count = None
    if page_count is None:
        try:
            reader = PdfReader(path)
            page_count = len(reader.pages)
        except Exception:
            page_count = 0
    for i in range(page_count):
        text = extract_text_pymupdf(path, i) or extract_text_pdfplumber(path, i) or extract_text_pypdf2(path, i) or extract_text_pdfminer(path, i)
        is_scanned = False
        if not text or len(text.strip()) < 50:
            #text = ocr_page(path, i)
            is_scanned = True
        text = fix_text_formatting(text)
        tables = extract_tables_camelot(path, i) or extract_tables_tabula(path, i)
        out['pages'].append({'page': i+1, 'is_scanned': is_scanned, 'text': text, 'tables': tables})
    return out


def save_extraction(result, outdir='output'):
    os.makedirs(outdir, exist_ok=True)
    base = os.path.splitext(result['file'])[0]
    txt_path = os.path.join(outdir, base + '_extracted.txt')
    with open(txt_path, 'w', encoding='utf-8') as f:
        for p in result['pages']:
            f.write(f"\\n=== PAGE {p['page']} (Scanned: {p['is_scanned']}) ===\\n")
            f.write(p['text'] + '\\n')
    json_path = os.path.join(outdir, base + '_extracted.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    table_dir = os.path.join(outdir, base + '_tables')
    os.makedirs(table_dir, exist_ok=True)
    for p in result['pages']:
        for tidx, t in enumerate(p['tables'], start=1):
            try:
                path = os.path.join(table_dir, f'page{p["page"]}_table{tidx}.csv')
                with open(path, 'w', encoding='utf-8') as tf:
                    tf.write(t)
            except Exception:
                pass
    print('Extraction saved to', outdir)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdf', required=True, help='PDF path')
    parser.add_argument('--out', default='output', help='Output dir')
    args = parser.parse_args()
    res = extract_pdf(args.pdf)
    save_extraction(res, args.out)
