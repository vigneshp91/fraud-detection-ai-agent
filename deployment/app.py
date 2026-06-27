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
from logs.logging_utils import new_request_id, log_event
from safety.guardrails import Guardrails

_tracer = LangfuseLogger()
_guardrails = Guardrails()


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
    escalated: bool = False
    rlhf_adjustment: str | None = None


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
    # Sanitize, mask PII, and check for prompt injection before sending to agents
    sanitized_tx = {
        k: _guardrails.mask_pii(_guardrails.sanitize(v)) if isinstance(v, str) else v
        for k, v in tx.items()
    }
    combined_input = " ".join(str(v) for v in sanitized_tx.values())
    is_safe, reason = _guardrails.check_input(combined_input)
    if not is_safe:
        raise ValueError(f"Input blocked by guardrails: {reason}")
    log_event("Input sanitized, PII masked, and passed guardrail checks.", new_request_id(), input=sanitized_tx)
    crew = build_crew(sanitized_tx)
    result = crew.kickoff()

    # Mask PII in agent output and check before returning
    # raw = result.raw if hasattr(result, "raw") else str(result)
    # raw = _guardrails.mask_pii(raw)
    # if hasattr(result, "raw"):
    #     result.raw = raw
    # is_safe, reason = _guardrails.check_output(raw)
    # if not is_safe:
    #     raise ValueError(f"Output blocked by guardrails: {reason}")

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
    request_id = new_request_id()
    log_event("http_request", request_id, path="/analyze")

    log_event("Analyze a financial transaction and return a fraud risk report.",request_id)
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
