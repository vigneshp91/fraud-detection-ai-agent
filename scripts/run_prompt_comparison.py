"""
Prompt comparison experiment — runs 3 prompt strategies on the same transaction
through the Orchestrator LLM call only (bypassing the full crew for speed).

Prior-agent outputs are pre-canned to isolate the effect of the final-task prompt.

Usage:
    python scripts/run_prompt_comparison.py
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
)
MODEL = "gpt-4o-mini"

# ── Fixed inputs (tc_002 — high-risk late-night foreign transaction) ──────────

TRANSACTION = {
    "transaction_id": "txn_tc_002",
    "user_id": "user_003",
    "amount": 2200.00,
    "merchant": "Unknown Merchant",
    "category": "online",
    "location": "Lagos, Nigeria",
    "timestamp": "2026-04-26 03:47:00",
}

# Pre-canned outputs from the first three agents (identical for all variants)
ANOMALY_FLAGS = """
- LATE NIGHT: Transaction at 03:47 AM — highly unusual hour
- HIGH-RISK GEOGRAPHY: Lagos, Nigeria is flagged as a high-fraud location
- LARGE AMOUNT: $2,200 significantly exceeds typical transaction sizes
- UNKNOWN MERCHANT: Merchant name not recognized in any known merchant database
"""

HISTORY_ANALYSIS = """
User user_003 historical baseline (last 30 transactions):
- avg_amount: $52.30  |  max_amount: $210.00
- typical locations: Chicago IL, Detroit MI
- top categories: grocery, restaurant, gas
- fraud_count_in_last30: 0
Deviations from this transaction:
- Amount 42x above average
- Location never seen before
- Category never transacted online
- Time: no prior 2–5 AM transactions
"""

RISK_SCORE_ANALYSIS = """
preliminary_risk_score: 88
risk_level: CRITICAL
risk_factors:
  - Late-night (03:47 AM) — high-risk time window (+25 pts per policy)
  - High-fraud geography: Lagos, Nigeria (+25 pts per policy)
  - Amount 42x above user's historical average (+20 pts)
  - Unknown merchant — no record in database (+20 pts)
  - Category never used before by this user (+10 pts)
policy_chunks_used: Section 2 (high-risk indicators) and Section 1 (thresholds)
"""

TX_STR = json.dumps(TRANSACTION, indent=2)

CONTEXT_BLOCK = f"""
Prior agent outputs:
ANOMALY FLAGS:
{ANOMALY_FLAGS}
HISTORY ANALYSIS:
{HISTORY_ANALYSIS}
RISK SCORE:
{RISK_SCORE_ANALYSIS}
"""

# ── Variant A: Zero-shot ──────────────────────────────────────────────────────

PROMPT_A = f"""You are a fraud detection system.

Transaction:
{TX_STR}

{CONTEXT_BLOCK}

Return a fraud risk assessment."""

# ── Variant B: Chain-of-thought (no structured schema) ───────────────────────

PROMPT_B = f"""You are a Fraud Detection Orchestrator reviewing a transaction.

Transaction:
{TX_STR}

{CONTEXT_BLOCK}

Think step by step:
1. What anomalies stand out?
2. How does this compare to the user's history?
3. What risk score is appropriate?
4. What should the recommendation be — APPROVE, REVIEW, or BLOCK?

Explain your reasoning before giving your final answer."""

# ── Variant C: Structured output (current production prompt) ─────────────────

PROMPT_C = f"""You are the Fraud Detection Orchestrator. Review all specialist agent findings
and produce the definitive fraud risk report.

Transaction:
{TX_STR}

{CONTEXT_BLOCK}

Your job:
1. Validate and reconcile all findings.
2. Confirm or adjust the risk score.
3. Issue the final recommendation: APPROVE / REVIEW / BLOCK.
4. If risk_score >= 61, set escalated to true.
5. Return ONLY the JSON object below — no extra text.

Required JSON schema:
{{
  "risk_score": <int 0-100>,
  "risk_level": "<LOW|MEDIUM|HIGH|CRITICAL>",
  "risk_factors": ["<string>", ...],
  "recommendation": "<APPROVE|REVIEW|BLOCK>",
  "summary": "<one paragraph>",
  "escalated": <true|false>,
  "rlhf_adjustment": null
}}"""


def call(prompt: str, label: str) -> dict:
    print(f"\n{'='*60}\nVariant {label}\n{'='*60}")
    t0 = time.perf_counter()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    latency = round(time.perf_counter() - t0, 2)
    raw = response.choices[0].message.content.strip()
    print(f"[latency: {latency}s]\n{raw[:600]}")
    return {"label": label, "raw": raw, "latency_s": latency}


if __name__ == "__main__":
    results = []
    results.append(call(PROMPT_A, "A — Zero-shot"))
    results.append(call(PROMPT_B, "B — Chain-of-thought"))
    results.append(call(PROMPT_C, "C — Structured output (production)"))

    out_path = "data/evaluation/prompt_comparison_results.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {out_path}")
