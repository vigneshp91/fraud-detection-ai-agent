import json
import logging
import os
from datetime import datetime, timezone
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

_ESCALATIONS_LOG = os.path.join(
    os.path.dirname(__file__), "..", "logs", "escalations.log"
)


def _append_escalation(payload: dict) -> None:
    os.makedirs(os.path.dirname(_ESCALATIONS_LOG), exist_ok=True)
    with open(_ESCALATIONS_LOG, "a") as f:
        f.write(json.dumps(payload) + "\n")


class EscalationInput(BaseModel):
    transaction_id: str = Field(description="The transaction ID to escalate")
    reason: str = Field(description="Why this transaction is being escalated")
    risk_score: int = Field(description="The assessed risk score (0-100)", ge=0, le=100)


class EscalationTool(BaseTool):
    name: str = "escalate_case"
    description: str = (
        "Escalates a high-risk transaction to the human fraud review team. "
        "Use when risk_score >= 61 or when automated analysis is inconclusive."
    )
    args_schema: type[BaseModel] = EscalationInput

    def _run(self, transaction_id: str, reason: str, risk_score: int) -> str:
        payload = {
            "transaction_id": transaction_id,
            "risk_score":     risk_score,
            "reason":         reason,
            "status":         "ESCALATED",
            "timestamp":      datetime.now(tz=timezone.utc).isoformat(),
        }
        logger.warning("ESCALATION: %s", json.dumps(payload))
        _append_escalation(payload)
        return json.dumps({
            "escalated":      True,
            "transaction_id": transaction_id,
            "message":        "Case routed to fraud review team.",
        })
