"""Local-first FastAPI. Configure RAG_API_KEY before exposing beyond loopback."""
import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, File, HTTPException, UploadFile, Header, Depends
from pydantic import BaseModel, Field
from rag.documents import ALLOWED
from rag.pipeline import Pipeline
import secrets

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pipeline = Pipeline()
    yield

app = FastAPI(title="Enterprise RAG V5", version="5.0.0", lifespan=lifespan)

def authorize(x_api_key: str | None = Header(default=None)):
    configured = os.getenv("RAG_API_KEY", "")
    if configured and not secrets.compare_digest(x_api_key or "", configured):
        raise HTTPException(401, "Valid X-API-Key required")
    return True

class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    mode: str = Field(default="hybrid", pattern="^(hybrid|dense|sparse)$")
    top_k: int = Field(default=5, ge=1, le=20)

@app.get("/")
def root(): return {"service":"Enterprise RAG V5", "docs":"/docs", "health":"/health"}

@app.get("/health")
def health(): return {"status":"ok", "version":"5.0.0", "auth_enabled":bool(os.getenv("RAG_API_KEY"))}

@app.get("/v1/status", dependencies=[Depends(authorize)])
def status():
    p = app.state.pipeline
    return {"generation_mode": p.settings.llm, "model": p.settings.ollama_model if p.settings.llm == "ollama" else "extractive", "embedder":p.settings.embedder, "chunk_count":len(p.store.chunks), "dense_weight":p.settings.dense_weight}

@app.get("/v1/documents", dependencies=[Depends(authorize)])
def documents():
    p = app.state.pipeline
    return {"documents":[{"source":name,"version":version} for name,version in p.store.documents()],"total_chunks":len(p.store.chunks)}

@app.delete("/v1/documents/{source}", dependencies=[Depends(authorize)])
def delete_document(source: str):
    if not app.state.pipeline.store.delete(Path(source).name): raise HTTPException(404, "Document not found")
    return {"deleted":Path(source).name}

@app.post("/v1/ask", dependencies=[Depends(authorize)])
def ask(request: AskRequest):
    try: return app.state.pipeline.ask(request.question, request.mode, request.top_k)
    except RuntimeError as exc: raise HTTPException(503, "Generation service unavailable; check Ollama and model configuration") from exc

@app.post("/v1/ingest", dependencies=[Depends(authorize)])
async def ingest(file: UploadFile=File(...)):
    name=Path(file.filename or "").name
    if not name or Path(name).suffix.lower() not in ALLOWED:
        raise HTTPException(400,"Allowed extensions: .txt .md .html .htm .pdf")
    limit=15*1024*1024
    data=await file.read(limit+1)
    if len(data)>limit: raise HTTPException(413,"File exceeds 15 MB")
    if not data: raise HTTPException(422,"File is empty")
    if Path(name).suffix.lower()==".pdf" and not data.startswith(b"%PDF-"):
        raise HTTPException(422,"Invalid PDF header")
    with tempfile.TemporaryDirectory() as folder:
        path=Path(folder)/name
        path.write_bytes(data)
        try: return app.state.pipeline.ingest(path)
        except (ValueError, OSError, UnicodeError, RuntimeError, Exception) as exc:
            # Parsing dependencies may throw library-specific exceptions; never leak tracebacks.
            raise HTTPException(422,"Unable to parse or index this document") from exc
