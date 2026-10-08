"""Run with: streamlit run app/dashboard.py"""
import os
import requests
import streamlit as st

st.set_page_config(page_title="Enterprise RAG | Hybrid Search", page_icon="📚", layout="wide")
API = os.getenv("RAG_API_URL", "http://localhost:8000").rstrip("/")
HEADERS = {"X-API-Key": os.getenv("RAG_API_KEY", "")}
st.title("📚 Enterprise RAG")
st.caption("Hybrid retrieval · Grounded answers · Inspectable sources")

with st.sidebar:
    st.header("Configuration")
    mode = st.selectbox("Retrieval mode", ["hybrid", "dense", "sparse"])
    top_k = st.slider("Top sources", 1, 15, 5)
    try:
        status = requests.get(f"{API}/v1/status", headers=HEADERS, timeout=5).json()
        st.caption(f"Generator: {status.get('generation_mode','unknown')} · Embedder: {status.get('embedder','unknown')}")
    except Exception:
        st.warning("Backend unavailable or authorization required")
    uploaded = st.file_uploader("Index a document", type=["pdf", "md", "txt", "html", "htm"])
    if uploaded and st.button("Ingest document", type="primary"):
        try:
            response = requests.post(f"{API}/v1/ingest", files={"file": (uploaded.name, uploaded.getvalue())}, headers=HEADERS, timeout=180)
            response.raise_for_status()
            st.success(response.json())
        except requests.RequestException as exc:
            st.error(f"Ingestion failed: {exc}")
    try:
        docs = requests.get(f"{API}/v1/documents", headers=HEADERS, timeout=5).json()
        st.metric("Indexed chunks", docs["total_chunks"])
        st.write("Documents:", ", ".join(d["source"] for d in docs["documents"]) or "None yet")
        selected = st.selectbox("Delete indexed document", [""] + [d["source"] for d in docs["documents"]])
        if selected and st.button("Delete selected document"):
            try:
                res=requests.delete(f"{API}/v1/documents/{selected}",headers=HEADERS,timeout=30)
                res.raise_for_status()
                st.success("Deleted; refresh the dashboard to update the list")
            except requests.RequestException as exc: st.error(str(exc))
    except Exception:
        st.warning("Start the API with `uvicorn app.main:app --reload`.")

question = st.text_input("Ask a question about your documents", placeholder="How does token rotation work?")
if st.button("Ask", type="primary") and question:
    try:
        with st.spinner("Retrieving and generating..."):
            response = requests.post(f"{API}/v1/ask", json={"question": question, "mode": mode, "top_k": top_k}, headers=HEADERS, timeout=180)
            response.raise_for_status()
            result = response.json()
        st.caption(f"Generation mode: {result.get('generation_mode')} · Model: {result.get('model')}")
        st.subheader("Answer")
        st.markdown(result["answer"])
        a, b, c, d = st.columns(4)
        a.metric("Latency", f"{result['latency_ms']:.0f} ms")
        b.metric("Citation coverage", f"{result['verification']['citation_coverage']:.0%}")
        c.metric("Mean token overlap", f"{result['verification'].get('mean_lexical_overlap', 0):.0%}")
        d.metric("Overlap threshold passed", f"{result['verification']['lexical_support_rate']:.0%}")
        st.caption(f"Valid citation references: {result['verification'].get('valid_citation_rate', 0):.0%} · Invalid IDs: {result['verification'].get('invalid_citations', [])}")
        if result["verification"].get("invalid_citations"):
            st.warning("The answer includes citation IDs that are not in the retrieved sources. Review before relying on it.")
        t = result.get("timings", {})
        if t:
            st.caption(f"Retrieval: {t.get('retrieval_ms', 0):.0f} ms · Generation: {t.get('generation_ms', 0):.0f} ms")
        st.caption(result["verification"]["note"])
        for warning in result["verification"].get("warnings", []):
            st.warning(warning)
        st.info("A high citation score means the IDs are well formed, not that the answer is true. Check retrieved evidence manually.")
        st.subheader("Retrieved evidence")
        for source in result["sources"]:
            with st.expander(f"{source['citation']} {source['source']} · page {source['page']} · score {source['score']}"):
                st.write(source["text"])
                st.caption(f"Chunk ID: {source['id']} · Strategy: {source['strategy']}")
        with st.expander("Retrieval diagnostics"):
            st.dataframe(result.get("retrieval_debug", []), use_container_width=True)
        with st.expander("Claim-level citation checks"):
            st.json(result["verification"]["claims"])
    except requests.RequestException as exc:
        st.error(f"Request failed: {exc}")

with st.expander("📊 Evaluation dashboard (local benchmark)"):
    from pathlib import Path
    import json
    report_path = Path("reports/evaluation.json")
    if not report_path.exists():
        st.info("Run `python -m scripts.evaluate` in the terminal, then refresh.")
    else:
        benchmark = json.loads(report_path.read_text())
        st.caption(f"Run configuration: {benchmark.get('embedding_mode', 'legacy')} embeddings · {benchmark.get('reranker', 'unknown')} reranker · {benchmark.get('case_count')} labeled questions")
        modes = benchmark["modes"]
        st.dataframe([{"mode": mode, **{k: val for k, val in entry.items() if k != "cases"}} for mode, entry in modes.items()], use_container_width=True)
        st.bar_chart({mode: {"Hit@K": entry["hit_at_k"], "MRR@K": entry["mrr_at_k"], "Recall@K": entry.get("recall_at_k", 0)} for mode, entry in modes.items()})
        st.caption("These are retrieval metrics only; they do not establish generated-answer accuracy or faithfulness.")
