"""Run: python -m scripts.check_nist_regressions (offline, no NIST PDF download)."""
import json
from pathlib import Path
from rag.list_checks import audit_list


def main():
    data = json.loads(Path('data/eval/nist_regressions.json').read_text())
    for case in data['cases']:
        result = audit_list(case['answer'], data['reference_items'])
        print(f"{case['id']}: {result['found']}/{result['expected']} expected labels; missing={result['missing']}")

if __name__ == '__main__':
    main()
