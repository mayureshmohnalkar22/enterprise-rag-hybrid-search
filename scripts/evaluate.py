import argparse
import json
from pathlib import Path
from rag.pipeline import Pipeline
from rag.evaluation import evaluate

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="data/eval/golden.json")
    parser.add_argument("--output", default="reports/evaluation.json")
    args = parser.parse_args()
    pipeline = Pipeline()
    if not pipeline.store.chunks:
        pipeline.ingest("data/sample_docs")
    report = evaluate(pipeline, args.dataset)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    print(json.dumps({key: {k: v for k, v in val.items() if k != "cases"} for key, val in report["modes"].items()}, indent=2))
    print(f"Full report: {out}")
