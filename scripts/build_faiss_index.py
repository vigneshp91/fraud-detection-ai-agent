"""
Build the FAISS vector index from processed document chunks.

Usage :
    python scripts/build_faiss_index.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval.embedder import Embedder
from retrieval.faiss_store import FAISSStore
from retrieval.chunker import load_chunks

CHUNKS_PATH  = "knowledge/processed/chunks.json"
INDEX_DIR    = "knowledge/faiss_index"


def main():
    print("Loading chunks...")
    chunks = load_chunks(CHUNKS_PATH)
    print(f"Loaded {len(chunks)} chunks.")

    embedder = Embedder()
    texts = [c["text"] for c in chunks]
    print("Generating embeddings...")
    embeddings = embedder.embed(texts)

    store = FAISSStore()
    store.build(embeddings, chunks)
    store.save(INDEX_DIR)
    print(f"FAISS index saved to {INDEX_DIR}/")


if __name__ == "__main__":
    main()
