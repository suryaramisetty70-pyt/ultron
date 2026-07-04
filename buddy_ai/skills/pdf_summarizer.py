# pdf_summarizer.py
"""Offline PDF Summarizer Skill

Extracts text from a PDF file and produces a concise summary.
Uses pypdf for extraction and a simple extractive summarization
approach (sentence scoring by frequency) for offline operation.
"""
import os
import re
from collections import Counter

def extract_text(pdf_path: str) -> str:
    """Extract all text from a PDF file using pypdf."""
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            return "ERROR: pypdf or PyPDF2 not installed."

    if not os.path.exists(pdf_path):
        return f"ERROR: File not found: {pdf_path}"

    reader = PdfReader(pdf_path)
    text_parts = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)
    return "\n".join(text_parts)

def _split_sentences(text: str) -> list:
    """Split text into sentences."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 10]

def _score_sentences(sentences: list) -> list:
    """Score sentences by word frequency (extractive summarization)."""
    all_words = []
    for s in sentences:
        words = re.findall(r'\b[a-zA-Z]{3,}\b', s.lower())
        all_words.extend(words)

    # Remove very common words
    stop_words = {'the', 'and', 'for', 'that', 'this', 'with', 'are', 'was',
                  'were', 'been', 'have', 'has', 'had', 'not', 'but', 'from',
                  'they', 'their', 'which', 'will', 'can', 'would', 'could',
                  'should', 'about', 'into', 'more', 'also', 'than', 'other'}
    freq = Counter(w for w in all_words if w not in stop_words)

    scored = []
    for i, s in enumerate(sentences):
        words = re.findall(r'\b[a-zA-Z]{3,}\b', s.lower())
        score = sum(freq.get(w, 0) for w in words if w not in stop_words)
        scored.append((score, i, s))

    scored.sort(reverse=True)
    return scored

def summarize_pdf(pdf_path: str, num_sentences: int = 5) -> str:
    """Extract text from PDF and return a concise summary."""
    text = extract_text(pdf_path)
    if text.startswith("ERROR:"):
        return text

    if not text.strip():
        return "The PDF appears to be empty or image-only (no extractable text)."

    sentences = _split_sentences(text)
    if len(sentences) <= num_sentences:
        return " ".join(sentences)

    scored = _score_sentences(sentences)
    # Pick top N sentences, ordered by original position
    top = sorted(scored[:num_sentences], key=lambda x: x[1])
    summary = " ".join(s for _, _, s in top)
    return summary

def summarize_to_file(pdf_path: str, output_path: str = None, num_sentences: int = 5) -> str:
    """Summarize a PDF and save to a text file."""
    summary = summarize_pdf(pdf_path, num_sentences)
    if output_path is None:
        base = os.path.splitext(pdf_path)[0]
        output_path = f"{base}_summary.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(summary)
    return f"Summary saved to {output_path}"
