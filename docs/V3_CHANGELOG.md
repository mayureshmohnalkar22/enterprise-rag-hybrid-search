# V3 changes

- Citation diagnostics now group a cited introductory heading and its contiguous numbered/bullet list into a single claim, avoiding the misleading list-item coverage penalty.
- Citation IDs are validated against retrieved sources; unknown IDs are reported separately.
- The API returns retrieval ranking diagnostics and separate retrieval/generation timings.
- The dashboard displays invalid-ID alerts, the ranking table and per-claim checks.
- Five regression tests guard these behaviors.

## Limitations

Lexical agreement and numbers are **heuristics**, not proof of factual correctness. Citations are never automatically repaired or fabricated. Human review remains necessary.

The RAG system does not guarantee that a generated assertion is entailed by its citation. For production use, add a calibrated entailment model and human-reviewed tests.
