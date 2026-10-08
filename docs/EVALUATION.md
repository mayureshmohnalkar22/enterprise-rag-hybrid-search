# Honest evaluation protocol

1. Development corpus: six bundled synthetic files, 60 **document-level** labels. A high Recall@5 on twelve chunks is a weak test; it does not imply enterprise performance.
2. For an independent test, import at least two licensed public corpora with explicit **passage-level** relevance labels; partition by document into dev/held-out test. Do not tune prompts or dense weights on the held-out test.
3. Record Recall@1/3/5/10, MRR@5, nDCG@5, median/p95 retrieval and generation latency and Mac peak RSS. Compare BM25, dense and hybrid by paired query.
4. Label model answers for completeness, abstention correctness, citation *support* (not just valid IDs), contradictions and missing evidence. Have a human review a blind sample. Content-word overlap is diagnostic only.
5. Run injection attempts in your own documents, malicious PDF/HTML, duplicate/update/delete/restart, offline Ollama, concurrent requests. Document failures as openly as successes.
6. Publish only measured figures, with embedding model, hardware, dataset version, chunk strategy, sample size and reranker configuration. Do not present hash embeddings as semantic embeddings.

See `docs/VERSION_HISTORY.md` for the actual V4 measurements and limitations.
