import time
from pathlib import Path
from .chunking import chunk_documents
from .config import Settings
from .documents import load_document, load_directory
from .embedding import Embedder
from .generation import generate
from .retrieval import Retriever
from .store import Corpus
from .verification import verify


class Pipeline:
    def __init__(self, settings=None):
        self.settings = settings or Settings()
        self.embedder = Embedder(self.settings.embedder)
        self.store = Corpus(self.settings.storage, self.embedder, self.settings.vector_backend)
        self.retriever = Retriever(self.store, self.settings.reranker)

    def ingest(self, path, strategy=None):
        path = Path(path)
        docs = load_directory(path) if path.is_dir() else load_document(path)
        chunks = chunk_documents(docs, strategy or self.settings.chunk_strategy,
                                 self.settings.chunk_size, self.settings.chunk_overlap, self.embedder)
        return {**self.store.upsert(chunks), "documents_processed": len({d["source"] for d in docs}),
                "chunks_total": len(self.store.chunks)}

    def ask(self, question, mode="hybrid", top_k=5):
        start = time.perf_counter()
        retrieval_start = time.perf_counter()
        sources = self.retriever.search(question, mode=mode, top_k=top_k, dense_weight=self.settings.dense_weight, expand=True)
        retrieval_ms = round((time.perf_counter() - retrieval_start) * 1000, 2)
        generation_start = time.perf_counter()
        answer = generate(question, sources, self.settings)
        generation_ms = round((time.perf_counter() - generation_start) * 1000, 2)
        verification = verify(answer, sources)
        return {"question": question, "answer": answer, "sources": sources,
                "verification": verification, "mode": mode, "generation_mode": self.settings.llm, "model": self.settings.ollama_model if self.settings.llm == "ollama" else "extractive",
                "timings": {"retrieval_ms": retrieval_ms, "generation_ms": generation_ms},
                "retrieval_debug": [{"rank": i, "citation": item["citation"], "source": item["source"],
                                     "page": item["page"], "score": item["score"], "chunk_id": item["id"]}
                                    for i, item in enumerate(sources, 1)],
                "latency_ms": round((time.perf_counter() - start) * 1000, 2)}
