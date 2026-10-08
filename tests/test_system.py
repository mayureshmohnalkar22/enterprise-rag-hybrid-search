import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from rag.chunking import chunk_documents
from rag.config import Settings
from rag.embedding import Embedder
from rag.evaluation import evaluate
from rag.pipeline import Pipeline
from rag.retrieval import fuse
from rag.verification import verify
from app.main import app


@pytest.fixture
def pipeline(tmp_path):
    p = Pipeline(Settings(storage=tmp_path))
    p.ingest("data/sample_docs")
    return p


def test_ingestion_and_idempotency(pipeline):
    assert len(pipeline.store.documents()) == 6
    assert pipeline.ingest("data/sample_docs")["unchanged"] is True  # same versions and strategy


def test_chunking_modes():
    docs = [{"source": "x.md", "version": "1", "page": 1, "text": "First topic. " * 40 + "\n\nSecond topic. " * 40}]
    for strategy in ("fixed", "recursive", "semantic"):
        chunks = chunk_documents(docs, strategy, 250, 30, Embedder())
        assert chunks and all(c["strategy"] == strategy for c in chunks)


def test_hybrid_retrieval(pipeline):
    for mode in ("hybrid", "dense", "sparse"):
        chunks = pipeline.retriever.search("refresh token rotation authentication", mode=mode)
        assert chunks and chunks[0]["source"] == "authentication.md"


def test_citation_verification():
    checks = verify("Tokens expire after fifteen minutes [1].", [{"citation": "[1]", "text": "Tokens expire after fifteen minutes."}])
    assert checks["citation_coverage"] == 1
    assert checks["lexical_support_rate"] == 1
    invalid = verify("This is not documented [9].", [])
    assert invalid["citation_coverage"] == 0


def test_answer(pipeline):
    result = pipeline.ask("How long does an access token last?")
    assert result["sources"] and "[" in result["answer"]
    assert result["latency_ms"] >= 0


def test_benchmark(pipeline):
    report = evaluate(pipeline, "data/eval/golden.json")
    assert report["case_count"] == 60
    for mode in report["modes"].values():
        assert 0 <= mode["hit_at_k"] <= 1


def test_api_upload_and_query(tmp_path, monkeypatch):
    monkeypatch.setenv("RAG_STORAGE", str(tmp_path))
    with TestClient(app) as client:
        assert client.get("/health").json()["status"] == "ok"
        response = client.post("/v1/ingest", files={"file": ("example.txt", b"Our API requires TLS and rotates keys every week.")})
        assert response.status_code == 200
        response = client.post("/v1/ask", json={"question": "What does the API require?"})
        assert response.status_code == 200
        assert response.json()["sources"]
        assert client.get("/v1/documents").json()["total_chunks"] == 1
        assert client.post("/v1/ingest", files={"file": ("hack.exe", b"no")}).status_code == 400


def test_version_replacement(tmp_path):
    p = Pipeline(Settings(storage=tmp_path / "db"))
    doc = tmp_path / "test.md"
    doc.write_text("The service rotates signing keys every ninety days.")
    p.ingest(doc)
    old = p.store.chunks[0]["id"]
    doc.write_text("The service rotates signing keys every thirty days.")
    p.ingest(doc)
    assert p.store.chunks[0]["id"] != old
    assert len(p.store.documents()) == 1


def test_ranking_fusion():
    a, b = {"id": "a"}, {"id": "b"}
    combined = fuse([[(a, 1), (b, 0)], [(b, 2), (a, 1)]])
    assert set(x["id"] for x, _ in combined) == {"a", "b"}


def test_numeric_citation_mismatch():
    evidence = [{"citation": "[1]", "text": "The token expires after 15 minutes."}]
    result = verify("The token expires after 60 minutes [1].", evidence)
    assert result["unsupported_claims"] == 1
    assert result["claims"][0]["number_mismatch"] is True


def test_abstention_verification():
    result = verify("I don't know based on the indexed documents.", [])
    assert result["abstained"] is True
    assert result["unsupported_claims"] == 0


def test_expanded_metrics(pipeline):
    report = evaluate(pipeline, "data/eval/golden.json", k=5)
    assert report["embedding_mode"] == "hash"
    for mode in report["modes"].values():
        assert 0 <= mode["recall_at_k"] <= 1
        assert 0 <= mode["ndcg_at_k"] <= 1
        assert mode["mean_latency_ms"] >= 0


def test_golden_labels_valid():
    from scripts.validate_dataset import validate
    count, problems = validate("data/sample_docs", "data/eval/golden.json")
    assert count >= 50
    assert problems == []
