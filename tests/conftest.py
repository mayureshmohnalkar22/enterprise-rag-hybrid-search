"""Keep the automated suite independent of the developer's running RAG setup.

The real application intentionally honors RAG_* shell variables (e.g. Ollama and
Sentence Transformers). Tests must start from deterministic defaults and can set
specific overrides via monkeypatch within the individual test.
"""

import os

import pytest


@pytest.fixture(autouse=True)
def isolate_rag_environment(monkeypatch):
    for key in tuple(os.environ):
        if key.startswith("RAG_"):
            monkeypatch.delenv(key)
