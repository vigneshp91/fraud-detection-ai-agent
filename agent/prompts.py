SYSTEM_PROMPT = """You are an AI fraud detection assistant. You analyze financial transactions
and assess their risk level based on anomaly patterns, user history, and behavioral baselines.
Always respond with structured, evidence-based assessments."""

ANOMALY_PROMPT_TEMPLATE = """Analyze the following transaction for anomalies:
{transaction}

Flag any suspicious attributes with clear justification."""

RISK_SCORE_PROMPT_TEMPLATE = """Given the following anomaly flags and behavioral baseline:

Anomalies: {anomalies}
Baseline: {baseline}

Calculate a risk score (0-100) and justify each factor."""

FINAL_REPORT_PROMPT_TEMPLATE = """Synthesize all specialist findings into a final fraud risk report.
Return a JSON object with: risk_score, risk_level, risk_factors, recommendation, summary."""
