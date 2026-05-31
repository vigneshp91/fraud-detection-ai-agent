from retrieval.embedder import Embedder
from retrieval.faiss_store import FAISSStore

INDEX_DIR = "knowledge/faiss_index"


class Retriever:
    """Retrieves relevant document chunks for a query using FAISS."""

    def __init__(self, index_dir: str = INDEX_DIR):
        self._embedder = Embedder()
        self._store    = FAISSStore()
        self._store.load(index_dir)

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        embedding = self._embedder.embed_one(query)
        return self._store.search(embedding, top_k=top_k)
