from crewai import Task
from agent.core_agent import monitor_agent, analyst_agent, risk_score_agent, fraud_detection_agent


def create_tasks(transaction_str: str, feedback_context: str = "", memory_context: str = "") -> tuple[Task, Task, Task, Task]:
    """Return fresh Task objects for each run so descriptions are never mutated."""

    anomaly_detection_task = Task(
        description=(
            "Examine this incoming transaction for surface-level anomalies.\n\n"
            f"INCOMING TRANSACTION:\n{transaction_str}\n\n"
            "Check for:\n"
            "- Unusual transaction time (e.g., 2–5 AM)\n"
            "- High-risk or unfamiliar location\n"
            "- Amount that seems outside a normal range (e.g., > $500)\n"
            "- Suspicious or unfamiliar merchant / category\n\n"
            "List every anomaly flag with a brief explanation of why it is suspicious."
        ),
        expected_output=(
            "A bullet-point list of anomaly flags (or 'No anomalies detected'). "
            "Each flag states what was observed and why it is suspicious."
        ),
        agent=monitor_agent,
    )

    history_analysis_task = Task(
        description=(
            "Retrieve and analyze the transaction history for the user in this transaction.\n\n"
            f"INCOMING TRANSACTION:\n{transaction_str}\n\n"
            "Steps:\n"
            "1. Extract the user_id from the transaction above.\n"
            "2. Call the `transaction_history_lookup` tool with that user_id.\n"
            "3. Summarize: average and max historical spend, locations seen, "
            "category breakdown, and number of past fraud flags.\n"
            "4. Highlight every dimension where the incoming transaction deviates from the baseline."
        ),
        expected_output=(
            "A structured summary of the user's historical behavior and a list of "
            "deviations the incoming transaction shows versus that baseline."
        ),
        agent=analyst_agent,
    )

    risk_scoring_task = Task(
        description=(
            "Using the anomaly flags and the historical analysis already produced, "
            "calculate an intermediate risk score for this transaction.\n\n"
            f"INCOMING TRANSACTION:\n{transaction_str}\n\n"
            "Steps:\n"
            "1. Call `retrieve_knowledge` with the query "
            "\"fraud risk scoring rules high risk indicators thresholds\" "
            "to pull the official policy guidelines before scoring.\n"
            "2. Review every anomaly flag and historical deviation from prior outputs.\n"
            "3. Apply the retrieved policy rules to assign a preliminary risk score 0–100:\n"
            "   - 0–25  → LOW RISK\n"
            "   - 26–60 → MEDIUM RISK\n"
            "   - 61–85 → HIGH RISK\n"
            "   - 86–100 → CRITICAL RISK\n"
            "4. For each risk factor, cite the specific policy rule that supports it.\n"
            "5. Check retrieved policy for known false positive patterns before finalising.\n"
            "Produce a clear, structured breakdown — the Orchestrator will make the final decision."
        ),
        expected_output=(
            "A structured breakdown containing:\n"
            "  - preliminary_risk_score (int 0-100)\n"
            "  - risk_level (LOW/MEDIUM/HIGH/CRITICAL)\n"
            "  - risk_factors (list of strings, each citing the policy rule that applies)\n"
            "  - policy_chunks_used (brief note on which policy sections informed the score)\n"
            "Plain text or lightweight JSON — no final verdict yet."
        ),
        agent=risk_score_agent,
        context=[anomaly_detection_task, history_analysis_task],
    )

    _feedback_section = (
        f"\n{feedback_context}\n"
        if feedback_context
        else ""
    )

    _memory_section = (
        f"\n{memory_context}\n"
        if memory_context
        else ""
    )

    final_report_task = Task(
        description=(
            "You are the Fraud Detection Orchestrator. Review all findings from your specialist "
            "agents and produce the definitive fraud risk report.\n\n"
            f"INCOMING TRANSACTION:\n{transaction_str}\n"
            f"{_feedback_section}"
            f"{_memory_section}\n"
            "You have received:\n"
            "- Anomaly flags from the Monitor Agent\n"
            "- Historical behavior analysis from the Analyst Agent\n"
            "- Preliminary risk score and factors from the Risk Score Agent (policy-backed)\n\n"
            "Your job:\n"
            "1. Validate and reconcile all findings.\n"
            "2. If prior session decisions are present above (PRIOR DECISIONS IN THIS SESSION), "
            "use them as reference context: if this user or pattern was recently reviewed, "
            "note the consistency or change in risk profile.\n"
            "3. If analyst feedback context is present above, use it to calibrate your verdict: "
            "ease back on patterns previously flagged as over-aggressive; maintain confidence "
            "on patterns previously confirmed correct.\n"
            "4. Confirm or adjust the risk score based on the full picture.\n"
            "5. Issue the final recommendation: APPROVE / REVIEW / BLOCK.\n"
            "6. FEEDBACK ADJUSTMENT (critical): If the analyst feedback context caused you to "
            "change the risk_score, risk_level, or recommendation compared to what the specialist "
            "agents suggested, you MUST set 'rlhf_adjustment' to a single sentence explaining "
            "exactly what changed and why (e.g. 'Risk level lowered from CRITICAL to HIGH because "
            "analyst feedback identified this merchant/location pattern as a past false positive.'). "
            "If feedback was absent or did not change your verdict, set 'rlhf_adjustment' to null.\n"
            "7. ESCALATION (mandatory): If the final risk_score is >= 61 (HIGH or CRITICAL), "
            "you MUST call the `escalate_case` tool BEFORE returning your report. "
            "Pass the transaction_id from the incoming transaction, a concise reason summarising "
            "the top risk factors, and the final risk_score.\n"
            "8. After escalating (if required), return ONLY the structured JSON report below — "
            "no extra text."
        ),
        expected_output=(
            "A JSON object with keys:\n"
            "  - risk_score (int 0-100)\n"
            "  - risk_level (LOW/MEDIUM/HIGH/CRITICAL)\n"
            "  - risk_factors (list of strings explaining what drove the score)\n"
            "  - recommendation (APPROVE / REVIEW / BLOCK)\n"
            "  - summary (one-paragraph explanation)\n"
            "  - escalated (bool — true if escalate_case was called, false otherwise)\n"
            "  - rlhf_adjustment (string describing what changed due to analyst feedback, "
            "or null if feedback was absent or did not alter the verdict)\n"
            "Output ONLY the JSON object, no extra text."
        ),
        agent=fraud_detection_agent,
        context=[anomaly_detection_task, history_analysis_task, risk_scoring_task],
    )

    return anomaly_detection_task, history_analysis_task, risk_scoring_task, final_report_task
