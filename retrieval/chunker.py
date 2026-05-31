import json
import os


class Chunker:
    """Splits documents into overlapping text chunks."""

    def __init__(self, chunk_size: int = 512, overlap: int = 64):
        self.chunk_size = chunk_size
        self.overlap    = overlap

    def chunk(self, document: dict) -> list[dict]:
        text   = document["text"]
        source = document["source"]
        words  = text.split()
        chunks = []
        step   = self.chunk_size - self.overlap
        for i in range(0, len(words), step):
            chunk_words = words[i: i + self.chunk_size]
            chunks.append({
                "source": source,
                "chunk_index": len(chunks),
                "text": " ".join(chunk_words),
            })
        return chunks

    def chunk_all(self, documents: list[dict]) -> list[dict]:
        all_chunks = []
        for doc in documents:
            all_chunks.extend(self.chunk(doc))
        return all_chunks

    def save(self, chunks: list[dict], output_path: str) -> None:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(chunks, f, indent=2)


def load_chunks(path: str) -> list[dict]:
    with open(path) as f:
        return json.load(f)
