import json
import os
from datetime import datetime


class FeedbackCollector:
    """Loads and appends human feedback to the feedback store."""

    def __init__(self, store_path: str):
        self.store_path = store_path

    def load_all(self) -> list[dict]:
        if not os.path.exists(self.store_path):
            return []
        with open(self.store_path) as f:
            return json.load(f)

    def record(self, transaction_id: str, rating: int, comment: str = "") -> None:
        """Append a feedback entry (rating 1–5) for a transaction."""
        entries = self.load_all()
        entries.append({
            "transaction_id": transaction_id,
            "rating": rating,
            "comment": comment,
            "timestamp": datetime.utcnow().isoformat(),
        })
        os.makedirs(os.path.dirname(self.store_path), exist_ok=True)
        with open(self.store_path, "w") as f:
            json.dump(entries, f, indent=2)
