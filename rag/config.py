import os
from dataclasses import dataclass, field
from pathlib import Path


def env_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


@dataclass
class Settings:
    storage: Path = field(default_factory=lambda: Path(os.getenv("RAG_STORAGE", "storage")))
    embedder: str = field(default_factory=lambda: os.getenv("RAG_EMBEDDER", "hash"))
    vector_backend: str = field(default_factory=lambda: os.getenv("RAG_VECTOR_BACKEND", "numpy"))
    reranker: str = field(default_factory=lambda: os.getenv("RAG_RERANKER", "lexical"))
    llm: str = field(default_factory=lambda: os.getenv("RAG_LLM", "extractive"))
    ollama_model: str = field(default_factory=lambda: os.getenv("RAG_OLLAMA_MODEL", "llama3.2:3b"))
    ollama_url: str = field(default_factory=lambda: os.getenv("RAG_OLLAMA_URL", "http://localhost:11434"))
    chunk_strategy: str = field(default_factory=lambda: os.getenv("RAG_CHUNK_STRATEGY", "recursive"))
    chunk_size: int = field(default_factory=lambda: env_int("RAG_CHUNK_SIZE", 850))
    chunk_overlap: int = field(default_factory=lambda: env_int("RAG_CHUNK_OVERLAP", 130))
    api_key: str = field(default_factory=lambda: os.getenv("RAG_API_KEY", ""))
    dense_weight: float = field(default_factory=lambda: float(os.getenv("RAG_DENSE_WEIGHT", "0.5")))
    context_chars: int = field(default_factory=lambda: env_int("RAG_CONTEXT_CHARS", 12000))
