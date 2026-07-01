import json
from crewai import Agent, Crew, Process
from tools.mcp_transaction_tool import MCPTransactionHistoryTool
from tools.mcp_escalation_tool import MCPEscalationTool
from tools.mcp_retrieval_tool import MCPRetrievalTool

_db_tool         = MCPTransactionHistoryTool()
_escalation_tool = MCPEscalationTool()
_retrieval_tool  = MCPRetrievalTool()

# ── Orchestrator ───────────────────────────────────────────────────────────────
fraud_detection_agent = Agent(
    role="Fraud Detection Orchestrator",
    goal=(
        "Coordinate the full fraud analysis pipeline by delegating to specialist agents, "
        "then synthesize their findings into a final structured fraud risk report."
    ),
    backstory=(
        "You are the head of a fraud operations center with 20 years of experience. "
        "You manage a team of specialist analysts and ensure every transaction receives "
        "a thorough, multi-dimensional fraud assessment before a decision is made."
    ),
    tools=[_escalation_tool],
    allow_delegation=False,

)

# ── Monitor Agent — flags surface-level anomalies ─────────────────────────────
monitor_agent = Agent(
    role="Transaction Anomaly Monitor",
    goal=(
        "Examine the raw transaction data and flag surface-level anomalies: "
        "unusual time, suspicious location, unexpected amount, or unfamiliar merchant."
    ),
    backstory=(
        "You are a real-time transaction monitoring specialist with a sharp eye for "
        "anything out of place — an odd hour, a risky geography, or an unusually large "
        "purchase — before deeper analysis begins."
    ),
    allow_delegation=False,
    
)

# ── Analyst Agent — retrieves and interprets transaction history ───────────────
analyst_agent = Agent(
    role="Transaction History Analyst",
    goal=(
        "Retrieve the user's transaction history and build a behavioral baseline: "
        "typical spend amounts, frequent locations, common categories, and past fraud flags."
    ),
    backstory=(
        "You are a behavioral analytics expert who mines historical transaction data "
        "to understand a customer's normal financial patterns, so that deviations stand out clearly."
    ),
    tools=[_db_tool],
    allow_delegation=False,
    
)

# ── Risk Score Agent — fuses signals into a 0–100 score ───────────────────────
risk_score_agent = Agent(
    role="Risk Score Calculator",
    goal=(
        "Combine anomaly flags from the Monitor and the behavioral baseline from the Analyst "
        "to produce a single, defensible risk score between 0 and 100, backed by policy rules."
    ),
    backstory=(
        "You are a quantitative risk modeler who specializes in fusing multiple weak signals "
        "into a single risk score. You always consult the official fraud detection policy "
        "before scoring, so every number you produce is grounded in written guidelines."
    ),
    tools=[_retrieval_tool],
    allow_delegation=False,
)


def build_crew(transaction_json: dict, session_memory=None) -> Crew:
    import os
    from agent.planner import create_tasks
    from policy_rlhf.feedback_context import build_feedback_context

    _feedback_store_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "rlhf", "feedback_store.json"
    )
    feedback_context = build_feedback_context(_feedback_store_path)

    memory_context = ""
    if session_memory is not None and len(session_memory) > 0:
        lines = []
        history = session_memory.get_history()
        for entry in history:
            role = "Transaction" if entry["role"] == "user" else "Decision"
            lines.append(f"  [{role}] {entry['content']}")
        memory_context = "PRIOR DECISIONS IN THIS SESSION:\n" + "\n".join(lines)

    tx_str = json.dumps(transaction_json, indent=2)
    anomaly_task, history_task, risk_task, final_task = create_tasks(
        tx_str, feedback_context=feedback_context, memory_context=memory_context
    )
    return Crew(
        agents=[monitor_agent, analyst_agent, risk_score_agent, fraud_detection_agent],
        tasks=[anomaly_task, history_task, risk_task, final_task],
        process=Process.sequential,
        verbose=True,
    )
