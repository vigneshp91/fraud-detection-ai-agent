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

    def record(
        self,
        transaction_id: str,
        rating: int,
        comment: str = "",
        transaction_meta: dict | None = None,
    ) -> None:
        """Append a feedback entry (rating 1–5) for a transaction.

        transaction_meta should contain the fields needed for feedback-loop
        context injection: category, merchant, location, amount, risk_level,
        risk_score, recommendation.
        """
        entries = self.load_all()
        entry: dict = {
            "transaction_id": transaction_id,
            "rating":         rating,
            "comment":        comment,
            "timestamp":      datetime.utcnow().isoformat(),
        }
        if transaction_meta:
            entry["transaction_meta"] = transaction_meta
        entries.append(entry)
        os.makedirs(os.path.dirname(self.store_path), exist_ok=True)
        with open(self.store_path, "w") as f:
            json.dump(entries, f, indent=2)
