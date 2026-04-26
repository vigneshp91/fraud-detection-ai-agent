

from crewai import Task
from agents import fraud_analyst


risk_scoring_task = Task(
        description=(
            "A new transaction has arrived and requires a fraud risk assessment.\n\n"
            "INCOMING TRANSACTION:\n{transaction}\n\n"
            "Steps:\n"
            "1. Extract the user_id from the incoming transaction.\n"
            "2. Use the `transaction_history_lookup` tool to fetch that user's past transactions.\n"
            "3. Compare the incoming transaction against the history on these dimensions:\n"
            "   - Amount deviation: how does this amount compare to the user's average and max?\n"
            "   - Location anomaly: is this location new or risky compared to past locations?\n"
            "   - Category anomaly: is this category unusual for this user?\n"
            "   - Time pattern: does the transaction time fit normal patterns?\n"
            "   - Historical fraud rate: has this user had flagged transactions before?\n"
            "4. Assign a risk score 0-100 and classify:\n"
            "   - 0-25  → LOW RISK\n"
            "   - 26-60 → MEDIUM RISK\n"
            "   - 61-85 → HIGH RISK\n"
            "   - 86-100 → CRITICAL RISK\n"
            "5. Return a structured JSON report."
        ),
        expected_output=(
            "A JSON object with keys:\n"
            "  - risk_score (int 0-100)\n"
            "  - risk_level (LOW/MEDIUM/HIGH/CRITICAL)\n"
            "  - risk_factors (list of strings explaining what drove the score)\n"
            "  - recommendation (APPROVE / REVIEW / BLOCK)\n"
            "  - summary (one-paragraph explanation)\n"
            "Output ONLY the JSON object, no extra text."
        ),
        agent=fraud_analyst,
    )