"""
Run the evaluation harness against test_cases.json.
Each test case is traced in Langfuse with correctness and latency scores.

Usage (run from project root):
    python scripts/run_evaluation.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from data.setup_db import setup_database
setup_database()

from evaluation.test_harness import TestHarness, _tracer, EVAL_SESSION_ID
from evaluation.metrics import compute_metrics

TEST_CASES_PATH = "data/evaluation/test_cases.json"


def main():
    if _tracer.is_enabled():
        print(f"Langfuse tracing enabled  (session: {EVAL_SESSION_ID})")
    else:
        print("Langfuse tracing disabled — set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY to enable.")

    harness = TestHarness(TEST_CASES_PATH)
    results = harness.run_all()

    metrics = compute_metrics(results)

    print("\n=== EVALUATION RESULTS ===")
    print(f"  total_cases   : {metrics['total_cases']}")
    print(f"  passed        : {metrics['passed']}")
    print(f"  failed        : {metrics['failed']}")
    print(f"  pass_rate     : {metrics['pass_rate_pct']}%")
    print(f"  avg_latency_s : {metrics['avg_latency_s']}s")
    print(f"  max_latency_s : {metrics['max_latency_s']}s")
    print("\n  by_risk_level:")
    for level, counts in metrics["by_risk_level"].items():
        pct = round(counts["passed"] / counts["total"] * 100, 1) if counts["total"] else 0
        print(f"    {level:10s}  {counts['passed']}/{counts['total']}  ({pct}%)")

    print("\n  per-case detail:")
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(
            f"    [{status}] {r['case_id']:12s}  "
            f"expected={r['expected'].get('risk_level'):8s}  "
            f"actual={r['actual'].get('risk_level', 'ERROR'):8s}  "
            f"latency={r['latency_s']}s"
        )

    # Flush Langfuse after all cases are logged
    _tracer.flush()
    if _tracer.is_enabled():
        print(f"\nTraces sent to Langfuse (session: {EVAL_SESSION_ID})")


if __name__ == "__main__":
    main()
