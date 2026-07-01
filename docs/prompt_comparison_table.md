# Prompt Comparison — Final Task (Orchestrator)

All three variants were tested on **tc_002** (high-risk late-night foreign transaction:
$2,200 at Unknown Merchant, Lagos Nigeria, 03:47 AM) using identical pre-canned
prior-agent context (anomaly flags, history analysis, risk score).
Run script: `python scripts/run_prompt_comparison.py`

---

## Variant A — Zero-shot

**Prompt (abbreviated):**
```
You are a fraud detection system.
Transaction: { ... }
[Prior agent context]
Return a fraud risk assessment.
```

**Output (excerpt):**
```
**Fraud Risk Assessment for Transaction ID: txn_tc_002**

Given the critical risk score of 88 and the multiple flags raised during the
analysis, this transaction is highly suspicious and warrants immediate review.
It is recommended to place a hold on the transaction and notify the user for
verification before proceeding.
```

**Latency:** 7.81s  
**Parseable by system:** ❌ — free-form markdown, no JSON fields  
**Recommendation extracted:** ❌ — buried as "place a hold" (not APPROVE/REVIEW/BLOCK)  
**Risk level extracted:** ❌ — "CRITICAL" present in prose but not as a structured field

---

## Variant B — Chain-of-thought

**Prompt (abbreviated):**
```
You are a Fraud Detection Orchestrator.
Think step by step:
1. What anomalies stand out?
2. How does this compare to history?
3. What risk score is appropriate?
4. What should the recommendation be — APPROVE, REVIEW, or BLOCK?
Explain your reasoning before giving your final answer.
```

**Output (excerpt):**
```
### 1. Anomalies that Stand Out
- Late Night Transaction: 03:47 AM raises a red flag.
- High-Risk Geography: Lagos, Nigeria is flagged as high-risk.
- Large Amount: $2,200 is 42x the user's average of $52.30.
- Unknown Merchant: not in any recognized database.

### Final Answer
**Recommendation: BLOCK**
```

**Latency:** 11.07s (slowest)  
**Parseable by system:** ⚠️ — requires regex to extract "BLOCK" from prose  
**Recommendation extracted:** ⚠️ — correct value (BLOCK) but embedded in prose  
**Risk level extracted:** ⚠️ — "CRITICAL" mentioned in analysis but no dedicated field

---

## Variant C — Structured output (production)

**Prompt (abbreviated):**
```
You are the Fraud Detection Orchestrator.
...
Return ONLY the JSON object below — no extra text.
Required schema: { risk_score, risk_level, risk_factors, recommendation,
                   summary, escalated, rlhf_adjustment }
```

**Output (full):**
```json
{
  "risk_score": 88,
  "risk_level": "CRITICAL",
  "risk_factors": [
    "Late-night (03:47 AM) — high-risk time window (+25 pts per policy)",
    "High-fraud geography: Lagos, Nigeria (+25 pts per policy)",
    "Amount 42x above user's historical average (+20 pts)",
    "Unknown merchant — no record in database (+20 pts)",
    "Category never used before by this user (+10 pts)"
  ],
  "recommendation": "BLOCK",
  "summary": "The transaction presents multiple high-risk indicators ...",
  "escalated": true,
  "rlhf_adjustment": null
}
```

**Latency:** 4.04s (fastest — 2.7× faster than Variant B)  
**Parseable by system:** ✅ — direct `json.loads()`, zero post-processing  
**Recommendation extracted:** ✅ — `output["recommendation"]` → `"BLOCK"`  
**Risk level extracted:** ✅ — `output["risk_level"]` → `"CRITICAL"`

---

## Comparison Table

| Dimension | A — Zero-shot | B — Chain-of-thought | C — Structured output |
|---|---|---|---|
| **Format compliance** | ❌ Markdown prose | ⚠️ Prose + bold header | ✅ Valid JSON |
| **Machine-parseable** | ❌ | ⚠️ Regex required | ✅ `json.loads()` |
| **Recommendation field** | ❌ Not extractable | ⚠️ Regex on "BLOCK" | ✅ Exact key |
| **Risk level field** | ❌ In prose only | ⚠️ In prose only | ✅ Exact key |
| **Reasoning visible** | ✅ Narrative | ✅ Numbered steps | ✅ `risk_factors` list |
| **Latency** | 7.81s | 11.07s | **4.04s** |
| **Token cost** | Medium | High | Medium |
| **Consistent across runs** | Low | Medium | High |

---

## Decision and Justification

**Variant C (Structured output) was chosen for the Orchestrator's final task.**

Key reasons:
1. **Automated parsing**: The downstream system (`crew.kickoff()` → `json.loads()`) needs
   a machine-readable response. Variant A and B require custom extractors that break on
   minor phrasing changes.
2. **Fastest latency**: 4.04s vs 7.81s (A) and 11.07s (B) — structured prompts reduce
   the model's output length by eliminating narrative filler.
3. **Deterministic field names**: `recommendation`, `risk_level`, and `escalated` are
   always present and correctly typed; no regex or heuristic needed.
4. **Reasoning is still visible**: The `risk_factors` list and `summary` field preserve
   explainability — we don't lose the "why."

**Variant B (Chain-of-thought) was retained for intermediate agents** (Monitor, Analyst,
Risk Calculator) where the output is consumed by the next agent as free text, so format
compliance is less critical and visible reasoning improves downstream agent quality.
