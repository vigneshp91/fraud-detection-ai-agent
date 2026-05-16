"""
FastAPI wrapper for the AI Fraud Detection Agent.

Run:
    uvicorn api:app --reload

POST /analyze   — analyze a transaction, returns a fraud risk report
GET  /health    — liveness check
"""
from __future__ import annotations

import asyncio
import json

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

load_dotenv()

# Seed the DB on startup (no-op if already seeded)
from data.setup_db import setup_database
setup_database()

from crew import build_crew

app = FastAPI(title="AI Fraud Detection Agent", version="1.0.0")


# ── Request / Response models ──────────────────────────────────────────────────

class TransactionRequest(BaseModel):
    transaction_id: str = Field(example="txn_001")
    user_id: str = Field(example="user_001")
    amount: float = Field(example=2200.00)
    merchant: str = Field(example="Unknown Merchant")
    category: str = Field(example="online")
    location: str = Field(example="Lagos, Nigeria")
    timestamp: str = Field(example="2026-04-26 03:47:00")


class FraudReport(BaseModel):
    risk_score: int
    risk_level: str
    risk_factors: list[str]
    recommendation: str
    summary: str


# ── Helpers ────────────────────────────────────────────────────────────────────

def _parse_crew_output(result) -> dict:
    raw = result.raw if hasattr(result, "raw") else str(result)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    return json.loads(raw)


def _run_crew_sync(tx: dict) -> dict:
    """Blocking call — runs in a thread so the event loop stays free."""
    crew = build_crew(tx)
    result = crew.kickoff()
    try:
        return _parse_crew_output(result)
    except json.JSONDecodeError as e:
        raise ValueError(f"Agent returned non-JSON output: {e}")


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["ops"])
def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=FraudReport, tags=["fraud"], responses={500: {"description": "Agent error or non-JSON output"}})
async def analyze(transaction: TransactionRequest):
    """
    Analyze a financial transaction and return a fraud risk report.

    The crew runs in a background thread so the async event loop is never blocked.
    """
    tx_dict = transaction.model_dump()
    try:
        report = await asyncio.to_thread(_run_crew_sync, tx_dict)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")
    return report
