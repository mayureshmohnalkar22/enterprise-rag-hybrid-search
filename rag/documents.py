"""Multi-format ingestion with provenance; handles local files only."""
import hashlib
import re
from pathlib import Path
from bs4 import BeautifulSoup

ALLOWED = {".txt", ".md", ".html", ".htm", ".pdf"}


def normalize(text: str) -> str:
    return re.sub(r"[ \t]+", " ", re.sub(r"\r\n?", "\n", text)).strip()


def load_document(path: Path) -> list[dict]:
    path = Path(path)
    if path.suffix.lower() not in ALLOWED:
        raise ValueError(f"Unsupported type: {path.suffix}")
    raw = path.read_bytes()
    version = hashlib.sha256(raw).hexdigest()[:16]
    if path.suffix.lower() == ".pdf":
        import fitz
        with fitz.open(stream=raw, filetype="pdf") as pdf:
            pages = [(idx + 1, page.get_text()) for idx, page in enumerate(pdf)]
    else:
        text = raw.decode("utf-8-sig", errors="replace")
        if path.suffix.lower() in {".html", ".htm"}:
            soup = BeautifulSoup(text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()
            text = soup.get_text("\n")
        pages = [(1, text)]
    out = []
    for page, text in pages:
        clean = normalize(text)
        if clean:
            out.append({"source": path.name, "page": page, "text": clean,
                        "version": version, "path": str(path.resolve())})
    return out


def load_directory(folder: Path) -> list[dict]:
    return [piece for path in sorted(Path(folder).rglob("*"))
            if path.is_file() and path.suffix.lower() in ALLOWED
            for piece in load_document(path)]
