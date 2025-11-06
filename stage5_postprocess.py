"""Stage5: postprocessing (grammar fix, redaction)"""
import re, os
try:
    import language_tool_python
    TOOL = language_tool_python.LanguageTool('en-US')
except Exception:
    TOOL = None

def redact_pii(text):
    pii = r'(\\b\\d{10}\\b|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,})'
    return re.sub(pii, '[REDACTED]', text)

def grammar_fix(text):
    if not TOOL:
        return text
    try:
        matches = TOOL.check(text)
        return language_tool_python.utils.correct(text, matches)
    except Exception:
        return text

def postprocess(text):
    t = redact_pii(text)
    t = grammar_fix(t)
    return t



# """
# Stage 5: Advanced Post-Processing (Grammar, Redaction, Fluency, Semantics)
# --------------------------------------------------------------------------
# Improves final summary readability and quality:
#   - Grammar & style correction
#   - Merge short sentences
#   - Replace simple words with synonyms
#   - Reorder sentences for logical flow
#   - Remove duplicate or redundant lines
#   - Redact sensitive information (PII)
# """

# import re
# import os
# import nltk
# import spacy
# import language_tool_python
# from nltk.corpus import wordnet
# from sentence_transformers import SentenceTransformer, util

# # -----------------------------
# # 🔧 Model Initialization
# # -----------------------------
# nltk.download("punkt", quiet=True)
# nltk.download("wordnet", quiet=True)
# nlp = spacy.load("en_core_web_sm")
# embedder = SentenceTransformer("all-MiniLM-L6-v2")
# tool = language_tool_python.LanguageTool('en-US')

# # -----------------------------
# # 🔐 PII Redaction
# # -----------------------------
# def redact_pii(text):
#     pii_pattern = r'(\b\d{10}\b|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|https?://\S+)'
#     return re.sub(pii_pattern, "[REDACTED]", text)

# # -----------------------------
# # 🧠 Grammar Correction
# # -----------------------------
# def grammar_fix(text):
#     try:
#         matches = tool.check(text)
#         return language_tool_python.utils.correct(text, matches)
#     except Exception:
#         return text

# # -----------------------------
# # ✍️ Merge short sentences
# # -----------------------------
# def merge_short_sentences(text, min_len=6):
#     """Merge small sentences for smoother flow."""
#     doc = nlp(text)
#     merged, buffer = [], ""
#     for sent in doc.sents:
#         s = sent.text.strip()
#         if len(s.split()) < min_len:
#             buffer += " " + s
#         else:
#             if buffer:
#                 s = buffer.strip() + " " + s
#                 buffer = ""
#             merged.append(s)
#     if buffer:
#         merged.append(buffer.strip())
#     return " ".join(merged)

# # -----------------------------
# # 🧩 Synonym Enhancement
# # -----------------------------
# def synonym_replace(sentence):
#     """Replace common words with first WordNet synonym."""
#     words = sentence.split()
#     new_sentence = []
#     for w in words:
#         syns = wordnet.synsets(w)
#         if syns:
#             lemma = syns[0].lemmas()[0].name()
#             if lemma != w:
#                 new_sentence.append(lemma)
#             else:
#                 new_sentence.append(w)
#         else:
#             new_sentence.append(w)
#     return " ".join(new_sentence)

# # -----------------------------
# # 🔄 Reorder sentences logically
# # -----------------------------
# def reorder_sentences(summary):
#     """Order sentences by semantic similarity for logical coherence."""
#     sentences = nltk.sent_tokenize(summary)
#     if len(sentences) <= 2:
#         return summary
#     embeddings = embedder.encode(sentences, convert_to_tensor=True)
#     doc_emb = embeddings.mean(dim=0, keepdim=True)
#     scores = util.cos_sim(embeddings, doc_emb).cpu().numpy().flatten()
#     ranked = [s for _, s in sorted(zip(scores, sentences), reverse=True)]
#     return " ".join(ranked)

# # -----------------------------
# # 🧹 Full Post-Processing Pipeline
# # -----------------------------
# def postprocess(text):
#     """Apply all post-processing steps."""
#     t = redact_pii(text)
#     t = grammar_fix(t)
#     t = merge_short_sentences(t)
#     t = synonym_replace(t)
#     t = reorder_sentences(t)
#     return t

# # -----------------------------
# # 🧪 Example Run
# # -----------------------------
# if __name__ == "__main__":
#     raw_summary = (
#         "The report analyze sale data. It show good growth. "
#         "AI use improve process. Contact me at example@mail.com."
#     )
#     clean_summary = postprocess(raw_summary)
#     print("🧾 Original Summary:\n", raw_summary)
#     print("\n✨ Post-processed Summary:\n", clean_summary)
