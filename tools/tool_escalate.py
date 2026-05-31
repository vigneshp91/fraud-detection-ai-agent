import json
import logging
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


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
            "risk_score": risk_score,
            "reason": reason,
            "status": "ESCALATED",
        }
        logger.warning("ESCALATION: %s", json.dumps(payload))
        return json.dumps({"escalated": True, "transaction_id": transaction_id, "message": "Case routed to fraud review team."})
