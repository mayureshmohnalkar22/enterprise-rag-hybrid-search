"""BM25, dense vector retrieval, rank fusion and optional cross-encoder reranking."""
import re
from .embedding import tokens


def bm25_search(chunks, question, top_k):
    if not chunks:
        return []
    corpus = [tokens(c["text"]) for c in chunks]
    try:
        from rank_bm25 import BM25Okapi
        scores = BM25Okapi(corpus).get_scores(tokens(question))
    except ImportError:
        # Portable BM25 baseline in restricted/offline environments.
        import math
        from collections import Counter
        query = tokens(question)
        avgdl = sum(map(len, corpus)) / max(1, len(corpus))
        dfs = Counter(term for doc in corpus for term in set(doc))
        scores = []
        for doc in corpus:
            counts, score = Counter(doc), 0.0
            for term in query:
                df = dfs.get(term, 0)
                idf = math.log(1 + (len(corpus) - df + .5) / (df + .5))
                freq = counts[term]
                if freq:
                    score += idf * freq * 2.5 / (freq + 1.5 * (.25 + .75 * len(doc) / max(1, avgdl)))
            scores.append(score)
    order = sorted(range(len(chunks)), key=lambda i: -scores[i])[:top_k]
    return [(chunks[i], float(scores[i])) for i in order]


def fuse(lists, weights=None, k=60):
    weights = weights or [1.0] * len(lists)
    scores, chunks = {}, {}
    for results, weight in zip(lists, weights):
        for rank, (chunk, _) in enumerate(results, 1):
            cid = chunk["id"]
            scores[cid] = scores.get(cid, 0.0) + weight / (k + rank)
            chunks[cid] = chunk
    return [(chunks[cid], score) for cid, score in sorted(scores.items(), key=lambda x: -x[1])]


class Retriever:
    def __init__(self, store, reranker="lexical"):
        self.store = store
        self.reranker = reranker
        self.cross_encoder = None
        if reranker == "cross-encoder":
            from sentence_transformers import CrossEncoder
            self.cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        elif reranker not in {"lexical", "none"}:
            raise ValueError("RAG_RERANKER must be lexical, none or cross-encoder")

    def search(self, question, mode="hybrid", top_k=5, candidate_k=20, dense_weight=0.5, expand=False):
        if mode not in {"hybrid", "dense", "sparse"}:
            raise ValueError("mode must be hybrid, dense or sparse")
        dense = self.store.dense(question, candidate_k) if mode != "sparse" else []
        sparse = bm25_search(self.store.chunks, question, candidate_k) if mode != "dense" else []
        if mode == "hybrid":
            results = fuse([dense, sparse], [dense_weight, 1 - dense_weight])
        else:
            results = dense if mode == "dense" else sparse
        candidates = results[:candidate_k]
        if expand and len(question.split()) >= 10:
            # Decomposed retrieval gathers evidence about distinct named topics.
            import re
            parts = [p.strip() for p in re.split(r"[,;]|\b(?:versus|vs\.|compared with)\b", question, flags=re.I) if len(p.split()) >= 2]
            if 1 < len(parts) <= 6:
                sets = [results]
                for part in parts:
                    local_dense = self.store.dense(part, candidate_k) if mode != "sparse" else []
                    local_sparse = bm25_search(self.store.chunks, part, candidate_k) if mode != "dense" else []
                    local = fuse([local_dense, local_sparse], [dense_weight, 1 - dense_weight]) if mode == "hybrid" else (local_dense if mode == "dense" else local_sparse)
                    sets.append(local)
                candidates = fuse(sets)[:candidate_k]

        if self.cross_encoder and candidates:
            relevance = self.cross_encoder.predict([(question, c["text"]) for c, _ in candidates])
            candidates = sorted(zip([c for c, _ in candidates], map(float, relevance)), key=lambda x: -x[1])
        elif self.reranker == "lexical":
            q = set(tokens(question))
            candidates = sorted(candidates, key=lambda p: -(p[1] + 0.008 * len(q & set(tokens(p[0]["text"]))) / max(1, len(q))))
        return [{**c, "score": round(float(score), 5), "citation": f"[{i}]"} for i, (c, score) in enumerate(candidates[:top_k], 1)]
