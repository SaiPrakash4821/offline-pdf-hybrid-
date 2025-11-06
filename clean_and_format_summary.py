#!/usr/bin/env python3
"""Clean and format a generated summary into a readable ~100-word paragraph.

Heuristics used:
- remove (cid:###) artifacts
- redact emails
- split camelCase / joined words by inserting spaces between lower->Upper
- split letters/digits boundaries
- normalize whitespace and punctuation
"""
import re
import argparse
import os


def clean_text(s):
    if not s:
        return ''
    # remove OCR (cid:###) artifacts
    s = re.sub(r"\(cid:\d+\)", ' ', s)
    # redact emails
    s = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", '[REDACTED]', s)
    # split lowerUpper -> lower Upper
    s = re.sub(r'([a-z])([A-Z])', r'\1 \2', s)
    # split letter-digit and digit-letter
    s = re.sub(r'([A-Za-z])([0-9])', r'\1 \2', s)
    s = re.sub(r'([0-9])([A-Za-z])', r'\1 \2', s)
    # add spaces after commas/periods if missing
    s = re.sub(r'([.,;:!?])(\w)', r'\1 \2', s)
    # collapse multiple punctuation
    s = re.sub(r'[\s]{2,}', ' ', s)
    # remove stray non-printable or weird chars
    s = re.sub(r'[^\x00-\x7F]+', ' ', s)
    s = s.strip()
    return s


def to_paragraph(s, target=100):
    cleaned = clean_text(s)
    if not cleaned:
        return ''
    words = cleaned.split()
    # limit to target words
    words = words[:target]
    para = ' '.join(words)
    # ensure sentences end properly: add a period if last char isn't punctuation
    if para and para[-1] not in '.!?':
        para = para.rstrip('.,;:') + '.'
    # capitalize first character
    para = para[0].upper() + para[1:]
    # tidy spacing around punctuation
    para = re.sub(r'\s+([.,;:!?])', r'\1', para)
    para = re.sub(r'\s{2,}', ' ', para)
    return para


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--in', dest='infile', required=True)
    parser.add_argument('--out', dest='outfile', default='output/summary_100words_clean.txt')
    parser.add_argument('--target', type=int, default=100)
    args = parser.parse_args()

    if not os.path.exists(args.infile):
        print('Input file not found:', args.infile)
        return
    with open(args.infile, 'r', encoding='utf-8') as f:
        txt = f.read()

    para = to_paragraph(txt, target=args.target)
    os.makedirs(os.path.dirname(args.outfile), exist_ok=True)
    with open(args.outfile, 'w', encoding='utf-8') as f:
        f.write(para)

    print('\n--- Cleaned ~100-word paragraph ---\n')
    print(para)
    print('\nSaved to:', args.outfile)


if __name__ == '__main__':
    main()
