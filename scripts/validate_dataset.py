"""Check golden question IDs and document relevance labels."""
import argparse
import json
from pathlib import Path
from rag.documents import ALLOWED


def validate(corpus, dataset):
    files = {p.name for p in Path(corpus).rglob("*") if p.suffix.lower() in ALLOWED}
    cases = json.loads(Path(dataset).read_text())
    errors, ids = [], set()
    for i, row in enumerate(cases, 1):
        cid = row.get("id", "")
        if not cid or cid in ids: errors.append(f"Case {i}: missing/duplicate ID {cid!r}")
        ids.add(cid)
        if not row.get("question", "").strip(): errors.append(f"Case {i}: empty question")
        if not row.get("relevant_sources"): errors.append(f"Case {i}: empty relevance labels")
        for name in row.get("relevant_sources", []):
            if name not in files: errors.append(f"Case {i}: missing source {name}")
    return len(cases), errors

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default="data/sample_docs")
    parser.add_argument("--dataset", default="data/eval/golden.json")
    args = parser.parse_args()
    count, issues = validate(args.corpus, args.dataset)
    print(f"Checked {count} evaluation cases; {len(issues)} issues")
    for issue in issues: print(issue)
    if issues: raise SystemExit(1)
