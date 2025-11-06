"""Stage 2: Preprocessing (normalization, tokenization, lemmatization, embeddings)"""
import os, re, json, unicodedata
try:
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.stem import WordNetLemmatizer
    from nltk.corpus import stopwords
    NLTK_AVAILABLE = True
except Exception:
    # fallback simple tokenizers
    NLTK_AVAILABLE = False
    def sent_tokenize(text):
        import re
        return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    def word_tokenize(s):
        return [w for w in re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", s)]
    class WordNetLemmatizer:
        def lemmatize(self, w):
            return w
    def stopwords():
        return set()
try:
    from sentence_transformers import SentenceTransformer
    EMB = True
except Exception:
    EMB = False

import nltk
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
except Exception:
    pass

lemmatizer = WordNetLemmatizer()
try:
    stop_words = set(stopwords.words('english')) if NLTK_AVAILABLE else set()
except Exception:
    stop_words = set()
embed_model = SentenceTransformer('all-MiniLM-L6-v2') if EMB else None

def normalize_unicode(text):
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r'\\s+', ' ', text).strip()
    return text

def clean_ocr_artifacts(text):
    repl = {'ﬁ':'fi','ﬂ':'fl','“':'"','”':'"','‘':"'",'’':"'"}
    for k,v in repl.items():
        text = text.replace(k,v)
    return text

def preprocess_from_extraction(json_path, outpath=None):
    with open(json_path,'r',encoding='utf-8') as f:
        data = json.load(f)
    all_sentences = []
    pages = data.get('pages',[])
    for p in pages:
        txt = p.get('text','') or ''
        txt = normalize_unicode(clean_ocr_artifacts(txt))
        try:
            sents = sent_tokenize(txt)
        except Exception:
            # naive split
            sents = [s.strip() for s in txt.split('.') if s.strip()]
        for si, s in enumerate(sents):
            try:
                words = [w for w in word_tokenize(s.lower()) if w.isalpha() and w not in stop_words]
            except Exception:
                words = [w for w in s.lower().split() if w.isalpha() and w not in stop_words]
            try:
                lemmas = ' '.join([lemmatizer.lemmatize(w) for w in words])
            except Exception:
                lemmas = ' '.join(words)
            entry = {'page': p.get('page'), 'sent_idx': si, 'orig': s, 'clean': ' '.join(words), 'lemmas_joined': lemmas}
            all_sentences.append(entry)
    out = {'file': data.get('file'), 'pages': [{'page':p.get('page'), 'sentences': []} for p in pages], 'sentences': all_sentences}
    if outpath:
        with open(outpath,'w',encoding='utf-8') as f:
            json.dump(out,f,indent=2,ensure_ascii=False)
    return out

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--injson', required=True)
    parser.add_argument('--out', default='stage2_preprocessed.json')
    args = parser.parse_args()
    preprocess_from_extraction(args.injson, outpath=args.out)


# """Stage 2: Preprocessing (normalization, tokenization, lemmatization, embeddings)"""
# import os, re, json, unicodedata
# from nltk.tokenize import sent_tokenize, word_tokenize
# from nltk.stem import WordNetLemmatizer
# from nltk.corpus import stopwords
# try:
#     from sentence_transformers import SentenceTransformer
#     EMB = True
# except Exception:
#     EMB = False

# import nltk
# nltk.download('punkt', quiet=True)
# nltk.download('stopwords', quiet=True)
# nltk.download('wordnet', quiet=True)

# lemmatizer = WordNetLemmatizer()
# stop_words = set(stopwords.words('english'))
# embed_model = SentenceTransformer('all-MiniLM-L6-v2') if EMB else None


# # ----------------------------------------------------
# # 🔧 Improved normalization and cleaning functions
# # ----------------------------------------------------
# def normalize_unicode(text):
#     text = unicodedata.normalize('NFKC', text)
#     text = re.sub(r'\s+', ' ', text).strip()
#     return text


# def clean_ocr_artifacts(text):
#     repl = {'ﬁ':'fi','ﬂ':'fl','“':'"','”':'"','‘':"'",'’':"'"}
#     for k,v in repl.items():
#         text = text.replace(k,v)
#     return text


# def advanced_cleaning(text):
#     """Extra cleaning for resumes and scanned PDFs"""
#     ### 🔧 Remove weird encoded characters
#     text = re.sub(r'\(cid:[0-9]+\)', ' ', text)       # remove (cid:123)
#     text = re.sub(r'[^\x00-\x7F]+', ' ', text)        # remove non-ASCII
#     ### 🔧 Separate merged words like 'MachineLearning' → 'Machine Learning'
#     text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
#     ### 🔧 Remove section headers (common in resumes)
#     text = re.sub(r'\b(SKILLS|PROJECTS|EDUCATION|SUMMARY|EXPERIENCE|CERTIFICATIONS)\b', ' ', text, flags=re.I)
#     text = re.sub(r'\s+', ' ', text).strip()
#     return text
# # ----------------------------------------------------


# def preprocess_from_extraction(json_path, outpath=None):
#     with open(json_path,'r',encoding='utf-8') as f:
#         data = json.load(f)
#     all_sentences = []
#     pages = data.get('pages',[])

#     for p in pages:
#         txt = p.get('text','') or ''
#         ### 🔧 Apply all cleaning layers
#         txt = normalize_unicode(clean_ocr_artifacts(advanced_cleaning(txt)))

#         sents = sent_tokenize(txt)
#         for si, s in enumerate(sents):
#             words = [w for w in word_tokenize(s.lower()) if w.isalpha() and w not in stop_words]
#             lemmas = ' '.join([lemmatizer.lemmatize(w) for w in words])
#             entry = {
#                 'page': p.get('page'),
#                 'sent_idx': si,
#                 'orig': s,
#                 'clean': ' '.join(words),
#                 'lemmas_joined': lemmas
#             }
#             all_sentences.append(entry)

#     out = {
#         'file': data.get('file'),
#         'pages': [{'page':p.get('page'), 'sentences': []} for p in pages],
#         'sentences': all_sentences
#     }

#     if outpath:
#         with open(outpath,'w',encoding='utf-8') as f:
#             json.dump(out,f,indent=2,ensure_ascii=False)

#     return out


# if __name__ == '__main__':
#     import argparse
#     parser = argparse.ArgumentParser()
#     parser.add_argument('--injson', required=True)
#     parser.add_argument('--out', default='stage2_preprocessed.json')
#     args = parser.parse_args()
#     preprocess_from_extraction(args.injson, outpath=args.out)
