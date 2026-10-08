"""Optional reference-list completeness audit used for labeled regression evaluations.
The gold list is never injected into live retrieval or generation.
"""
import re


def normalize(s):
    return ' '.join(re.findall(r'[a-z0-9]+', s.casefold()))


def audit_list(answer, gold_items):
    """Compare complete item phrases, not just list length. Intended for gold-labeled tests."""
    normalized = normalize(answer)
    found = [item for item in gold_items if re.search(r'(?<!\w)'+re.escape(normalize(item))+r'(?!\w)', normalized)]
    missing = [item for item in gold_items if item not in found]
    return {'expected':len(gold_items), 'found':len(found), 'recall':round(len(found)/max(1,len(gold_items)),3),
            'missing':missing, 'matched':found, 'complete':not missing}
