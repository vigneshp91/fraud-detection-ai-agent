# Demo Script

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env  # fill in OPENAI_API_KEY
python data/setup_db.py
```

## Run CLI Demo
```bash
python scripts/run_agent.py
```
Walk through the three built-in scenarios (low / medium / high risk) and explain the agent reasoning at each step.

## Run API Demo
```bash
uvicorn deployment.app:app --reload
```
Open `http://localhost:8000/docs` and POST to `/analyze` with the high-risk payload:
```json
{
  "transaction_id": "txn_demo_001",
  "user_id": "user_003",
  "amount": 2200.00,
  "merchant": "Unknown Merchant",
  "category": "online",
  "location": "Lagos, Nigeria",
  "timestamp": "2026-04-26 03:47:00"
}
```

## Key Talking Points
1. Multi-agent specialization — each agent has a focused role.
2. Tool use — the Analyst agent queries a real SQLite database.
3. Structured output — the Orchestrator returns validated JSON.
4. Safety — PII filter and guardrails protect every input/output.
