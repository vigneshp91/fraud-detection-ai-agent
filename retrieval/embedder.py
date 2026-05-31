from __future__ import annotations
import os


class Embedder:
    """Generates text embeddings using OpenAI or a local model."""

    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
            response = client.embeddings.create(model=self.model, input=texts)
            return [item.embedding for item in response.data]
        except ImportError:
            raise ImportError("openai package required. Run: pip install openai")

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]
