"""Fixed, recursive, and similarity-based semantic chunking."""
import hashlib
import re
import numpy as np


def make_chunk(doc, text, index, strategy):
    key = f"{doc['source']}:{doc['version']}:{doc['page']}:{index}:{strategy}"
    return {"id": hashlib.sha256(key.encode()).hexdigest()[:20], "text": text.strip(),
            "source": doc["source"], "version": doc["version"], "page": doc["page"],
            "path": doc.get("path", ""), "index": index, "strategy": strategy,
            "char_count": len(text.strip())}


def fixed_parts(text, size, overlap):
    parts, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        parts.append(text[start:end])
        if end == len(text):
            break
        start = max(start + 1, end - overlap)
    return parts


def recursive_parts(text, size, overlap):
    paragraphs = re.split(r"\n\s*\n|(?=^#{1,4} )", text, flags=re.MULTILINE)
    parts, current = [], ""
    for para in paragraphs:
        if len(para) > size:
            if current.strip():
                parts.append(current.strip())
                current = ""
            parts.extend(fixed_parts(para, size, overlap))
        elif len(current) + len(para) + 2 > size and current:
            parts.append(current.strip())
            current = (current[-overlap:] + "\n" if overlap else "") + para
        else:
            current += ("\n\n" if current else "") + para
    if current.strip():
        parts.append(current.strip())
    return parts


def semantic_parts(text, size, overlap, embedder, threshold=0.58):
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n{2,}", text) if s.strip()]
    if len(sentences) < 2:
        return fixed_parts(text, size, overlap)
    vecs = embedder.encode(sentences)
    groups, group, count = [], [], 0
    for i, sentence in enumerate(sentences):
        score = float(np.dot(vecs[i-1], vecs[i])) if i else 1.0
        if group and (count + len(sentence) > size or score < threshold):
            groups.append(" ".join(group))
            group, count = [], 0
        group.append(sentence)
        count += len(sentence) + 1
    if group:
        groups.append(" ".join(group))
    return [part for group in groups for part in fixed_parts(group, size, overlap)]


def chunk_documents(documents, strategy="recursive", size=850, overlap=130, embedder=None):
    if strategy not in {"fixed", "recursive", "semantic"}:
        raise ValueError("strategy must be fixed, recursive, or semantic")
    if size < 100 or not 0 <= overlap < size:
        raise ValueError("size >= 100 and 0 <= overlap < size required")
    chunks = []
    for doc in documents:
        if strategy == "fixed":
            parts = fixed_parts(doc["text"], size, overlap)
        elif strategy == "semantic":
            if embedder is None:
                raise ValueError("semantic chunking requires an embedder")
            parts = semantic_parts(doc["text"], size, overlap, embedder)
        else:
            parts = recursive_parts(doc["text"], size, overlap)
        chunks.extend(make_chunk(doc, part, i, strategy) for i, part in enumerate(parts) if part.strip())
    return chunks
