from crewai import Agent
from tools.transaction_db_tool import TransactionHistoryTool

_db_tool = TransactionHistoryTool()

# ── Orchestrator ──────────────────────────────────────────────────────────────
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
    allow_delegation=False,
    verbose=True,
)

# ── Monitor Agent — flags surface-level anomalies ────────────────────────────
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
    verbose=True,
)

# ── Analyst Agent — retrieves and interprets transaction history ──────────────
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
    verbose=True,
)

# ── Risk Score Agent — fuses signals into a 0–100 score ──────────────────────
risk_score_agent = Agent(
    role="Risk Score Calculator",
    goal=(
        "Combine anomaly flags from the Monitor and the behavioral baseline from the Analyst "
        "to produce a single, defensible risk score between 0 and 100."
    ),
    backstory=(
        "You are a quantitative risk modeler who specializes in fusing multiple weak signals "
        "into a single risk score. You weigh each factor carefully and always justify your "
        "final number with concrete evidence."
    ),
    allow_delegation=False,
    verbose=True,
)
