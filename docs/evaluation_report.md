# Evaluation Report

## Test Suite
- **Total cases**: 3 (see `data/evaluation/test_cases.json`)
- **Risk levels covered**: LOW, MEDIUM, HIGH

## Metrics

| Metric | Value |
|---|---|
| Pass rate | TBD — run `python scripts/run_evaluation.py` |
| Avg latency | TBD |
| JSON parse success rate | TBD |

## Known Failure Modes
- The LLM occasionally wraps JSON in markdown code fences; the output parser handles this but adds latency.
- MEDIUM risk cases (score 26–60) are the hardest to classify consistently — the boundary with LOW is context-dependent.

## Recommendations
- Expand test suite to ≥ 20 cases per risk tier.
- Add latency benchmarks per agent step.
- Integrate evaluation into CI via `scripts/run_evaluation.py`.
