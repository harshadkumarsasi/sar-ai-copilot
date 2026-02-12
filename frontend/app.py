"""
Streamlit frontend for SAR AI Copilot.

Responsibilities:
- Accept analyst inputs
- Trigger SAR generation
- Display SAR narrative
- Show reasoning trace
"""


import sys
import os

# Ensure project root is in Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

import streamlit as st
from backend.llm.model import SARLLM, SARInput
from backend.explainability.trace import ExplainabilityEngine
from backend.db.postgres import PostgresClient

# -------------------------------
# App Configuration
# -------------------------------
st.set_page_config(page_title="SAR AI Copilot", layout="wide")
st.title("🔍 SAR AI Copilot")
st.markdown("AI-assisted Suspicious Activity Report drafting tool.")

# -------------------------------
# Initialize Core Components
# -------------------------------
llm = SARLLM()
explain_engine = ExplainabilityEngine()

# Database (safe init)
try:
    db = PostgresClient()
    db.init_tables()
except Exception:
    db = None  # Allow demo mode without DB


# -------------------------------
# Sidebar - Analyst Inputs
# -------------------------------
st.sidebar.header("Analyst Inputs")

customer_id = st.sidebar.text_input("Customer ID", "CUST-001")
customer_name = st.sidebar.text_input("Customer Name", "John Doe")
risk_score = st.sidebar.slider("Risk Score", 0.0, 100.0, 65.0)

alert_reason = st.sidebar.text_area(
    "Alert Reason",
    "Unusual spike in cross-border transactions exceeding typical monthly volume.",
)

transaction_summary = st.sidebar.text_area(
    "Transaction Summary",
    "Multiple high-value transfers to newly added offshore beneficiaries within 7 days.",
)

generate_button = st.sidebar.button("Generate SAR")

# -------------------------------
# Main Panel
# -------------------------------
if generate_button:

    st.subheader("Generated SAR Narrative")

    customer_profile = {
        "customer_id": customer_id,
        "customer_name": customer_name,
        "risk_score": risk_score,
    }

    sar_input = SARInput(
        customer_profile=customer_profile,
        transaction_summary={"summary": transaction_summary},
        alert_reason=alert_reason,
    )

    # Generate SAR narrative
    sar_output = llm.generate_sar(sar_input)

    # Store case in DB (if available)
    case_id = None
    if db:
        case_id = db.create_case(customer_id, risk_score)

    # Capture reasoning trace
    trace = explain_engine.capture_trace(
        case_id=case_id or -1,
        model_name="mistral (ollama)",
        input_signals={
            "customer_profile": customer_profile,
            "transaction_summary": transaction_summary,
            "alert_reason": alert_reason,
        },
        retrieved_context="",
    )

    # Log action if DB available
    if db and case_id:
        db.log_action(
            case_id,
            action="sar_generated",
            details=trace.to_dict(),
        )

    # Display SAR
    st.success("SAR Draft Generated Successfully")
    st.text_area("SAR Draft", sar_output, height=300)

    # Display Explainability
    with st.expander("View Reasoning Trace"):
        st.json(trace.to_dict())

else:
    st.info("Enter analyst inputs in the sidebar and click 'Generate SAR' to begin.")