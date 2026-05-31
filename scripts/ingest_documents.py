"""
Ingest raw documents from knowledge/raw/ into knowledge/processed/chunks.json.

Usage :
    python scripts/ingest_documents.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval.document_loader import DocumentLoader
from retrieval.chunker import Chunker

RAW_DIR     = "knowledge/raw"
OUTPUT_PATH = "knowledge/processed/chunks.json"


def main():
    loader  = DocumentLoader(RAW_DIR)
    chunker = Chunker(chunk_size=512, overlap=64)

    print(f"Loading documents from {RAW_DIR}...")
    documents = loader.load_all()
    print(f"Loaded {len(documents)} documents.")

    chunks = chunker.chunk_all(documents)
    print(f"Generated {len(chunks)} chunks.")

    chunker.save(chunks, OUTPUT_PATH)
    print(f"Chunks saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
