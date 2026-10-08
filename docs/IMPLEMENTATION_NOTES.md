# Implemented versus next-stage improvements

## Implemented
- Parse PDF, TXT, HTML and Markdown with source and page metadata.
- Fixed/recursive/semantic splitting and version-aware persistence.
- Local vector retrieval with optional ChromaDB; BM25 and weighted RRF.
- Optional CrossEncoder reranker, Ollama generation, citation-aware extractive fallback.
- Lexical citation support checks, sources, Streamlit interface and FastAPI endpoints.
- 60 gold questions and reproducible document-level retrieval evaluation.
- Docker Compose, pytest integration tests and GitHub Actions CI.

## Not yet production-certified
- Learned citation entailment verification and calibrated confidence scoring.
- Separate manually labeled faithful answer and abstention evaluation.
- Enterprise authentication, document ACL filtering, multi-tenancy and audit trails.
- Scalable atomic ingestion, external storage, distributed locking and telemetry.
- Actual load testing and deployment hardening.

The architecture intentionally distinguishes working portfolio functionality from production security controls.
