"""Run an isolated, deterministic benchmark without touching user-uploaded storage."""
import argparse
import json
import tempfile
from pathlib import Path
from dataclasses import replace
from rag.config import Settings
from rag.evaluation import evaluate
from rag.pipeline import Pipeline


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default="data/sample_docs")
    parser.add_argument("--dataset", default="data/eval/golden.json")
    parser.add_argument("--embedder", choices=["hash", "sentence-transformers"], default="hash")
    parser.add_argument("--reranker", choices=["none", "lexical", "cross-encoder"], default="none")
    parser.add_argument("--chunking", choices=["fixed", "recursive", "semantic"], default="recursive")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--output", default="reports/evaluation.json")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as folder:
        settings = replace(Settings(), storage=Path(folder), embedder=args.embedder,
                           reranker=args.reranker, chunk_strategy=args.chunking, vector_backend="numpy")
        pipeline = Pipeline(settings)
        ingestion = pipeline.ingest(args.corpus)
        report = evaluate(pipeline, args.dataset, k=args.top_k)
        report["corpus"] = str(args.corpus)
        report["ingestion"] = ingestion
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2))
    print(json.dumps({"configuration": {"embedder": args.embedder, "reranker": args.reranker},
                      "cases": report["case_count"],
                      "metrics": {mode: {k: v for k, v in m.items() if k != "cases"} for mode, m in report["modes"].items()}}, indent=2))
    print(f"Saved {target}")

if __name__ == "__main__":
    run()
