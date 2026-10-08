# Enterprise RAG V4 — reliability update

V4 builds on V3 and retains document ingestion, hybrid search, reranking, FastAPI, Ollama and Streamlit.

- Separates actual **mean token overlap** from the **fraction of claims above a lexical-overlap threshold**. Neither is factual faithfulness.
- Keeps citation coverage and invalid-ID detection; adds visible warnings about contradictory abstention and conflicting numbers.
- Improves the Ollama instruction for enumerations and compound labels without hard-coding NIST facts into the inference path.
- Includes offline NIST gold-list regressions to demonstrate how 100% citation coverage can coexist with missing or split categories.
- Adds regression tests and a standalone regression checker.

**Limitation:** This project does not implement a trained semantic entailment judge or automatic answer revision. An entailment classifier would require model downloads, a separately evaluated dataset, and calibration before making accuracy claims. The gold-list checker is for known labeled benchmarks only; it never sees arbitrary user answers at runtime.
