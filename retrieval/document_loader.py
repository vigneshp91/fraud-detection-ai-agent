import os


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}


class DocumentLoader:
    """Loads raw documents from a directory."""

    def __init__(self, raw_dir: str):
        self.raw_dir = raw_dir

    def load_all(self) -> list[dict]:
        documents = []
        for fname in os.listdir(self.raw_dir):
            ext = os.path.splitext(fname)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue
            path = os.path.join(self.raw_dir, fname)
            documents.append(self._load_file(path, fname))
        return documents

    def _load_file(self, path: str, fname: str) -> dict:
        ext = os.path.splitext(fname)[1].lower()
        if ext == ".pdf":
            return self._load_pdf(path, fname)
        with open(path, encoding="utf-8", errors="ignore") as f:
            return {"source": fname, "text": f.read()}

    def _load_pdf(self, path: str, fname: str) -> dict:
        try:
            import pypdf
            reader = pypdf.PdfReader(path)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError:
            text = f"[PDF content of {fname} — install pypdf to extract text]"
        return {"source": fname, "text": text}
