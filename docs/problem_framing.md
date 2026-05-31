# Problem Framing

## Problem Statement
Financial fraud costs institutions billions annually. Manual review is too slow and error-prone at scale. This project builds an AI agent system that automates fraud risk assessment for individual transactions in real time.

## Scope
- **Input**: A single financial transaction (user ID, amount, merchant, category, location, timestamp).
- **Output**: A structured fraud risk report (risk score 0–100, risk level, risk factors, recommendation).

## Agents
| Agent | Role |
|---|---|
| Transaction Anomaly Monitor | Flags surface-level anomalies (time, location, amount, merchant) |
| Transaction History Analyst | Retrieves user history and builds a behavioral baseline |
| Risk Score Calculator | Fuses anomaly flags and baseline into a 0–100 risk score |
| Fraud Detection Orchestrator | Synthesizes all findings into the final report |

## Success Criteria
- Correct risk level classification on ≥ 90% of test cases.
- API response time < 60 seconds per transaction.
- No PII leakage in logs or outputs.
