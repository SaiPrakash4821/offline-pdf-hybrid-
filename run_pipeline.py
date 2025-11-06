# """Run the full pipeline. Usage:
# python run_pipeline.py --pdf path/to/doc.pdf --outdir output --method all
# """
# import os, argparse, json
# from stage1_extraction import extract_pdf, save_extraction
# from stage2_preprocessing import preprocess_from_extraction
# from stage3_summarization import summarize_extractive, summarize_generative, hybrid_summary
# from stage4_selection import save_outputs
# from stage5_postprocess import postprocess
# from stage6_output import generate_pdf

# def run(pdf_path, outdir='output', method='all'):
#     os.makedirs(outdir, exist_ok=True)
#     extracted = extract_pdf(pdf_path)
#     extracted_json = os.path.join(outdir, 'stage1_extracted.json')
#     with open(extracted_json,'w',encoding='utf-8') as f:
#         json.dump(extracted, f, indent=2, ensure_ascii=False)
#     preproc = preprocess_from_extraction(extracted_json, outpath=os.path.join(outdir,'stage2_preprocessed.json'))
#     if method in ('extractive','all'):
#         ext = summarize_extractive(preproc, budget_words=250)
#         with open(os.path.join(outdir,'summary_extractive.txt'),'w',encoding='utf-8') as f: f.write(ext)
#         generate_pdf(ext, os.path.join(outdir,'summary_extractive.pdf'), title='Extractive Summary')
#     if method in ('generative','all'):
#         try:
#             gen_t5 = summarize_generative(preproc, model_name='t5-small')
#             with open(os.path.join(outdir,'summary_generative_t5.txt'),'w',encoding='utf-8') as f: f.write(gen_t5)
#             generate_pdf(gen_t5, os.path.join(outdir,'summary_generative_t5.pdf'), title='Generative T5 Summary')
#         except Exception as e:
#             print('T5 generation failed:', e)
#         try:
#             gen_bart = summarize_generative(preproc, model_name='facebook/bart-large-cnn')
#             with open(os.path.join(outdir,'summary_generative_bart.txt'),'w',encoding='utf-8') as f: f.write(gen_bart)
#             generate_pdf(gen_bart, os.path.join(outdir,'summary_generative_bart.pdf'), title='Generative BART Summary')
#         except Exception as e:
#             print('BART generation failed:', e)
#     if method in ('hybrid','all'):
#         try:
#             ext, g_t5, g_bart, final = hybrid_summary(preproc)
#             with open(os.path.join(outdir,'summary_hybrid.txt'),'w',encoding='utf-8') as f: f.write(final)
#             generate_pdf(final, os.path.join(outdir,'summary_hybrid.pdf'), title='Hybrid Summary')
#         except Exception as e:
#             print('Hybrid failed:', e)
#     print('Pipeline finished. Outputs in', outdir)

# if __name__=='__main__':
#     parser = argparse.ArgumentParser()
#     parser.add_argument('--pdf', required=True)
#     parser.add_argument('--outdir', default='output')
#     parser.add_argument('--method', choices=['extractive','generative','hybrid','all'], default='all')
#     args = parser.parse_args()
#     run(args.pdf, outdir=args.outdir, method=args.method)


"""
Run the Hybrid PDF Summarizer Pipeline.
Usage:
    # For a single PDF
    python run_pipeline.py --pdf path/to/doc.pdf --outdir output --method hybrid

    # For an entire folder of PDFs
    python run_pipeline.py --folder path/to/folder --outdir output --method hybrid
"""

import os
import argparse
import json
from pathlib import Path
from stage1_extraction import extract_pdf
from stage2_preprocessing import preprocess_from_extraction
#from stage3_summarization import hybrid_summary
from stage6_output import generate_pdf
from stage3_summarization import summarize_extractive, summarize_generative, hybrid_summary


def run_single(pdf_path, outdir='output'):
    """Run hybrid summarization for one PDF."""
    os.makedirs(outdir, exist_ok=True)
    print(f"\nProcessing: {pdf_path}")

    # Stage 1 – Extraction
    extracted = extract_pdf(pdf_path)
    extracted_json = os.path.join(outdir, f"{Path(pdf_path).stem}_stage1.json")
    with open(extracted_json, 'w', encoding='utf-8') as f:
        json.dump(extracted, f, indent=2, ensure_ascii=False)

    # Stage 2 – Preprocessing
    preproc = preprocess_from_extraction(extracted_json, outpath=os.path.join(outdir, f"{Path(pdf_path).stem}_stage2.json"))

    # Stage 3 – Hybrid Summarization
    try:
        ext, g_t5, g_bart, final = hybrid_summary(preproc)
        txt_path = os.path.join(outdir, f"summary_{Path(pdf_path).stem}_hybrid.txt")
        pdf_path_out = os.path.join(outdir, f"summary_{Path(pdf_path).stem}_hybrid.pdf")

        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(final)
        generate_pdf(final, pdf_path_out, title=f"Hybrid Summary - {Path(pdf_path).stem}")
        print(f"✅ Summary saved to {pdf_path_out}")
    except Exception as e:
        print(f"❌ Hybrid summarization failed for {pdf_path}: {e}")


def run_folder(folder_path, outdir='output'):
    """Run hybrid summarization for all PDFs in a folder."""
    folder_path = Path(folder_path)
    pdf_files = list(folder_path.rglob("*.pdf"))
    if not pdf_files:
        print("⚠️ No PDF files found.")
        return
    print(f"🔍 Found {len(pdf_files)} PDF files in {folder_path}")
    for pdf_file in pdf_files:
        run_single(str(pdf_file), outdir)
    print(f"\n✅ All summaries saved in: {outdir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdf', help='Path to a single PDF')
    parser.add_argument('--folder', help='Path to a folder containing PDFs')
    parser.add_argument('--outdir', default='output', help='Output directory')
    parser.add_argument('--method', choices=['hybrid'], default='hybrid', help='Only hybrid is supported here')
    args = parser.parse_args()

    if args.folder:
        run_folder(args.folder, outdir=args.outdir)
    elif args.pdf:
        run_single(args.pdf, outdir=args.outdir)
    else:
        print("⚠️ Please specify either --pdf or --folder")



# """
# Hybrid Folder Summarizer – Combine all PDF summaries into one file
# Usage:
# python run_pipeline.py --folder "path/to/folder" --outdir output
# """

# import os
# import argparse
# import json
# from pathlib import Path
# from stage1_extraction import extract_pdf
# from stage2_preprocessing import preprocess_from_extraction
# from stage3_summarization import hybrid_summary
# from stage6_output import generate_pdf

# def summarize_pdf(pdf_path, temp_dir):
#     """Run hybrid summary for one PDF and return the text summary."""
#     extracted = extract_pdf(pdf_path)
#     extracted_json = os.path.join(temp_dir, f"{Path(pdf_path).stem}_stage1.json")
#     with open(extracted_json, 'w', encoding='utf-8') as f:
#         json.dump(extracted, f, indent=2, ensure_ascii=False)

#     preproc = preprocess_from_extraction(extracted_json, outpath=os.path.join(temp_dir, f"{Path(pdf_path).stem}_stage2.json"))

#     try:
#         ext, g_t5, g_bart, final = hybrid_summary(preproc)
#         clean_summary = final.strip().replace("\n\n", "\n")
#         return clean_summary
#     except Exception as e:
#         print(f"❌ Failed summarizing {pdf_path}: {e}")
#         return ""

# def summarize_folder(folder_path, outdir):
#     """Summarize all PDFs in a folder and combine results into one PDF."""
#     folder_path = Path(folder_path)
#     outdir = Path(outdir)
#     outdir.mkdir(parents=True, exist_ok=True)

#     pdf_files = list(folder_path.rglob("*.pdf"))
#     if not pdf_files:
#         print("⚠️ No PDF files found in folder.")
#         return

#     combined_summary = ""
#     print(f"🔍 Found {len(pdf_files)} PDF files. Summarizing...")

#     temp_dir = outdir / "temp"
#     temp_dir.mkdir(exist_ok=True)

#     for i, pdf in enumerate(pdf_files, start=1):
#         print(f"[{i}/{len(pdf_files)}] Summarizing {pdf.name}")
#         summary_text = summarize_pdf(str(pdf), temp_dir)
#         if summary_text:
#             combined_summary += f"\n\n--- Summary of {pdf.name} ---\n\n{summary_text}\n"

#     combined_summary = combined_summary.strip()

#     if combined_summary:
#         final_pdf_path = outdir / "combined_hybrid_summary.pdf"
#         generate_pdf(combined_summary, str(final_pdf_path), title="Combined Hybrid Summary")
#         print(f"\n✅ Combined summary saved to: {final_pdf_path}")
#     else:
#         print("⚠️ No summaries were generated.")

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser()
#     parser.add_argument("--folder", required=True, help="Path to folder with PDFs")
#     parser.add_argument("--outdir", default="output", help="Output directory")
#     args = parser.parse_args()

#     summarize_folder(args.folder, args.outdir)



