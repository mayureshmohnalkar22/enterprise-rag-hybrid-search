"""Local deterministic hash embeddings by default; optional real semantic embeddings."""
import hashlib
import re
import numpy as np


def tokens(text):
    return re.findall(r"[a-z0-9_./-]+", text.lower())


class Embedder:
    def __init__(self, mode="hash"):
        self.mode = mode
        self.model = None
        if mode == "sentence-transformers":
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        elif mode != "hash":
            raise ValueError("RAG_EMBEDDER must be hash or sentence-transformers")

    def encode(self, texts):
        if not texts:
            return np.zeros((0, 384), dtype=np.float32)
        if self.model:
            return np.asarray(self.model.encode(texts, normalize_embeddings=True), dtype=np.float32)
        vectors = np.zeros((len(texts), 384), dtype=np.float32)
        for i, text in enumerate(texts):
            for term in tokens(text):
                digest = hashlib.blake2b(term.encode(), digest_size=8).digest()
                h = int.from_bytes(digest, "little")
                vectors[i, h % 384] += 1 if (h >> 10) % 2 else -1
            norm = np.linalg.norm(vectors[i])
            if norm:
                vectors[i] /= norm
        return vectors
