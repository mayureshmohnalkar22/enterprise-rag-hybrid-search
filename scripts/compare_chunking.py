"""Benchmark retrieval on separate, isolated stores for each strategy."""
import json
import tempfile
from pathlib import Path
from rag.config import Settings
from rag.pipeline import Pipeline
from rag.evaluation import evaluate

if __name__ == "__main__":
    summary = {}
    with tempfile.TemporaryDirectory() as root:
        for name in ("fixed", "recursive", "semantic"):
            settings = Settings(storage=Path(root) / name, chunk_strategy=name)
            pipeline = Pipeline(settings)
            ingestion = pipeline.ingest("data/sample_docs")
            metrics = evaluate(pipeline, "data/eval/golden.json", modes=("hybrid",))
            summary[name] = {"chunks": ingestion["chunks_total"],
                             "hit_at_5": metrics["modes"]["hybrid"]["hit_at_k"],
                             "mrr_at_5": metrics["modes"]["hybrid"]["mrr_at_k"]}
    Path("reports").mkdir(exist_ok=True)
    Path("reports/chunking.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
