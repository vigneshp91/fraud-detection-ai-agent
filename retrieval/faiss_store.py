from __future__ import annotations
import os
import pickle


class FAISSStore:
    """Wraps a FAISS index for storing and searching embeddings."""

    def __init__(self):
        self._index  = None
        self._chunks: list[dict] = []

    def build(self, embeddings: list[list[float]], chunks: list[dict]) -> None:
        try:
            import faiss
            import numpy as np
        except ImportError:
            raise ImportError("faiss-cpu and numpy required. Run: pip install faiss-cpu numpy")

        dim  = len(embeddings[0])
        vecs = np.array(embeddings, dtype="float32")
        self._index  = faiss.IndexFlatL2(dim)
        self._index.add(vecs)
        self._chunks = chunks

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        import faiss
        import numpy as np
        vec = np.array([query_embedding], dtype="float32")
        _, indices = self._index.search(vec, top_k)
        return [self._chunks[i] for i in indices[0] if i < len(self._chunks)]

    def save(self, directory: str) -> None:
        import faiss
        os.makedirs(directory, exist_ok=True)
        faiss.write_index(self._index, os.path.join(directory, "index.faiss"))
        with open(os.path.join(directory, "index.pkl"), "wb") as f:
            pickle.dump(self._chunks, f)

    def load(self, directory: str) -> None:
        import faiss
        self._index = faiss.read_index(os.path.join(directory, "index.faiss"))
        with open(os.path.join(directory, "index.pkl"), "rb") as f:
            self._chunks = pickle.load(f)
