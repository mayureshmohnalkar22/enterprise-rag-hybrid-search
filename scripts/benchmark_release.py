"""Generate a V5 retrieval report without claiming generated-answer correctness."""
import argparse, json
from pathlib import Path
from rag.config import Settings
from rag.pipeline import Pipeline
from rag.evaluation import evaluate

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--embedder',choices=['hash','sentence-transformers'],default='hash')
    ap.add_argument('--output',default='reports/v5-retrieval.json')
    a=ap.parse_args()
    p=Pipeline(Settings(storage=Path('storage/release-benchmark-'+a.embedder),embedder=a.embedder,llm='extractive'))
    p.ingest('data/sample_docs')
    report=evaluate(p,'data/eval/golden.json')
    report['dataset_kind']='six small synthetic documents; document-level labels; NOT held-out independent evidence'
    report['limitations']='Not an Ollama, NIST PDF, or semantic-faithfulness assessment. Do not claim production accuracy.'
    output=Path(a.output);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2))
    print(json.dumps({m:{k:v for k,v in d.items() if k != 'cases'} for m,d in report['modes'].items()},indent=2))
    print('Saved',output)
if __name__=='__main__':main()
