"""
Evaluation harness — runs test cases through the fraud-detection crew and
records each result as a Langfuse trace with correctness + latency scores.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone

from monitoring.langfuse_logger import LangfuseLogger

_tracer = LangfuseLogger()

EVAL_SESSION_ID = f"eval-{datetime.now(tz=timezone.utc).strftime('%Y%m%dT%H%M%S')}"


class TestHarness:
    """Runs test cases against the fraud detection agent and records results."""

    def __init__(self, test_cases_path: str):
        self.test_cases_path = test_cases_path
        self._cases = self._load()

    def _load(self) -> list[dict]:
        if not os.path.exists(self.test_cases_path):
            return []
        with open(self.test_cases_path) as f:
            return json.load(f)

    def run_all(self) -> list[dict]:
        from agent.core_agent import build_crew

        results = []
        for case in self._cases:
            case_id  = case.get("id", "unknown")
            tx       = case["input"]
            expected = case.get("expected", {})

            t0 = time.perf_counter()
            output: dict = {}
            passed = False

            # Each test case becomes one Langfuse trace (as_type="evaluator").
            with _tracer.observe(
                name=f"eval/{case_id}",
                as_type="evaluator",
                input={"transaction": tx, "expected": expected},
                metadata={"case_id": case_id, "session_id": EVAL_SESSION_ID},
            ) as obs:
                try:
                    crew   = build_crew(tx)
                    result = crew.kickoff()
                    raw    = result.raw if hasattr(result, "raw") else str(result)

                    # Strip markdown fences the LLM may wrap around the JSON
                    raw = raw.strip()
                    if raw.startswith("```"):
                        raw = raw.split("```")[1]
                        if raw.startswith("json"):
                            raw = raw[4:]
                        raw = raw.strip()

                    output = json.loads(raw)
                    passed = output.get("risk_level") == expected.get("risk_level")

                except Exception as exc:
                    output = {"error": str(exc)}
                    passed = False

                latency_s = round(time.perf_counter() - t0, 2)

                # Persist the crew output on the trace
                obs.update(output=output)

                # Score 1: correctness (1 = pass, 0 = fail) — numeric
                obs.score_trace(
                    name="correctness",
                    value=1.0 if passed else 0.0,
                    comment=(
                        f"Expected risk_level={expected.get('risk_level')}, "
                        f"got risk_level={output.get('risk_level')}. "
                        f"Expected recommendation={expected.get('recommendation')}, "
                        f"got recommendation={output.get('recommendation')}."
                    ),
                )

                # Score 2: latency in seconds — numeric
                obs.score_trace(
                    name="latency_s",
                    value=latency_s,
                    comment=f"Crew completed in {latency_s}s for case {case_id}",
                )

            results.append({
                "case_id":   case_id,
                "passed":    passed,
                "expected":  expected,
                "actual":    output,
                "latency_s": latency_s,
            })

            # Flush after each case so the trace appears in Langfuse immediately,
            # rather than waiting until the entire evaluation run is complete.
            _tracer.flush()

        return results
