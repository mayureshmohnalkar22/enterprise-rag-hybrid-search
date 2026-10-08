"""Final release regression suite: lifecycle, failure handling and security boundaries."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from rag.config import Settings
from rag.pipeline import Pipeline
from rag.verification import verify


def test_numerical_metadata_is_not_claim_quantity():
    result = verify('GOVERN 1.1 is documented [1], page 27.',
                    [{'citation':'[1]','text':'GOVERN 1.1 describes legal requirements.'}])
    assert not result['claims'][0]['number_mismatch']


def test_numerical_factual_difference_remains_flagged():
    result = verify('The service expires after 90 days [1].',
                    [{'citation':'[1]','text':'The service expires after 30 days.'}])
    assert result['claims'][0]['number_mismatch']


def test_document_delete_and_restart(tmp_path):
    settings=Settings(storage=tmp_path/'db')
    doc=tmp_path/'remove.md'; doc.write_text('Rotating tokens requires re-authentication.')
    p=Pipeline(settings); p.ingest(doc)
    assert p.store.delete('remove.md')
    assert not p.store.delete('remove.md')
    assert Pipeline(settings).store.documents()==[]


def test_api_key_and_upload_validation(tmp_path,monkeypatch):
    monkeypatch.setenv('RAG_STORAGE',str(tmp_path/'db'))
    monkeypatch.setenv('RAG_API_KEY','local-test-secret')
    with TestClient(app) as client:
        assert client.get('/health').status_code==200
        assert client.get('/v1/documents').status_code==401
        assert client.post('/v1/ask',json={'question':'Is anything indexed?'}).status_code==401
        assert client.post('/v1/ingest',files={'file':('x.txt',b'ok')}).status_code==401
        headers={'X-API-Key':'local-test-secret'}
        assert client.get('/v1/status',headers=headers).json()['generation_mode']=='extractive'
        assert client.post('/v1/ingest',headers=headers,files={'file':('bad.pdf',b'not pdf')}).status_code==422
        assert client.post('/v1/ingest',headers=headers,files={'file':('empty.txt',b'')}).status_code==422
        good=client.post('/v1/ingest',headers=headers,files={'file':('good.txt',b'Local APIs require TLS 1.3 for secure transport.')})
        assert good.status_code==200,good.text
        assert client.delete('/v1/documents/good.txt',headers=headers).status_code==200
        assert client.delete('/v1/documents/good.txt',headers=headers).status_code==404


def test_malformed_pdf_with_header(tmp_path,monkeypatch):
    monkeypatch.setenv('RAG_STORAGE',str(tmp_path/'db'))
    monkeypatch.delenv('RAG_API_KEY',raising=False)
    with TestClient(app) as client:
        response=client.post('/v1/ingest',files={'file':('malformed.pdf',b'%PDF-1.7\nnot a real PDF')})
        assert response.status_code==422
        assert 'traceback' not in response.text.lower()


def test_query_expansion_retains_valid_citations(tmp_path):
    p=Pipeline(Settings(storage=tmp_path/'db'))
    p.ingest('data/sample_docs')
    sources=p.retriever.search('authentication, refresh token rotation, governance, and incident response documentation',expand=True)
    assert sources and [s['citation'] for s in sources]==[f'[{i}]' for i in range(1,len(sources)+1)]


def test_test_configuration_isolation(monkeypatch):
    """A test may override model settings without leaking into another test."""
    assert Settings().embedder == 'hash'
    assert Settings().llm == 'extractive'
    monkeypatch.setenv('RAG_EMBEDDER', 'sentence-transformers')
    monkeypatch.setenv('RAG_LLM', 'ollama')
    assert Settings().embedder == 'sentence-transformers'
    assert Settings().llm == 'ollama'
