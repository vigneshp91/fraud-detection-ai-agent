# AI Fraud Detection Agent

An intelligent fraud detection system powered by agentic AI (CrewAI + Claude) that analyzes financial transactions and returns a structured risk report.

## Architecture

Four agents run sequentially, each passing context to the next:

```
Transaction in
      │
      ▼
 Monitor Agent          ← flags anomalies (time, location, amount, merchant)
      │
      ▼
 Analyst Agent          ← fetches user history from SQLite, builds baseline
      │
      ▼
 Risk Score Agent       ← combines signals into a preliminary 0–100 score
      │
      ▼
 Orchestrator Agent     ← reconciles all findings, issues final verdict
      │
      ▼
 JSON Report out        ← risk_score, risk_level, risk_factors, recommendation, summary
```

## Installation

```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

## Running

### CLI (demo mode)

Runs three built-in demo transactions (low / medium / high risk):

```bash
python main.py
```

Pass a custom transaction as a JSON string:

```bash
python main.py '{"transaction_id":"txn_001","user_id":"user_001","amount":4500,"merchant":"Unknown Merchant","category":"online","location":"Lagos, Nigeria","timestamp":"2026-04-26 03:47:00"}'
```

### API server

```bash
uvicorn api:app --reload
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

## Configuration

Set model and environment variables in `.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
```

## License

MIT
