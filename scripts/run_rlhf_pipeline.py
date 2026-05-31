"""
Run the RLHF (Reinforcement Learning from Human Feedback) pipeline.

Usage :
    python scripts/run_rlhf_pipeline.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from policy_rlhf.feedback_collector import FeedbackCollector
from policy_rlhf.policy_updater import PolicyUpdater
from policy_rlhf.policy_checker import PolicyChecker

FEEDBACK_PATH = "data/rlhf/feedback_store.json"
POLICY_PATH   = "data/policy/policy.json"


def main():
    collector = FeedbackCollector(FEEDBACK_PATH)
    feedback  = collector.load_all()
    print(f"Loaded {len(feedback)} feedback entries.")

    checker = PolicyChecker(POLICY_PATH)
    updater = PolicyUpdater(POLICY_PATH)

    violations = checker.check_all(feedback)
    if violations:
        print(f"Found {len(violations)} policy violations — updating policy...")
        updater.update(violations)
    else:
        print("No policy violations found.")


if __name__ == "__main__":
    main()
