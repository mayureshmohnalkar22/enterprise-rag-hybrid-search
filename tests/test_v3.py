"""V3 regressions for citation coverage and source transparency."""
from pathlib import Path
from rag.config import Settings
from rag.pipeline import Pipeline
from rag.verification import verify


def evidence():
    return [{"citation": "[2]", "text": "The four core functions are GOVERN, MAP, MEASURE and MANAGE. Governance is cross-cutting."}]


def test_numbered_list_intro_citation_covers_group():
    answer = "The four core functions are [2]:\n1. GOVERN\n2. MAP\n3. MEASURE\n4. MANAGE"
    result = verify(answer, evidence())
    assert result["citation_coverage"] == 1
    assert len(result["claims"]) == 1
    assert result["invalid_citations"] == []


def test_invalid_citations_are_reported():
    result = verify("The functions are GOVERN, MAP, MEASURE and MANAGE [8].", evidence())
    assert result["citation_coverage"] == 0
    assert result["valid_citation_rate"] == 0
    assert result["invalid_citations"] == ["[8]"]


def test_unreferenced_list_is_not_cited():
    result = verify("The functions are:\n1. GOVERN\n2. MAP", evidence())
    assert result["citation_coverage"] == 0


def test_unrelated_following_paragraph_does_not_inherit_citation():
    result = verify("The functions are listed [2].\nThe CEO is Jane Smith.", evidence())
    assert result["citation_coverage"] == 0.5


def test_pipeline_exposes_debug_timings(tmp_path):
    p = Pipeline(Settings(storage=tmp_path))
    p.ingest(Path("data/sample_docs"))
    result = p.ask("How do access tokens work?")
    assert len(result["retrieval_debug"]) == len(result["sources"])
    assert result["timings"]["retrieval_ms"] >= 0
    assert result["timings"]["generation_ms"] >= 0
