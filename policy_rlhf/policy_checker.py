import json
import os


class PolicyChecker:
    """Checks agent outputs and feedback against the current policy rules."""

    def __init__(self, policy_path: str):
        self.policy_path = policy_path
        self._policy = self._load()

    def _load(self) -> dict:
        if not os.path.exists(self.policy_path):
            return {"rules": []}
        with open(self.policy_path) as f:
            return json.load(f)

    def check(self, feedback_entry: dict) -> list[str]:
        """Return a list of violated rule IDs for this feedback entry."""
        violations = []
        for rule in self._policy.get("rules", []):
            if self._violates(feedback_entry, rule):
                violations.append(rule["id"])
        return violations

    def check_all(self, feedback: list[dict]) -> list[dict]:
        results = []
        for entry in feedback:
            violated = self.check(entry)
            if violated:
                results.append({"entry": entry, "violated_rules": violated})
        return results

    def _violates(self, entry: dict, rule: dict) -> bool:
        # Extend with real rule-matching logic per rule type
        return False
