"""
FastAPI wrapper for the AI Fraud Detection Agent.

    uvicorn deployment.app:app --reload

POST /analyze   — analyze a transaction, returns a fraud risk report
GET  /health    — liveness check
"""
from __future__ import annotations

import asyncio
import json
import time
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

load_dotenv()

from data.setup_db import setup_database
setup_database()

from agent.core_agent import build_crew
from deployment.config import settings
from monitoring.langfuse_logger import LangfuseLogger

_tracer = LangfuseLogger()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    # Flush any buffered Langfuse events on shutdown so no traces are lost.
    _tracer.flush()


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    lifespan=lifespan,
)


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


@app.post(
    "/analyze",
    response_model=FraudReport,
    tags=["fraud"],
    responses={500: {"description": "Agent error or non-JSON output"}},
)
async def analyze(transaction: TransactionRequest):
    """Analyze a financial transaction and return a fraud risk report."""
    tx_dict = transaction.model_dump()
    with _tracer.observe(
        name=f"analyze/{transaction.transaction_id}",
        as_type="span",
        input=tx_dict,
        metadata={"user_id": transaction.user_id},
    ) as obs:
        t0 = time.perf_counter()
        try:
            report = await asyncio.to_thread(_run_crew_sync, tx_dict)
        except ValueError as e:
            obs.update(output={"error": str(e)})
            _tracer.flush()
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            obs.update(output={"error": str(e)})
            _tracer.flush()
            raise HTTPException(status_code=500, detail=f"Agent error: {e}")

        latency_s = round(time.perf_counter() - t0, 2)
        obs.update(output=report)
        obs.score_trace(name="latency_s", value=latency_s)

    _tracer.flush()
    return report
