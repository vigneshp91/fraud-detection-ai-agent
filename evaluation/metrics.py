def compute_metrics(results: list[dict]) -> dict:
    """Compute pass rate, latency stats, and per-risk-level breakdown."""
    total  = len(results)
    passed = sum(1 for r in results if r["passed"])

    latencies = [r["latency_s"] for r in results if "latency_s" in r]
    avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
    max_latency = round(max(latencies), 2) if latencies else 0.0

    level_counts: dict = {}
    for r in results:
        level  = r["expected"].get("risk_level", "UNKNOWN")
        bucket = level_counts.setdefault(level, {"total": 0, "passed": 0})
        bucket["total"] += 1
        if r["passed"]:
            bucket["passed"] += 1

    return {
        "total_cases":   total,
        "passed":        passed,
        "failed":        total - passed,
        "pass_rate_pct": round(passed / total * 100, 1) if total else 0.0,
        "avg_latency_s": avg_latency,
        "max_latency_s": max_latency,
        "by_risk_level": level_counts,
    }
