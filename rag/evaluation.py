"""Reproducible document-level retrieval evaluation; no generated-answer claims."""
import json
import time
from pathlib import Path


def evaluate(pipeline, path, modes=("dense", "sparse", "hybrid"), k=5):
    rows = json.loads(Path(path).read_text())
    if not rows:
        raise ValueError("Evaluation dataset cannot be empty")
    results = {}
    for mode in modes:
        records = []
        for case in rows:
            started = time.perf_counter()
            retrieved = pipeline.retriever.search(case["question"], mode=mode, top_k=k)
            elapsed_ms = (time.perf_counter()-started)*1000
            sources = [r["source"] for r in retrieved]
            targets = set(case["relevant_sources"])
            if not targets:
                raise ValueError(f"Case {case['id']} has no relevant_sources")
            first = next((i for i, src in enumerate(sources, 1) if src in targets), None)
            unique_hits = set(sources) & targets
            # Document-level metrics deduplicate repeated chunks from the same source.
            unique_sources = list(dict.fromkeys(sources))
            dcg = sum((1 / __import__("math").log2(i + 2)) for i, src in enumerate(unique_sources) if src in targets)
            ideal = sum((1 / __import__("math").log2(i + 2)) for i in range(min(len(targets), k)))
            records.append({"id": case["id"], "hit": bool(first),
                            "reciprocal_rank": 1 / first if first else 0,
                            "precision_at_k": len(unique_hits) / k,
                            "recall_at_k": len(unique_hits) / len(targets),
                            "ndcg_at_k": dcg / ideal if ideal else 0,
                            "latency_ms": round(elapsed_ms, 3),
                            "returned_sources": sources, "relevant_sources": sorted(targets)})
        n = len(records)
        results[mode] = {"hit_at_k": round(sum(r["hit"] for r in records)/n, 4),
                         "mrr_at_k": round(sum(r["reciprocal_rank"] for r in records)/n, 4),
                         "precision_at_k": round(sum(r["precision_at_k"] for r in records)/n, 4),
                         "recall_at_k": round(sum(r["recall_at_k"] for r in records)/n, 4),
                         "ndcg_at_k": round(sum(r["ndcg_at_k"] for r in records)/n, 4),
                         "mean_latency_ms": round(sum(r["latency_ms"] for r in records)/n, 3),
                         "cases": records}
    return {"k": k, "case_count": len(rows), "embedding_mode": pipeline.settings.embedder,
            "reranker": pipeline.settings.reranker, "chunk_strategy": pipeline.settings.chunk_strategy,
            "modes": results, "notes": "Document-level retrieval evaluation on provided relevance labels; no answer faithfulness measurement. Precision@K denominator is K; results may contain multiple chunks per document."}
