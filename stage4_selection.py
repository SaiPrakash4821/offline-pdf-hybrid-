"""Stage4: selection (simple saving of candidate sentences)"""
import os, json
try:
    from fpdf import FPDF
    HAS_FPDF = True
except Exception:
    HAS_FPDF = False


def save_outputs(selected, outdir='output', base='final_summary'):
    """Save selected items. `selected` can be a list of dicts with 'text' or a list of strings."""
    os.makedirs(outdir, exist_ok=True)
    # normalize to list of strings
    txt_items = []
    for s in selected:
        if isinstance(s, dict):
            t = s.get('text') or s.get('orig') or s.get('summary') or ''
            txt_items.append(t)
        else:
            txt_items.append(str(s))
    txt = '\n'.join(txt_items)
    with open(os.path.join(outdir, base + '.txt'), 'w', encoding='utf-8') as f:
        f.write(txt)
    with open(os.path.join(outdir, base + '.json'), 'w', encoding='utf-8') as f:
        json.dump(selected, f, indent=2, ensure_ascii=False)
    if HAS_FPDF:
        try:
            pdf = FPDF(); pdf.add_page(); pdf.set_font('Arial', size=12); pdf.multi_cell(0, 8, txt); pdf.output(os.path.join(outdir, base + '.pdf'))
        except Exception:
            print('Could not write PDF with FPDF, saved TXT/JSON only.')
    else:
        print('FPDF not available; saved TXT and JSON only.')
    print('Stage4 outputs saved to', outdir)
