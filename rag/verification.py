"""Transparent citation/lexical diagnostics. Heuristics, never semantic entailment."""
import re
from .embedding import tokens

STOP = {"the", "and", "with", "from", "that", "are", "for", "this", "have", "into", "a", "an", "is", "to", "in", "of", "according", "source", "states", "following"}
CITE = re.compile(r"\[(\d+)\]")
LIST = re.compile(r"^\s*(?:[-*•]\s+|\d+[.)]\s+)")
ABSTAIN = re.compile(r"\b(?:i (?:do not|don't) (?:know|have)|not enough information|cannot (?:determine|answer)|insufficient (?:information|evidence))\b", re.I)
NUMERIC = re.compile(r"\b\d+(?:\.\d+)?%?\b")


def claim_groups(answer):
    """Treat citation-bearing list headers and the directly following list as one claim."""
    lines = [line.strip() for line in answer.splitlines() if line.strip()]
    groups, i = [], 0
    while i < len(lines):
        line = lines[i]
        if not LIST.match(line) and i + 1 < len(lines) and LIST.match(lines[i + 1]):
            items, j = [], i + 1
            while j < len(lines) and LIST.match(lines[j]):
                items.append(LIST.sub('', lines[j]).strip()); j += 1
            groups.append(' '.join([line] + items))
            i = j
            continue
        if LIST.match(line):
            items = []
            while i < len(lines) and LIST.match(lines[i]):
                items.append(LIST.sub('', lines[i]).strip()); i += 1
            groups.append(' '.join(items))
            continue
        groups.extend(x.strip() for x in re.split(r'(?<=[.!?])\s+(?=[A-Z])', line) if x.strip())
        i += 1
    return groups


def _overlap(claim, evidence):
    """Content-token recall for cited passage; NOT a probability of truth."""
    words = set(tokens(CITE.sub('', claim))) - STOP
    if not words:
        return 0.0
    return len(words & (set(tokens(evidence)) - STOP)) / len(words)


def verify(answer, sources):
    known = {s['citation']: s for s in sources}
    if not answer.strip() or (ABSTAIN.search(answer) and not CITE.search(answer) and len(answer.split()) < 15):
        return {'claims': [], 'citation_coverage': 0.0, 'valid_citation_rate': 0.0,
                'lexical_support_rate': 0.0, 'mean_lexical_overlap': 0.0, 'unsupported_claims': 0,
                'invalid_citations': [], 'abstained': True, 'warnings': [],
                'note': 'No cited factual claims. Lexical checks are not factual verification.'}
    checks, invalid_all = [], set()
    for claim in claim_groups(answer):
        citations = list(dict.fromkeys('['+n+']' for n in CITE.findall(claim)))
        valid = [x for x in citations if x in known]
        invalid = [x for x in citations if x not in known]
        invalid_all.update(invalid)
        content = CITE.sub('', claim).strip()
        # Citation markers and PDF page references in parentheses are metadata, not factual quantities.
        cleaned = re.sub(r'\([^)]*\bpage\s+\d+[^)]*\)', '', content, flags=re.I)
        cleaned = re.sub(r'\b(?:page|p\.)\s*\d+\b', '', cleaned, flags=re.I)
        cleaned = re.sub(r'\b[A-Z][A-Z_-]{2,}\s+\d+(?:\.\d+)+\b', '', cleaned)
        cleaned = re.sub(r'\b(?:section|chapter|figure|table)\s+\d+(?:\.\d+)*\b', '', cleaned, flags=re.I)
        claim_numbers = set(NUMERIC.findall(cleaned))
        scores = []
        for citation in valid:
            ev = known[citation]['text']
            score = _overlap(cleaned, ev)
            numeric_ok = not claim_numbers or claim_numbers.issubset(set(NUMERIC.findall(ev)))
            scores.append((score, numeric_ok))
        best = max((s for s, _ in scores), default=0.0)
        numeric_bad = bool(scores) and all(not ok for _, ok in scores)
        proxy = any(s >= 0.5 and ok for s, ok in scores)
        checks.append({'claim': content, 'citations': citations, 'valid_citations': valid,
                       'invalid_citations': invalid, 'lexical_overlap': round(best, 3),
                       'lexical_support': round(best, 3), 'supported_heuristic': proxy,
                       'number_mismatch': numeric_bad,
                       'status': 'invalid citation' if invalid else ('proxy-supported' if proxy else 'needs review')})
    count = max(1,len(checks))
    refs = sum(len(c['citations']) for c in checks)
    warnings = []
    if ABSTAIN.search(answer) and len(answer.splitlines()) >= 4:
        warnings.append('Possible contradictory abstention: answer says information is missing but also supplies a substantial response. Review manually.')
    if invalid_all:
        warnings.append('Some citation IDs are not among retrieved sources.')
    if any(c['number_mismatch'] for c in checks):
        warnings.append('A cited claim includes a number absent from its cited excerpt (heuristic).')
    return {'claims':checks,
            'citation_coverage':round(sum(bool(c['valid_citations']) for c in checks)/count,3),
            'valid_citation_rate':round(sum(len(c['valid_citations']) for c in checks)/max(1,refs),3),
            'lexical_support_rate':round(sum(c['supported_heuristic'] for c in checks)/count,3),
            'mean_lexical_overlap':round(sum(c['lexical_overlap'] for c in checks)/count,3),
            'unsupported_claims':sum(not c['supported_heuristic'] for c in checks),
            'invalid_citations':sorted(invalid_all), 'abstained':False, 'warnings':warnings,
            'note':'All overlap and numeric checks are proxies, not semantic entailment or proof of accuracy. Read the cited passages.'}
