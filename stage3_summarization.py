"""Stage 3: Summarization (extractive, generative (t5/bart), hybrid)"""
import os, json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx
from fpdf import FPDF

try:
    from transformers import pipeline
    TRANS = True
except Exception:
    TRANS = False

# sentence-transformers is optional; if unavailable we'll fall back to TF-IDF/textrank only
try:
    from sentence_transformers import SentenceTransformer, util
    EMB = True
except Exception:
    EMB = False

def load_json(path):
    with open(path,'r',encoding='utf-8') as f:
        return json.load(f)

def save_json(obj,path):
    with open(path,'w',encoding='utf-8') as f:
        json.dump(obj,f,indent=2,ensure_ascii=False)

def save_pdf(text,outpath,title=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial',size=12)
    if title:
        pdf.set_font('Arial','B',14)
        pdf.multi_cell(0,8,title)
        pdf.ln(4)
        pdf.set_font('Arial',size=12)
    pdf.multi_cell(0,8,text)
    pdf.output(outpath)

def flatten(prep_json):
    return prep_json.get('sentences',[])

def build_tfidf(sent_texts):
    vec = TfidfVectorizer(max_df=0.85, min_df=1)
    mat = vec.fit_transform(sent_texts)
    return vec, mat

def textrank_scores(tfidf):
    sim = cosine_similarity(tfidf)
    np.fill_diagonal(sim,0)
    G = nx.from_numpy_array(sim)
    try:
        pr = nx.pagerank(G)
    except Exception:
        pr = {i: float(sim[i].sum()) for i in range(sim.shape[0])}
    return pr

# def summarize_extractive(prep_json, budget_words=200):
#     sents = flatten(prep_json)
#     texts = [s['lemmas_joined'] for s in sents]
#     origs = [s['orig'] for s in sents]
#     if not texts:
#         return ''
#     vec, tfidf = build_tfidf(texts)
#     scores = np.asarray(tfidf.sum(axis=1)).reshape(-1)
#     ranked = list(np.argsort(scores)[::-1])
#     pr = textrank_scores(tfidf)
#     ranked_pr = [idx for idx,_ in sorted(pr.items(), key=lambda x:x[1], reverse=True)]
#     pool = list(dict.fromkeys(ranked[:10] + ranked_pr[:10]))
#     selected = []
#     words = 0
#     for idx in sorted(pool):
#         s = origs[idx]
#         l = len(s.split())
#         if words + l > budget_words:
#             break
#         selected.append(s)
#         words += l
#     return '\n'.join(selected)


import numpy as np


def summarize_extractive(prep_json, budget_words=200):
    """
    Enhanced extractive summarizer combining TF-IDF, TextRank, and semantic similarity.
    Produces smoother, more meaningful summaries.
    """
    sents = flatten(prep_json)
    texts = [s['lemmas_joined'] for s in sents]
    origs = [s['orig'] for s in sents]
    if not texts:
        return ''
    
    # --- 1️⃣ TF-IDF scoring ---
    vec, tfidf = build_tfidf(texts)
    tfidf_scores = np.asarray(tfidf.sum(axis=1)).reshape(-1)
    
    # --- 2️⃣ TextRank scoring ---
    pr = textrank_scores(tfidf)
    textrank_sorted = [idx for idx, _ in sorted(pr.items(), key=lambda x: x[1], reverse=True)]
    
    # --- 3️⃣ Semantic coherence (SentenceTransformer) (optional) ---
    # Only enable embedding-based semantic scores when explicitly allowed.
    # This avoids automatic HF model downloads and long waits when sentence-transformers is installed.
    import os
    enable_emb = os.environ.get('ENABLE_EMBEDDINGS', '0') == '1'
    if EMB and enable_emb and len(texts) > 0:
        try:
            embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            embeddings = embedding_model.encode(texts, convert_to_tensor=True)
            doc_embedding = embeddings.mean(dim=0, keepdim=True)
            semantic_scores = util.cos_sim(embeddings, doc_embedding).cpu().numpy().flatten()
        except Exception:
            semantic_scores = np.zeros(len(texts))
    else:
        semantic_scores = np.zeros(len(texts))
    
    # --- 4️⃣ Combine all 3 scores (weighted average) ---
    # If semantic scores are all zeros (no embedding available) adjust weights
    pr_array = np.array([pr.get(i, 0) for i in range(len(texts))])
    if semantic_scores.sum() == 0:
        combined_scores = (0.6 * tfidf_scores) + (0.4 * pr_array)
    else:
        combined_scores = (0.4 * tfidf_scores) + (0.3 * semantic_scores) + (0.3 * pr_array)
    ranked = list(np.argsort(combined_scores)[::-1])
    
    # --- 5️⃣ Select top sentences (respecting word budget) ---
    selected, total_words = [], 0
    for idx in ranked:
        sent = origs[idx]
        word_count = len(sent.split())
        if total_words + word_count > budget_words:
            break
        selected.append(sent)
        total_words += word_count
    
    # --- 6️⃣ Return coherent summary ---
    summary = ' '.join(selected)
    return summary


def summarize_generative(prep_json, model_name='t5-small'):
    if not TRANS:
        raise RuntimeError('transformers not installed')
    sents = prep_json.get('sentences',[])
    text = '\n'.join([s.get('orig','') for s in sents])
    summarizer = pipeline('summarization', model=model_name, device=-1)
    out = summarizer(text, max_length=250, min_length=10, do_sample=False)
    return out[0]['summary_text']

def hybrid_summary(prep_json):
    """Hybrid summary: prefer extractive output by default.

    Generative models are only run when the environment variable
    ENABLE_GENERATIVE=1 is set. This avoids long runs or large model downloads
    when transformers are installed but models are not desired.
    """
    import os
    ext = summarize_extractive(prep_json, budget_words=150)
    gen_t5 = ''
    gen_bart = ''
    enable_gen = os.environ.get('ENABLE_GENERATIVE', '0') == '1'
    if enable_gen and TRANS:
        try:
            gen_t5 = summarize_generative(prep_json, model_name='t5-small')
        except Exception:
            gen_t5 = ''
        try:
            gen_bart = summarize_generative(prep_json, model_name='facebook/bart-large-cnn')
        except Exception:
            gen_bart = ''
    final = gen_bart or gen_t5 or ext
    return ext, gen_t5, gen_bart, final

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--in', dest='injson', required=True)
    parser.add_argument('--outdir', default='output')
    parser.add_argument('--budget', type=int, default=200)
    args = parser.parse_args()
    prep = load_json(args.injson)
    os.makedirs(args.outdir, exist_ok=True)
    ext = summarize_extractive(prep, budget_words=args.budget)
    save_json({'summary':ext}, os.path.join(args.outdir,'summary_extractive.json'))
    save_pdf(ext, os.path.join(args.outdir,'summary_extractive.pdf'), title='Extractive Summary')
    if TRANS:
        gen_t5 = summarize_generative(prep, model_name='t5-small')
        save_json({'summary':gen_t5}, os.path.join(args.outdir,'summary_generative_t5.json'))
        save_pdf(gen_t5, os.path.join(args.outdir,'summary_generative_t5.pdf'), title='Generative T5 Summary')
        try:
            gen_bart = summarize_generative(prep, model_name='facebook/bart-large-cnn')
            save_json({'summary':gen_bart}, os.path.join(args.outdir,'summary_generative_bart.json'))
            save_pdf(gen_bart, os.path.join(args.outdir,'summary_generative_bart.pdf'), title='Generative BART Summary')
        except Exception:
            pass
        ext, g_t5, g_bart, final = hybrid_summary(prep)
        save_json({'extractive':ext, 't5':g_t5, 'bart':g_bart, 'hybrid':final}, os.path.join(args.outdir,'summary_hybrid.json'))
        save_pdf(final, os.path.join(args.outdir,'summary_hybrid.pdf'), title='Hybrid Summary')
    else:
        print('Transformers not available; only extractive summary produced.')



# """Stage 3: Summarization (extractive, generative (t5/bart), hybrid)"""
# import os, json, re
# import numpy as np
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import cosine_similarity
# import networkx as nx
# from fpdf import FPDF

# try:
#     from transformers import pipeline
#     from sentence_transformers import SentenceTransformer, util
#     import language_tool_python
#     TRANS = True
# except Exception:
#     TRANS = False

# # -------------------------------
# # Utility Functions
# # -------------------------------
# def load_json(path):
#     with open(path, 'r', encoding='utf-8') as f:
#         return json.load(f)

# def save_json(obj, path):
#     with open(path, 'w', encoding='utf-8') as f:
#         json.dump(obj, f, indent=2, ensure_ascii=False)

# def save_pdf(text, outpath, title=None):
#     pdf = FPDF()
#     pdf.add_page()
#     pdf.set_font('Arial', size=12)
#     if title:
#         pdf.set_font('Arial', 'B', 14)
#         pdf.multi_cell(0, 8, title)
#         pdf.ln(4)
#         pdf.set_font('Arial', size=12)
#     pdf.multi_cell(0, 8, text)
#     pdf.output(outpath)

# def flatten(prep_json):
#     return prep_json.get('sentences', [])

# def build_tfidf(sent_texts):
#     vec = TfidfVectorizer(max_df=0.85, min_df=1)
#     mat = vec.fit_transform(sent_texts)
#     return vec, mat

# def textrank_scores(tfidf):
#     sim = cosine_similarity(tfidf)
#     np.fill_diagonal(sim, 0)
#     G = nx.from_numpy_array(sim)
#     try:
#         pr = nx.pagerank(G)
#     except Exception:
#         pr = {i: float(sim[i].sum()) for i in range(sim.shape[0])}
#     return pr


# # -------------------------------
# # Extractive Summarizer
# # -------------------------------
# def summarize_extractive(prep_json, budget_words=200):
#     sents = flatten(prep_json)
#     texts = [s['lemmas_joined'] for s in sents]
#     origs = [s['orig'] for s in sents]
#     if not texts:
#         return ''
    
#     vec, tfidf = build_tfidf(texts)
#     tfidf_scores = np.asarray(tfidf.sum(axis=1)).reshape(-1)
#     pr = textrank_scores(tfidf)
#     textrank_sorted = [idx for idx, _ in sorted(pr.items(), key=lambda x: x[1], reverse=True)]
    
#     embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
#     embeddings = embedding_model.encode(texts, convert_to_tensor=True)
#     doc_embedding = embeddings.mean(dim=0, keepdim=True)
#     semantic_scores = util.cos_sim(embeddings, doc_embedding).cpu().numpy().flatten()
    
#     combined_scores = (0.4 * tfidf_scores) + (0.3 * semantic_scores) + (0.3 * np.array(
#         [pr.get(i, 0) for i in range(len(texts))]))
#     ranked = list(np.argsort(combined_scores)[::-1])
    
#     selected, total_words = [], 0
#     for idx in ranked:
#         sent = origs[idx]
#         word_count = len(sent.split())
#         if total_words + word_count > budget_words:
#             break
#         selected.append(sent)
#         total_words += word_count
    
#     summary = ' '.join(selected)
#     return summary


# # -------------------------------
# # Generative Summarizer (Improved)
# # -------------------------------
# def chunk_text(text, max_chars=2000):  # 🔧 reduced from 4000 → 2000
#     chunks, cur = [], ""
#     for sent in text.split('. '):
#         if len(cur) + len(sent) <= max_chars:
#             cur += sent + '. '
#         else:
#             chunks.append(cur.strip())
#             cur = sent + '. '
#     if cur:
#         chunks.append(cur.strip())
#     return chunks


# def summarize_generative(prep_json, model_name='facebook/bart-large-cnn'):
#     if not TRANS:
#         raise RuntimeError('transformers not installed')
#     sents = prep_json.get('sentences', [])
#     text = '\n'.join([s.get('orig', '') for s in sents])
#     summarizer = pipeline('summarization', model=model_name, device=-1)

#     chunks = chunk_text(text)
#     summaries = []
#     for ch in chunks:
#         out = summarizer(ch, max_length=100, min_length=60, num_beams=4, truncation=True)  # 🔧 word control
#         summaries.append(out[0]['summary_text'])

#     combined = ' '.join(summaries)
#     combined = summarizer(combined, max_length=120, min_length=80, num_beams=4)[0]['summary_text']  # 🔧 final 100-word limit

#     # Grammar & style correction
#     grammar_tool = language_tool_python.LanguageTool('en-US')
#     matches = grammar_tool.check(combined)
#     corrected = language_tool_python.utils.correct(combined, matches)
#     corrected = re.sub(r'\s+', ' ', corrected)
#     corrected = '. '.join(s.capitalize().strip() for s in corrected.split('.') if s.strip())  # 🔧 Capitalize sentences

#     # Sentence re-ranking for diversity
#     embed_model = SentenceTransformer('all-MiniLM-L6-v2')
#     sents = corrected.split('. ')
#     sent_emb = embed_model.encode(sents, convert_to_tensor=True)
#     doc_emb = embed_model.encode(text, convert_to_tensor=True)
#     scores = util.cos_sim(sent_emb, doc_emb).cpu().numpy().flatten()
#     ranked = sorted(zip(scores, range(len(sents)), sents), reverse=True)

#     # 🔧 Select top 5 semantically distinct sentences
#     seen, final = set(), []
#     for score, idx, s in ranked:
#         if not any(util.cos_sim(embed_model.encode(s), embed_model.encode(f)).item() > 0.8 for f in final):
#             final.append(s)
#         if len(final) == 5:
#             break

#     final_summary = ' '.join(final)
#     return final_summary


# # -------------------------------
# # Hybrid Summarizer
# # -------------------------------
# def hybrid_summary(prep_json):
#     ext = summarize_extractive(prep_json, budget_words=150)
#     gen_final = ''
#     try:
#         if TRANS:
#             gen_final = summarize_generative(prep_json, model_name='facebook/bart-large-cnn')
#     except Exception:
#         gen_final = ''
#     final = gen_final or ext
#     return ext, gen_final, final


# # -------------------------------
# # CLI Runner
# # -------------------------------
# if __name__ == '__main__':
#     import argparse
#     parser = argparse.ArgumentParser()
#     parser.add_argument('--in', dest='injson', required=True)
#     parser.add_argument('--outdir', default='output')
#     parser.add_argument('--budget', type=int, default=200)
#     args = parser.parse_args()
#     prep = load_json(args.injson)
#     os.makedirs(args.outdir, exist_ok=True)

#     ext = summarize_extractive(prep, budget_words=args.budget)
#     save_json({'summary': ext}, os.path.join(args.outdir, 'summary_extractive.json'))
#     save_pdf(ext, os.path.join(args.outdir, 'summary_extractive.pdf'), title='Extractive Summary')

#     if TRANS:
#         gen_final = summarize_generative(prep, model_name='facebook/bart-large-cnn')
#         save_json({'summary': gen_final}, os.path.join(args.outdir, 'summary_generative.json'))
#         save_pdf(gen_final, os.path.join(args.outdir, 'summary_generative.pdf'), title='Generative Summary')

#         ext, gen_final, final = hybrid_summary(prep)
#         save_json({'extractive': ext, 'generative': gen_final, 'hybrid': final},
#                   os.path.join(args.outdir, 'summary_hybrid.json'))
#         save_pdf(final, os.path.join(args.outdir, 'summary_hybrid.pdf'), title='Hybrid Summary')
#     else:
#         print('Transformers not available; only extractive summary produced.')


