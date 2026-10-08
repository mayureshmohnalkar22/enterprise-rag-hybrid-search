# Project evolution: V1 → V5

| Version | Focus | What changed |
|---|---|---|
| V1 | Runnable prototype | PDF/HTML/Markdown/TXT parsing, chunking, hybrid search, basic FastAPI + Streamlit and extraction fallback. |
| V2 | Reproducible retrieval | Sentence Transformers option, BM25/dense/hybrid benchmarking, 60 labeled synthetic questions, dataset checks, corrected import-time storage settings. |
| V3 | Citation diagnostics | Grouped-list citation checks, invalid-ID detection, retrieval timings, diagnostic panels and NIST list regression fixtures. |
| V4 | Evaluation transparency | Distinguished mean token overlap from threshold pass rate, exposed numerical and contradiction warnings, expanded regression suite to 25 passing tests. |
| V5 | Final portfolio release | Malformed-PDF handling, optional API key, localhost-bound Docker, document deletion, safer numeric comparison, diversified query retrieval, model-status UI, regression tests, preflight and release documentation. |

## Measured V4 audit (2026-10-08)

**25/25 tests passed**. Dataset: six synthetic source documents (recursive: 12 chunks) and 60 document-level retrieval labels, `k=5`, hash embeddings (not semantic neural embeddings).

| Method | Recall@5 | MRR@5 | nDCG@5 |
|---|---:|---:|---:|
| Dense (hash) | 0.9833 | 0.8233 | 0.8647 |
| BM25 | 1.0000 | 0.9389 | 0.9554 |
| Hybrid | 1.0000 | 0.8297 | 0.8749 |

The toy evaluation favored BM25; it **does not** show that hybrid is universally worse. Hash vectors cannot substitute for the real Sentence Transformers evaluation. No Ollama or NIST PDF execution was available in the audit environment. V3/V4 user-observed NIST cases included: contradictory abstention despite listing all seven characteristics; splitting “Secure and Resilient” and omitting “Privacy-Enhanced”; a corrected seven-item answer with 100% citation coverage and 0% lexical-support proxy; a four-function response with 58% mean token overlap but 0% threshold pass; and an uneven long answer with 43% citation coverage, 24% token overlap, and 23.42s latency. These are **individual local examples**, not controlled benchmark averages. Citation ID validity does not establish evidence support.

## Release honesty

A portfolio-ready repository means the code, tests and instructions are publishable. A *production-ready* multi-tenant service needs further work: tenant authorization, rate limits, independently held-out large-scale document evaluation, injection hardening, calibrated semantic faithfulness assessment, live local Ollama and Mac resource benchmarks. Any README screenshots must be genuine; placeholders are not demonstrations.
