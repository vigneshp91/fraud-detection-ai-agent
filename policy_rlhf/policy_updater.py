import json
import os
from datetime import datetime


class PolicyUpdater:
    """Updates policy rules based on detected violations from human feedback."""

    def __init__(self, policy_path: str):
        self.policy_path = policy_path

    def _load(self) -> dict:
        if not os.path.exists(self.policy_path):
            return {"rules": [], "version": 1, "updated_at": None}
        with open(self.policy_path) as f:
            return json.load(f)

    def _save(self, policy: dict) -> None:
        os.makedirs(os.path.dirname(self.policy_path), exist_ok=True)
        policy["updated_at"] = datetime.utcnow().isoformat()
        with open(self.policy_path, "w") as f:
            json.dump(policy, f, indent=2)

    def update(self, violations: list[dict]) -> None:
        """Increment violation counts and flag rules for review."""
        policy = self._load()
        rule_map = {r["id"]: r for r in policy.get("rules", [])}

        for v in violations:
            for rule_id in v.get("violated_rules", []):
                if rule_id in rule_map:
                    rule_map[rule_id]["violation_count"] = rule_map[rule_id].get("violation_count", 0) + 1

        policy["rules"] = list(rule_map.values())
        policy["version"] = policy.get("version", 1) + 1
        self._save(policy)
