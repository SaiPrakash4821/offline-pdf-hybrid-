#!/usr/bin/env python3
"""Generate a human-like ~100-word paragraph from an existing stage2_preprocessed.json.

This script avoids heavy ML deps and uses a heuristic to pick diverse sentences
from the preprocessed JSON produced by `stage2_preprocessing.py`.
"""
import json
import os
import argparse


def find_preprocessed(default_paths=None):
    if default_paths is None:
        default_paths = [
            'output_extractive/stage2_preprocessed.json',
            'output_generative/stage2_preprocessed.json',
            'output/stage2_preprocessed.json',
            'stage2_preprocessed.json',
        ]
    for p in default_paths:
        if os.path.exists(p):
            return p
    return None


def load_sentences(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    sents = []
    for s in data.get('sentences', []):
        t = s.get('orig') or s.get('clean') or ''
        t = t.strip()
        if t:
            sents.append(t)
    # fallback: try pages -> texts
    if not sents:
        for p in data.get('pages', []):
            text = p.get('text','') or ''
            for line in text.split('\n'):
                line = line.strip()
                if len(line.split()) >= 5:
                    sents.append(line)
    return sents


def build_100_word_paragraph(sentences, target=100):
    if not sentences:
        return ''
    n = len(sentences)
    # choose diverse indices across the document
    picks = []
    stride = max(1, n // 8)
    idx = 0
    while idx < n and len(picks) < 12:
        picks.append(idx)
        idx += stride

    # ensure we also consider some early/late sentences
    picks += [0, n//2, max(0, n-1)]
    # unique and bounded
    picks = sorted(set([min(max(0, i), n-1) for i in picks]))

    selected = []
    total_words = 0
    for i in picks:
        s = sentences[i].strip()
        # clean whitespace
        s = ' '.join(s.split())
        # ensure punctuation
        if not s.endswith(('.', '!', '?')):
            s = s + '.'
        words = len(s.split())
        if total_words + words > target:
            # take only necessary words to reach target
            needed = target - total_words
            if needed <= 0:
                break
            parts = s.split()
            snippet = ' '.join(parts[:max(1, needed)])
            if not snippet.endswith(('.', '!', '?')):
                snippet = snippet.rstrip('.,') + '...'
            selected.append(snippet)
            total_words += len(snippet.split())
            break
        selected.append(s)
        total_words += words
        if total_words >= target:
            break

    # if still short, append subsequent sentences
    if total_words < target:
        for s in sentences:
            if s in selected:
                continue
            ss = s.strip()
            if not ss.endswith(('.', '!', '?')):
                ss = ss + '.'
            words = len(ss.split())
            if total_words + words > target:
                needed = target - total_words
                parts = ss.split()
                snippet = ' '.join(parts[:max(1, needed)])
                if not snippet.endswith(('.', '!', '?')):
                    snippet = snippet.rstrip('.,') + '...'
                selected.append(snippet)
                total_words += len(snippet.split())
                break
            selected.append(ss)
            total_words += words
            if total_words >= target:
                break

    # Final postprocessing: ensure sentences are capitalized and form a paragraph
    final_sents = []
    for s in selected:
        s = s.strip()
        if not s:
            continue
        s = s[0].upper() + s[1:]
        final_sents.append(s)

    para = ' '.join(final_sents)
    # clean double spaces
    para = ' '.join(para.split())
    return para


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--in', dest='injson', help='Path to stage2_preprocessed.json')
    parser.add_argument('--out', dest='outpath', default='output/summary_100words.txt')
    parser.add_argument('--target', type=int, default=100, help='Target word count (approx)')
    args = parser.parse_args()

    inpath = args.injson or find_preprocessed()
    if not inpath:
        print('No preprocessed JSON found. Run stage2 or provide --in path to stage2_preprocessed.json')
        return

    sentences = load_sentences(inpath)
    para = build_100_word_paragraph(sentences, target=args.target)
    if not para:
        print('Could not build a summary from the provided file.')
        return

    os.makedirs(os.path.dirname(args.outpath), exist_ok=True)
    with open(args.outpath, 'w', encoding='utf-8') as f:
        f.write(para)

    print('\n--- 100-word paragraph (approx) ---\n')
    print(para)
    print('\nSaved to:', args.outpath)


if __name__ == '__main__':
    main()
