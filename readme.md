# AI Fraud Detection Agent — Capstone

A multi-agent fraud detection system built with CrewAI. Analyzes financial transactions through a pipeline of specialist agents and returns a structured risk report.

## Quickstart

```bash
pip install -r requirements.txt
cp .env.example .env          # add your OPENAI_API_KEY
python data/setup_db.py       # seed the SQLite transaction database
python demo_agent/scripts/run_agent.py   # run the CLI demo
```

## Run the API

```bash
uvicorn deployment.app:app --reload
# Open http://localhost:8000/docs
```

The server starts at `http://localhost:8000`.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness check |
| `POST` | `/analyze` | Analyze a transaction |

Interactive docs (Swagger UI): `http://localhost:8000/docs`

#### Example request

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "txn_high_001",
    "user_id": "user_003",
    "amount": 2200.00,
    "merchant": "Unknown Merchant",
    "category": "online",
    "location": "Lagos, Nigeria",
    "timestamp": "2026-04-26 03:47:00"
  }'
```

#### Example response

```json
{
  "risk_score": 91,
  "risk_level": "CRITICAL",
  "risk_factors": [
    "Transaction at 3:47 AM — outside normal hours",
    "Location 'Lagos, Nigeria' not seen in user history",
    "Amount $2,200 is 10x above user average",
    "Unknown merchant with no prior history"
  ],
  "recommendation": "BLOCK",
  "summary": "This transaction exhibits multiple high-risk signals..."
}
```

## Risk levels

| Score | Level | Recommendation |
|-------|-------|----------------|
| 0 – 25 | LOW | APPROVE |
| 26 – 60 | MEDIUM | REVIEW |
| 61 – 85 | HIGH | BLOCK |
| 86 – 100 | CRITICAL | BLOCK |


## Run Evaluation
```bash
pip install -r requirements.txt
cp .env.example .env          # add your OPENAI_API_KEY
python scripts/run_evaluation.py
```


## Project Structure

| Directory | Purpose |
|---|---|
| `agent/` | Agent definitions, crew builder, task planner, prompts, memory |
| `tools/` | CrewAI tools — DB lookup, escalation, tool registry |
| `retrieval/` | RAG pipeline — document loader, chunker, embedder, FAISS store |
| `data/` | SQLite DB, policy rules, RLHF feedback, evaluation test cases |
| `knowledge/` | Raw documents, processed chunks, FAISS index |
| `deployment/` | FastAPI app and config |
| `scripts/` | CLI entry points for all pipelines |
| `safety/` | Guardrails and PII filter |
| `monitoring/` | LangSmith and Langfuse integrations |
| `evaluation/` | Test harness and metrics |
| `policy_rlhf/` | Policy checker, feedback collector, policy updater |
| `mcp/` | Model Context Protocol server and client |
| `docs/` | Problem framing, demo script, evaluation report, engineering justification |
| `logs/` | Runtime logs |

## Agents

1. **Transaction Anomaly Monitor** — flags unusual time, location, amount, or merchant.
2. **Transaction History Analyst** — retrieves user history and builds a behavioral baseline.
3. **Risk Score Calculator** — fuses signals into a 0–100 risk score.
4. **Fraud Detection Orchestrator** — synthesizes findings into the final JSON report.

## Output Schema

```json
{
  "risk_score": 87,
  "risk_level": "CRITICAL",
  "risk_factors": ["3 AM transaction", "High-risk geography", "Amount 10x user average"],
  "recommendation": "BLOCK",
  "summary": "..."
}
```
