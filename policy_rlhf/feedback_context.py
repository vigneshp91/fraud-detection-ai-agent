"""
Feedback context builder for the RLHF prompt-injection loop.

Reads recent human ratings from feedback_store.json and produces a concise
text block that is injected into the Orchestrator's final task prompt before
the crew runs. This closes the feedback loop without retraining the model.

Rating semantics (enforced by the simulator UI):
  1–2  →  poor decision (false positive / false negative)
  3    →  neutral
  4–5  →  correct decision confirmed by analyst
"""
from __future__ import annotations

import json
import os


def build_feedback_context(
    store_path: str,
    max_corrections: int = 5,
    max_confirmations: int = 3,
) -> str:
    """Return a prompt-ready context string drawn from recent analyst feedback.

    Returns an empty string when there is no actionable feedback so the prompt
    is unchanged for first-run transactions.
    """
    if not os.path.exists(store_path):
        return ""

    with open(store_path) as f:
        all_feedback: list[dict] = json.load(f)

    # Only entries that include transaction metadata are useful for context
    enriched = [e for e in all_feedback if e.get("transaction_meta")]
    if not enriched:
        return ""

    # Split by analyst verdict
    corrections   = [e for e in enriched if e["rating"] <= 2]
    confirmations = [e for e in enriched if e["rating"] >= 4]

    # Most recent first, capped to keep the prompt concise
    corrections   = corrections[-max_corrections:]
    confirmations = confirmations[-max_confirmations:]

    if not corrections and not confirmations:
        return ""

    lines: list[str] = [
        "━━━ ANALYST FEEDBACK CONTEXT (RLHF) ━━━",
        "The following entries reflect recent human reviews of agent decisions.",
        "Use them to calibrate your verdict — do not override clear evidence, but",
        "apply extra caution or confidence where patterns match.",
        "",
    ]

    # ── Corrections: analyst said the decision was wrong ─────────────────────
    if corrections:
        lines.append("⚠️  POTENTIAL OVER/UNDER-FLAGGING (rating 1–2 from analysts):")
        for e in corrections:
            meta    = e["transaction_meta"]
            comment = f'  Analyst note: "{e["comment"]}"' if e.get("comment") else ""
            lines.append(
                f"  • {meta.get('category','?')} | {meta.get('merchant','?')} | "
                f"{meta.get('location','?')} | ${meta.get('amount','?')}"
            )
            lines.append(
                f"    Agent decided: {meta.get('risk_level','?')} / "
                f"{meta.get('recommendation','?')} (score {meta.get('risk_score','?')}) "
                f"→ rated {e['rating']}/5{comment}"
            )
        lines.append(
            "  → Consider whether the same pattern warrants a less aggressive verdict."
        )
        lines.append("")

    # ── Confirmations: analyst said the decision was correct ─────────────────
    if confirmations:
        lines.append("✅  CONFIRMED CORRECT DECISIONS (rating 4–5 from analysts):")
        for e in confirmations:
            meta    = e["transaction_meta"]
            comment = f'  Analyst note: "{e["comment"]}"' if e.get("comment") else ""
            lines.append(
                f"  • {meta.get('category','?')} | {meta.get('merchant','?')} | "
                f"{meta.get('location','?')} | ${meta.get('amount','?')}"
            )
            lines.append(
                f"    Agent decided: {meta.get('risk_level','?')} / "
                f"{meta.get('recommendation','?')} (score {meta.get('risk_score','?')}) "
                f"→ rated {e['rating']}/5{comment}"
            )
        lines.append(
            "  → These patterns were confirmed correct — maintain similar confidence."
        )
        lines.append("")

    lines.append("━━━ END OF FEEDBACK CONTEXT ━━━")
    return "\n".join(lines)
