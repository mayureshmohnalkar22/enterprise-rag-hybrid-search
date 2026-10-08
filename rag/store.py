"""Persistent corpus with version-aware upserts; optional Chroma vector index."""
import json
import threading
from pathlib import Path
import numpy as np


class Corpus:
    def __init__(self, folder, embedder, backend="numpy"):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.path = self.folder / "chunks.json"
        self.embedder, self.backend = embedder, backend
        self.lock = threading.RLock()
        self.chunks = json.loads(self.path.read_text()) if self.path.exists() else []
        self.vectors = self.embedder.encode([c["text"] for c in self.chunks])
        self.collection = None
        if backend == "chroma":
            import chromadb
            client = chromadb.PersistentClient(path=str(self.folder / "chroma"))
            self.collection = client.get_or_create_collection("documents", metadata={"hnsw:space": "cosine"})
            self._sync_chroma()
        elif backend != "numpy":
            raise ValueError("RAG_VECTOR_BACKEND must be numpy or chroma")

    def _sync_chroma(self):
        ids = [c["id"] for c in self.chunks]
        current = self.collection.get()["ids"]
        stale = list(set(current) - set(ids))
        if stale:
            self.collection.delete(ids=stale)
        if ids:
            self.collection.upsert(ids=ids, documents=[c["text"] for c in self.chunks],
                                   embeddings=self.vectors.tolist())

    def upsert(self, new):
        with self.lock:
            sources = {c["source"] for c in new}
            old_for_sources = [c for c in self.chunks if c["source"] in sources]
            old_versions = {(c["source"], c["version"], c["strategy"]) for c in old_for_sources}
            new_versions = {(c["source"], c["version"], c["strategy"]) for c in new}
            if old_versions == new_versions and old_for_sources:
                return {"inserted": 0, "deduplicated": 0, "unchanged": True}
            survivors = [c for c in self.chunks if c["source"] not in sources]
            survivor_vecs = self.embedder.encode([c["text"] for c in survivors])
            inserted, duplicates = [], 0
            # Detect near-duplicates only within each source. Distinct documents retain their provenance.
            vectors = self.embedder.encode([c["text"] for c in new])
            kept_vectors = []
            for c, v in zip(new, vectors):
                if kept_vectors and max(float(np.dot(v, p)) for p in kept_vectors) > 0.98:
                    duplicates += 1
                    continue
                inserted.append(c)
                kept_vectors.append(v)
            self.chunks = survivors + inserted
            self.vectors = self.embedder.encode([c["text"] for c in self.chunks])
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.chunks, indent=2))
            tmp.replace(self.path)
            if self.collection:
                self._sync_chroma()
            return {"inserted": len(inserted), "deduplicated": duplicates, "unchanged": False}

    def dense(self, query, top_k):
        if not self.chunks:
            return []
        q = self.embedder.encode([query])[0]
        with self.lock:
            if self.collection:
                response = self.collection.query(query_embeddings=[q.tolist()], n_results=min(top_k, len(self.chunks)))
                lookup = {c["id"]: c for c in self.chunks}
                return [(lookup[k], float(1 - dist)) for k, dist in zip(response["ids"][0], response["distances"][0])]
            scores = self.vectors @ q
            return [(self.chunks[int(i)], float(scores[i])) for i in np.argsort(-scores)[:top_k]]

    def delete(self, source):
        with self.lock:
            before = len(self.chunks)
            self.chunks = [c for c in self.chunks if c["source"] != source]
            if len(self.chunks) == before:
                return False
            self.vectors = self.embedder.encode([c["text"] for c in self.chunks])
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.chunks, indent=2))
            tmp.replace(self.path)
            if self.collection:
                self._sync_chroma()
            return True

    def documents(self):
        return sorted({(c["source"], c["version"]) for c in self.chunks})
