"""Local dependency and model availability checks. Run python -m scripts.preflight."""
import importlib.util, os, requests

def main():
    for module in ("fitz", "sentence_transformers", "chromadb", "streamlit", "fastapi"):
        print(f"{module}: {'installed' if importlib.util.find_spec(module) else 'NOT installed'}")
    try:
        r=requests.get(os.getenv("RAG_OLLAMA_URL","http://127.0.0.1:11434").rstrip('/')+"/api/tags",timeout=2)
        r.raise_for_status()
        models=[m.get('name') for m in r.json().get('models',[])]
        print('Ollama: reachable; models:',', '.join(models) or 'none')
    except requests.RequestException: print('Ollama: unreachable (optional if using extractive mode)')
if __name__=='__main__':main()
