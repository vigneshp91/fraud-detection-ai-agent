"""
Fraud Detection AI Agent — Streamlit GUI Simulator

Run:
    streamlit run simulator/app.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Fraud Detection AI Agent",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from data.setup_db import setup_database
from safety.guardrails import Guardrails
from safety.pii_filter import detect as detect_pii
from policy_rlhf.feedback_collector import FeedbackCollector
from policy_rlhf.policy_checker import PolicyChecker
from mcp.fraud_mcp_server import fraud_mcp_client

_ROOT            = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_FEEDBACK_PATH   = os.path.join(_ROOT, "data", "rlhf", "feedback_store.json")
_POLICY_PATH     = os.path.join(_ROOT, "data", "policy", "policy.json")
_TEST_CASES_PATH = os.path.join(_ROOT, "data", "evaluation", "test_cases.json")

setup_database()
_guardrails     = Guardrails()
_feedback_store = FeedbackCollector(_FEEDBACK_PATH)
_policy_checker = PolicyChecker(_POLICY_PATH)

# ── Session state ─────────────────────────────────────────────────────────────
for _key, _default in [
    ("last_report",  None),
    ("last_tx_id",   ""),
    ("last_tx",      {}),
    ("last_safety",  {}),   # guardrail + PII results for the last submission
    ("eval_results", []),
    ("form_preset",  None),
]:
    if _key not in st.session_state:
        st.session_state[_key] = _default

# ── Constants ─────────────────────────────────────────────────────────────────
RISK_COLORS = {
    "LOW":      "#28a745",
    "MEDIUM":   "#fd7e14",
    "HIGH":     "#e05d00",
    "CRITICAL": "#8b0000",
}
REC_COLORS = {
    "APPROVE": "#28a745",
    "REVIEW":  "#fd7e14",
    "BLOCK":   "#dc3545",
}
STAR_MAP   = {1: "⭐", 2: "⭐⭐", 3: "⭐⭐⭐", 4: "⭐⭐⭐⭐", 5: "⭐⭐⭐⭐⭐"}
CATEGORIES = ["groceries", "gas", "restaurant", "electronics", "travel", "atm", "online"]

PRESETS = {
    "🟢 Low Risk": {
        "transaction_id": "txn_low_001",
        "user_id":        "user_001",
        "amount":         45.50,
        "merchant":       "Starbucks",
        "category":       "restaurant",
        "location":       "New York, NY",
        "timestamp":      datetime.now().strftime("%Y-%m-%d 09:15:00"),
    },
    "🟡 Medium Risk": {
        "transaction_id": "txn_med_001",
        "user_id":        "user_002",
        "amount":         380.00,
        "merchant":       "Apple Store",
        "category":       "electronics",
        "location":       "Chicago, IL",
        "timestamp":      datetime.now().strftime("%Y-%m-%d 14:30:00"),
    },
    "🔴 High Risk": {
        "transaction_id": "txn_high_001",
        "user_id":        "user_003",
        "amount":         2200.00,
        "merchant":       "Unknown Merchant",
        "category":       "online",
        "location":       "Lagos, Nigeria",
        "timestamp":      datetime.now().strftime("%Y-%m-%d 03:47:00"),
    },
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _badge(label: str, color: str, size: str = "1.05em") -> str:
    return (
        f'<span style="background:{color};color:white;padding:5px 16px;'
        f'border-radius:8px;font-weight:bold;font-size:{size}">{label}</span>'
    )


def _parse_crew_output(result) -> dict:
    raw = result.raw if hasattr(result, "raw") else str(result)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    return json.loads(raw)


def _run_analysis(tx: dict) -> tuple[dict, float]:
    from agent.core_agent import build_crew
    sanitized = {
        k: _guardrails.mask_pii(_guardrails.sanitize(v)) if isinstance(v, str) else v
        for k, v in tx.items()
    }
    combined = " ".join(str(v) for v in sanitized.values())
    is_safe, reason = _guardrails.check_input(combined)
    if not is_safe:
        raise ValueError(f"Input blocked by guardrails: {reason}")
    t0 = time.perf_counter()
    crew = build_crew(sanitized)
    result = crew.kickoff()
    latency = round(time.perf_counter() - t0, 2)
    return _parse_crew_output(result), latency


def _show_report(report: dict, latency: float | None = None) -> None:
    risk_level = report.get("risk_level", "UNKNOWN")
    rec        = report.get("recommendation", "UNKNOWN")
    score      = report.get("risk_score", 0)
    escalated  = report.get("escalated", False)
    color      = RISK_COLORS.get(risk_level, "#555")
    rec_color  = REC_COLORS.get(rec, "#555")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Risk Score", f"{score} / 100")
    m2.markdown(f"**Risk Level**<br>{_badge(risk_level, color)}", unsafe_allow_html=True)
    m3.markdown(f"**Recommendation**<br>{_badge(rec, rec_color)}", unsafe_allow_html=True)
    if latency is not None:
        m4.metric("Analysis Time", f"{latency}s")

    st.progress(score / 100, text=f"Risk Score: {score}/100")

    rlhf_adjustment = report.get("rlhf_adjustment")
    if rlhf_adjustment:
        st.success(f"🔁 **RLHF adjustment applied:** {rlhf_adjustment}")

    if escalated:
        st.warning("🚨 **Escalated** — case routed to the human fraud review team via MCP `escalate_case`")
    elif score >= 61:
        st.info("ℹ️ Score ≥ 61 but escalation not triggered — check agent output.")

    st.markdown("**Risk Factors**")
    for factor in report.get("risk_factors", []) or ["No risk factors identified."]:
        st.markdown(f"&nbsp;&nbsp;• {factor}")

    st.markdown("**Summary**")
    st.info(report.get("summary", ""))

    with st.expander("Raw JSON"):
        st.json(report)


def _load_test_cases() -> list[dict]:
    if not os.path.exists(_TEST_CASES_PATH):
        return []
    with open(_TEST_CASES_PATH) as f:
        return json.load(f)


def _load_policy() -> dict:
    if not os.path.exists(_POLICY_PATH):
        return {"version": 1, "updated_at": None, "rules": []}
    with open(_POLICY_PATH) as f:
        return json.load(f)


# ── System status ─────────────────────────────────────────────────────────────
_openai_ok   = bool(os.environ.get("OPENAI_API_KEY"))
_db_ok       = os.path.exists(os.path.join(_ROOT, "data", "transactions.db"))
_langfuse_ok = bool(os.environ.get("LANGFUSE_PUBLIC_KEY"))


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.title("🛡️ Fraud Detection")
    st.caption("AI Agent Simulator")
    st.divider()

    st.subheader("System Status")
    st.markdown("✅ OpenAI API" if _openai_ok else "❌ OpenAI API key missing")
    st.markdown("✅ Database ready" if _db_ok else "⚠️ Database missing — run `data/setup_db.py`")
    st.markdown("✅ Langfuse active" if _langfuse_ok else "⚪ Langfuse disabled (optional)")
    st.markdown("✅ MCP Server — in-process")

    st.divider()
    st.subheader("Agent Pipeline")
    st.markdown(
        "1. 👁️ **Monitor** — anomaly flags\n"
        "2. 🔎 **Analyst** — history via MCP\n"
        "3. 📐 **Calculator** — risk score 0–100\n"
        "4. 🧠 **Orchestrator** — final verdict"
    )

    st.divider()
    st.caption("CrewAI → MCP → SQLite")
    st.caption("Transport: InProcessTransport")
    st.caption("Protocol: JSON-RPC 2.0")
    st.caption("v1.0.0")


# ══════════════════════════════════════════════════════════════════════════════
#  TABS
# ══════════════════════════════════════════════════════════════════════════════

tab_sim, tab_eval, tab_history, tab_policy, tab_mcp, tab_escalations = st.tabs([
    "🔍 Simulator",
    "🧪 Evaluation Suite",
    "📊 User History (MCP)",
    "📋 Policy Rules",
    "🔌 MCP Inspector",
    "🚨 Escalations",
])


# ════════════════════════════════════════════════════════════════════════════
#  TAB 1 — TRANSACTION SIMULATOR
# ════════════════════════════════════════════════════════════════════════════

with tab_sim:
    st.header("Transaction Simulator")
    st.caption("Fill in any transaction and watch the 4-agent pipeline analyze it live.")

    if not _openai_ok:
        st.error("⚠️ OPENAI_API_KEY not found — add it to your .env file to run the agent.")

    form_col, result_col = st.columns([1, 1], gap="large")

    # ── LEFT: input form ──────────────────────────────────────────────────────
    with form_col:
        st.subheader("Load Preset")
        p_cols = st.columns(3)
        for i, pname in enumerate(PRESETS):
            if p_cols[i].button(pname, use_container_width=True, key=f"preset_btn_{i}"):
                st.session_state.form_preset = PRESETS[pname]

        preset = st.session_state.form_preset or {}

        st.subheader("Transaction Details")
        with st.form("tx_form"):
            tx_id     = st.text_input("Transaction ID",
                                      value=preset.get("transaction_id", f"txn_{int(time.time())}"))
            user_id   = st.text_input("User ID",
                                      value=preset.get("user_id", "user_001"))
            amount    = st.number_input("Amount ($)",
                                        value=float(preset.get("amount", 100.00)),
                                        min_value=0.01, step=0.01, format="%.2f")
            merchant  = st.text_input("Merchant",
                                      value=preset.get("merchant", ""))
            cat_idx   = CATEGORIES.index(preset["category"]) if preset.get("category") in CATEGORIES else 0
            category  = st.selectbox("Category", CATEGORIES, index=cat_idx)
            location  = st.text_input("Location",
                                      value=preset.get("location", "New York, NY"))
            timestamp = st.text_input("Timestamp (YYYY-MM-DD HH:MM:SS)",
                                      value=preset.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            submitted = st.form_submit_button(
                "🔍 Analyze Transaction",
                use_container_width=True,
                disabled=not _openai_ok,
            )

        if submitted:
            tx = {
                "transaction_id": tx_id,
                "user_id":        user_id,
                "amount":         amount,
                "merchant":       merchant,
                "category":       category,
                "location":       location,
                "timestamp":      timestamp,
            }

            # ── Compute safety / PII before running the crew ────────────────
            raw_combined  = " ".join(str(v) for v in tx.values())
            pii_types     = detect_pii(raw_combined)
            is_safe, why  = _guardrails.check_input(raw_combined)
            masked_input  = _guardrails.mask_pii(_guardrails.sanitize(raw_combined))

            st.session_state.last_safety = {
                "is_safe":     is_safe,
                "reason":      why,
                "pii_types":   pii_types,
                "raw":         raw_combined,
                "masked":      masked_input,
            }

            if not is_safe:
                st.error(f"🚫 Input blocked by guardrails: {why}")
            else:
                with st.spinner("Running 4-agent analysis pipeline — this takes ~30–60s…"):
                    try:
                        report, latency = _run_analysis(tx)
                        st.session_state.last_report = report
                        st.session_state.last_tx_id  = tx_id
                        st.session_state.last_tx      = tx
                        st.session_state.last_latency = latency
                        st.success(f"Analysis complete in {latency}s")
                    except Exception as e:
                        st.error(f"Agent error: {e}")

    # ── RIGHT: results, safety panel, feedback ────────────────────────────────
    with result_col:

        # ── Analysis result ───────────────────────────────────────────────────
        st.subheader("Analysis Result")
        if st.session_state.last_report:
            _show_report(
                st.session_state.last_report,
                st.session_state.get("last_latency"),
            )
        else:
            st.info("Submit a transaction on the left to see the full risk report here.")
            st.markdown(
                "**What happens after you submit:**\n"
                "1. Guardrails check + PII masking\n"
                "2. Monitor Agent flags anomalies\n"
                "3. Analyst Agent fetches history via **MCP**\n"
                "4. Risk Calculator scores 0–100\n"
                "5. Orchestrator issues final verdict"
            )

        # ── RLHF context that was injected into this run ─────────────────────
        if st.session_state.last_report:
            from policy_rlhf.feedback_context import build_feedback_context
            injected_ctx = build_feedback_context(_FEEDBACK_PATH)
            if injected_ctx:
                with st.expander("🔁 RLHF Feedback injected into this analysis"):
                    st.code(injected_ctx, language=None)
            else:
                with st.expander("🔁 RLHF Feedback context"):
                    st.caption(
                        "No enriched feedback yet. Submit a rating below — "
                        "the next analysis will include this as context for the Orchestrator."
                    )

        # ── Input safety report ───────────────────────────────────────────────
        safety = st.session_state.last_safety
        if safety:
            st.divider()
            st.subheader("🛡️ Input Safety Report")

            g_col, p_col = st.columns(2)

            with g_col:
                st.markdown("**Guardrail Check**")
                if safety["is_safe"]:
                    st.success("✅ Safe — no blocked phrases detected")
                else:
                    st.error(f"🚫 BLOCKED: {safety['reason']}")

            with p_col:
                st.markdown("**PII Detection**")
                pii = safety["pii_types"]
                if pii:
                    st.warning(f"⚠️ Found: **{', '.join(pii)}**")
                    for p in pii:
                        st.markdown(f"&nbsp;&nbsp;• `{p}`")
                else:
                    st.success("✅ No PII detected")

            with st.expander("View raw → masked transformation"):
                st.markdown("**Original combined input (before masking):**")
                st.code(safety["raw"], language=None)
                st.markdown("**Sent to agents (after sanitize + PII mask):**")
                st.code(safety["masked"], language=None)

        # ── Feedback & RLHF ───────────────────────────────────────────────────
        if st.session_state.last_report:
            st.divider()
            st.subheader("💬 Rate This Decision")

            with st.form("feedback_form"):
                fb_tx_id   = st.text_input(
                    "Transaction ID",
                    value=st.session_state.last_tx_id,
                    disabled=True,
                )
                fb_rating  = st.slider("Rating (1 = poor decision, 5 = excellent)", 1, 5, 4)
                st.caption(f"{STAR_MAP[fb_rating]}  ({fb_rating}/5)")
                fb_comment = st.text_area(
                    "Comment (optional)",
                    max_chars=500,
                    placeholder="e.g. 'False positive — customer confirmed it was them'",
                )
                fb_submit  = st.form_submit_button("✅ Submit Feedback", use_container_width=True)

            if fb_submit:
                # Build transaction_meta so the feedback loop has enough context
                # to generate meaningful prompt injections for future analyses.
                tx_meta = {
                    **{k: st.session_state.last_tx.get(k)
                       for k in ("category", "merchant", "location", "amount")},
                    "risk_level":     st.session_state.last_report.get("risk_level"),
                    "risk_score":     st.session_state.last_report.get("risk_score"),
                    "recommendation": st.session_state.last_report.get("recommendation"),
                }
                _feedback_store.record(
                    st.session_state.last_tx_id,
                    fb_rating,
                    fb_comment,
                    transaction_meta=tx_meta,
                )
                st.success(f"Feedback saved — **{st.session_state.last_tx_id}** rated {STAR_MAP[fb_rating]}")
                st.caption("This will influence the Orchestrator's verdict on the next analysis.")

            # Feedback history (compact)
            all_feedback = _feedback_store.load_all()
            if all_feedback:
                with st.expander(f"Feedback history ({len(all_feedback)} entries)"):
                    fb_df = pd.DataFrame(all_feedback)
                    fb_df.insert(1, "Stars", fb_df["rating"].map(STAR_MAP))
                    st.dataframe(
                        fb_df[["transaction_id", "Stars", "rating", "comment", "timestamp"]],
                        use_container_width=True,
                        hide_index=True,
                    )
                    avg = round(sum(e["rating"] for e in all_feedback) / len(all_feedback), 2)
                    st.metric("Average Rating", f"{avg} / 5", delta=f"{len(all_feedback)} total")

                    violations = _policy_checker.check_all(all_feedback)
                    if violations:
                        st.warning(f"{len(violations)} policy violation(s) detected in feedback")
                    else:
                        st.success("No policy violations in feedback")


# ════════════════════════════════════════════════════════════════════════════
#  TAB 2 — EVALUATION SUITE
# ════════════════════════════════════════════════════════════════════════════

with tab_eval:
    st.header("🧪 Evaluation Suite")
    st.caption("Run all test cases through the agent and score correctness + latency.")

    if not _openai_ok:
        st.error("⚠️ OPENAI_API_KEY not found — agent cannot run.")

    cases = _load_test_cases()
    if not cases:
        st.warning("No test cases found at `data/evaluation/test_cases.json`")
    else:
        st.info(f"**{len(cases)} test case(s)** loaded — IDs: {', '.join(c['id'] for c in cases)}")

        with st.expander("Preview Test Cases"):
            for c in cases:
                st.markdown(f"**{c['id']}** — {c.get('description', '')}")
                ec1, ec2 = st.columns(2)
                ec1.json(c["input"])
                ec2.json(c.get("expected", {}))
                st.divider()

        if st.button("▶ Run All Test Cases", disabled=not _openai_ok or not cases):
            results      = []
            progress_bar = st.progress(0, text="Starting…")
            status_slot  = st.empty()

            for i, case in enumerate(cases):
                status_slot.info(
                    f"Running **{case['id']}**: {case.get('description', '')} ({i+1}/{len(cases)})"
                )
                try:
                    report, latency = _run_analysis(case["input"])
                    expected = case.get("expected", {})
                    passed   = report.get("risk_level") == expected.get("risk_level")
                    results.append({
                        "ID":             case["id"],
                        "Description":    case.get("description", ""),
                        "Result":         "✅ Pass" if passed else "❌ Fail",
                        "Expected Level": expected.get("risk_level", "—"),
                        "Actual Level":   report.get("risk_level", "—"),
                        "Expected Rec":   expected.get("recommendation", "—"),
                        "Actual Rec":     report.get("recommendation", "—"),
                        "Latency (s)":    latency,
                        "_passed":        passed,
                    })
                except Exception as e:
                    results.append({
                        "ID":             case["id"],
                        "Description":    case.get("description", ""),
                        "Result":         "❌ Error",
                        "Expected Level": case.get("expected", {}).get("risk_level", "—"),
                        "Actual Level":   "ERROR",
                        "Expected Rec":   case.get("expected", {}).get("recommendation", "—"),
                        "Actual Rec":     str(e)[:60],
                        "Latency (s)":    0,
                        "_passed":        False,
                    })
                progress_bar.progress((i + 1) / len(cases), text=f"{i+1}/{len(cases)} complete")

            st.session_state.eval_results = results
            status_slot.success("Evaluation complete!")

    if st.session_state.eval_results:
        results  = st.session_state.eval_results
        passed_n = sum(1 for r in results if r["_passed"])
        total_n  = len(results)
        avg_lat  = round(sum(r["Latency (s)"] for r in results) / total_n, 2) if total_n else 0
        max_lat  = max((r["Latency (s)"] for r in results), default=0)

        st.divider()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Pass Rate",   f"{passed_n}/{total_n}",
                  delta=f"{round(passed_n/total_n*100)}%" if total_n else "—")
        m2.metric("Avg Latency", f"{avg_lat}s")
        m3.metric("Max Latency", f"{max_lat}s")
        m4.metric("Cases Run",   total_n)

        st.dataframe(
            pd.DataFrame([{k: v for k, v in r.items() if not k.startswith("_")} for r in results]),
            use_container_width=True,
            hide_index=True,
        )


# ════════════════════════════════════════════════════════════════════════════
#  TAB 3 — USER HISTORY VIA MCP
# ════════════════════════════════════════════════════════════════════════════

with tab_history:
    st.header("📊 User Transaction History (via MCP)")
    st.caption(
        "The analyst agent calls `transaction_history_lookup` via MCP during every analysis. "
        "Try it directly here and inspect the raw JSON-RPC exchange."
    )

    uid_col, btn_col = st.columns([3, 1])
    with uid_col:
        uid_choice = st.selectbox("User ID", ["user_001", "user_002", "user_003", "Custom…"],
                                  key="hist_uid_select")
        history_uid = (
            st.text_input("Enter User ID", key="hist_uid_custom")
            if uid_choice == "Custom…"
            else uid_choice
        )
    with btn_col:
        st.markdown("<br>", unsafe_allow_html=True)
        fetch_clicked = st.button("📡 Fetch via MCP", use_container_width=True)

    if fetch_clicked and history_uid:
        with st.spinner(f"Calling MCP: transaction_history_lookup(user_id='{history_uid}')…"):
            try:
                raw = fraud_mcp_client.call_tool("transaction_history_lookup", user_id=history_uid)
                st.session_state[f"hist_{history_uid}"] = json.loads(raw)
            except Exception as e:
                st.error(f"MCP call failed: {e}")

    cache_key = f"hist_{history_uid}"
    if cache_key in st.session_state:
        data = st.session_state[cache_key]

        if "error" in data:
            st.error(data["error"])
        else:
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Total Transactions", data["total_transactions"])
            m2.metric("Avg Amount", f"${data['avg_amount']}")
            m3.metric("Max Amount", f"${data['max_amount']}")
            m4.metric("Min Amount", f"${data['min_amount']}")
            m5.metric(
                "Fraud Rate",
                f"{data['fraud_rate_pct']}%",
                delta=f"{data['fraud_count_in_last30']} flagged in last 30",
                delta_color="inverse",
            )

            col_cat, col_loc = st.columns([2, 1])
            with col_cat:
                st.subheader("Category Breakdown")
                cat_df = pd.DataFrame(
                    sorted(data["category_breakdown"].items(), key=lambda x: -x[1]),
                    columns=["Category", "Count"],
                )
                st.bar_chart(cat_df.set_index("Category"))
            with col_loc:
                st.subheader("Unique Locations")
                for loc in sorted(data["unique_locations"]):
                    st.markdown(f"• {loc}")

            st.subheader("Recent Transactions (last 10)")
            if data.get("recent_transactions"):
                st.dataframe(
                    pd.DataFrame(data["recent_transactions"]),
                    use_container_width=True,
                    hide_index=True,
                )

            with st.expander("📦 Raw JSON-RPC 2.0 Exchange"):
                rc, rp = st.columns(2)
                rc.markdown("**Request →**")
                rc.json({
                    "jsonrpc": "2.0", "id": "1", "method": "tools/call",
                    "params":  {"name": "transaction_history_lookup",
                                "arguments": {"user_id": history_uid}},
                })
                rp.markdown("**← Response**")
                rp.json({
                    "jsonrpc": "2.0", "id": "1",
                    "result":  {"content": [{"type": "text", "text": "(see parsed data above)"}]},
                })


# ════════════════════════════════════════════════════════════════════════════
#  TAB 4 — POLICY RULES
# ════════════════════════════════════════════════════════════════════════════

with tab_policy:
    st.header("📋 Policy Rules")
    st.caption("Active policy rules governing when the agent recommends APPROVE, REVIEW, or BLOCK.")

    policy = _load_policy()
    p1, p2 = st.columns(2)
    p1.markdown(f"**Policy Version:** `{policy.get('version', 1)}`")
    p2.markdown(f"**Last Updated:** `{policy.get('updated_at', 'Never')}`")
    st.divider()

    rules = policy.get("rules", [])
    if rules:
        st.dataframe(
            pd.DataFrame(rules)[["id", "description", "condition", "action", "violation_count"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "id":              st.column_config.TextColumn("Rule ID"),
                "description":     st.column_config.TextColumn("Description"),
                "condition":       st.column_config.TextColumn("Condition"),
                "action":          st.column_config.TextColumn("Action"),
                "violation_count": st.column_config.NumberColumn("Violations", format="%d"),
            },
        )

        st.subheader("Rule Details")
        for rule in rules:
            action_color = REC_COLORS.get(rule["action"], "#555")
            with st.expander(f"{rule['id']} — {rule['description']}"):
                c1, c2, c3 = st.columns(3)
                c1.markdown(f"**Condition**\n\n`{rule['condition']}`")
                c2.markdown(f"**Action**\n\n{_badge(rule['action'], action_color)}",
                            unsafe_allow_html=True)
                c3.metric("Violations", rule.get("violation_count", 0))
    else:
        st.info("No policy rules defined.")

    with st.expander("Raw policy.json"):
        st.json(policy)


# ════════════════════════════════════════════════════════════════════════════
#  TAB 5 — MCP INSPECTOR
# ════════════════════════════════════════════════════════════════════════════

with tab_mcp:
    st.header("🔌 MCP Inspector")
    st.caption(
        "Inspect the in-process MCP server, browse tool schemas, "
        "and fire raw JSON-RPC 2.0 calls."
    )

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Transport", "InProcessTransport")
    s2.metric("Protocol",  "JSON-RPC 2.0")
    s3.metric("Status",    "Online ✅")
    try:
        _tools_list = fraud_mcp_client.list_tools()
        s4.metric("Tools Registered", len(_tools_list))
    except Exception:
        _tools_list = []
        s4.metric("Tools Registered", "Error")

    st.subheader("Registered Tools")
    for tool in _tools_list:
        with st.expander(f"🔧 {tool['name']}"):
            st.markdown(f"**Description:** {tool['description']}")
            st.markdown("**Input Schema (JSON Schema):**")
            st.json(tool["inputSchema"])

    st.divider()
    st.subheader("Interactive Tool Call")
    tool_names    = [t["name"] for t in _tools_list]
    selected_tool = st.selectbox("Tool", tool_names, key="mcp_tool_select")

    if selected_tool == "transaction_history_lookup":
        mcp_uid   = st.text_input("user_id", value="user_001", key="mcp_call_uid")
        call_args = {"user_id": mcp_uid}
    elif selected_tool == "escalate_case":
        ca1, ca2, ca3 = st.columns(3)
        call_args = {
            "transaction_id": ca1.text_input("transaction_id",
                                             value=st.session_state.last_tx_id or "txn_001"),
            "reason":         ca2.text_input("reason",
                                             value="High risk score from automated analysis"),
            "risk_score":     ca3.number_input("risk_score", min_value=0, max_value=100, value=85),
        }
    else:
        call_args = {}

    _req_id = "demo-42"
    jsonrpc_request = {
        "jsonrpc": "2.0",
        "id":      _req_id,
        "method":  "tools/call",
        "params":  {"name": selected_tool, "arguments": call_args},
    }
    st.markdown("**Request preview (JSON-RPC 2.0):**")
    st.json(jsonrpc_request)

    if st.button("📡 Send to MCP Server"):
        req_col, resp_col = st.columns(2)
        req_col.markdown("**Sent →**")
        req_col.json(jsonrpc_request)
        resp_col.markdown("**← Received**")
        with st.spinner("Calling…"):
            try:
                raw_result = fraud_mcp_client.call_tool(selected_tool, **call_args)
                resp_col.json({
                    "jsonrpc": "2.0", "id": _req_id,
                    "result": {"content": [{"type": "text", "text": raw_result}]},
                })
                st.markdown("**Parsed result:**")
                try:
                    st.json(json.loads(raw_result))
                except json.JSONDecodeError:
                    st.write(raw_result)
            except Exception as e:
                resp_col.json({
                    "jsonrpc": "2.0", "id": _req_id,
                    "error": {"code": -32000, "message": str(e)},
                })

    st.divider()
    st.subheader("Call Chain Architecture")
    st.code(
        "CrewAI analyst_agent\n"
        "  └─ MCPTransactionHistoryTool._run(user_id)\n"
        "       └─ MCPClient.call_tool('transaction_history_lookup', user_id=...)\n"
        "            └─ JSON-RPC 2.0 Request  →  InProcessTransport\n"
        "                 └─ MCPServer.handle(request)\n"
        "                      └─ _transaction_history_lookup(user_id)\n"
        "                           └─ sqlite3  →  data/transactions.db\n"
        "\n"
        "To go multi-process: swap InProcessTransport → StdioTransport or SSETransport.\n"
        "No changes needed in the agent or server code.",
        language=None,
    )


# ════════════════════════════════════════════════════════════════════════════
#  TAB 6 — ESCALATIONS LOG
# ════════════════════════════════════════════════════════════════════════════

_ESCALATIONS_LOG = os.path.join(_ROOT, "logs", "escalations.log")


def _load_escalations() -> list[dict]:
    if not os.path.exists(_ESCALATIONS_LOG):
        return []
    entries = []
    with open(_ESCALATIONS_LOG) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries


with tab_escalations:
    st.header("🚨 Escalation Log")
    st.caption(
        "Every transaction with `risk_score ≥ 61` triggers the `escalate_case` MCP tool. "
        "Each call is appended to `logs/escalations.log` as a JSON line."
    )

    col_refresh, col_path = st.columns([1, 3])
    with col_refresh:
        refresh = st.button("🔄 Refresh", use_container_width=True)
    with col_path:
        st.code(_ESCALATIONS_LOG, language=None)

    escalations = _load_escalations()

    if not escalations:
        st.info(
            "No escalations recorded yet. "
            "Run a HIGH or CRITICAL risk transaction in the Simulator tab to generate one."
        )
    else:
        # ── Summary metrics ────────────────────────────────────────────────
        scores    = [e.get("risk_score", 0) for e in escalations]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0
        max_score = max(scores, default=0)

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Escalations", len(escalations))
        m2.metric("Avg Risk Score",     avg_score)
        m3.metric("Max Risk Score",     max_score)

        st.divider()

        # ── Table ──────────────────────────────────────────────────────────
        df = pd.DataFrame(escalations)

        # Colour-code risk score column
        def _score_color(val: int) -> str:
            if val >= 86:
                return "background-color:#8b0000;color:white"
            if val >= 61:
                return "background-color:#e05d00;color:white"
            return ""

        display_cols = [c for c in
                        ["timestamp", "transaction_id", "risk_score", "reason", "status"]
                        if c in df.columns]

        styled = (
            df[display_cols]
            .sort_values("timestamp", ascending=False)
            .style.map(_score_color, subset=["risk_score"])
        )
        st.dataframe(styled, use_container_width=True, hide_index=True)

        # ── Per-entry detail expanders ─────────────────────────────────────
        st.subheader("Entry Details")
        for entry in reversed(escalations):
            score  = entry.get("risk_score", 0)
            color  = "#8b0000" if score >= 86 else "#e05d00"
            label  = f"{_badge(str(score), color)} &nbsp; {entry.get('transaction_id', '—')} &nbsp; {entry.get('timestamp', '')}"
            with st.expander(entry.get("transaction_id", "—") + f"  |  score {score}  |  {entry.get('timestamp', '')}"):
                st.markdown(f"**Risk Score:** {_badge(str(score), color)}", unsafe_allow_html=True)
                st.markdown(f"**Status:** `{entry.get('status', '—')}`")
                st.markdown(f"**Reason:** {entry.get('reason', '—')}")
                st.markdown(f"**Timestamp:** `{entry.get('timestamp', '—')}`")
                st.json(entry)

        # ── Raw log ────────────────────────────────────────────────────────
        with st.expander("📄 Raw log file"):
            with open(_ESCALATIONS_LOG) as f:
                st.code(f.read(), language="json")
