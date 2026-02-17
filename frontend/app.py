"""
Streamlit frontend for SAR AI Copilot.
Now includes:
- Case dashboard
- Case detail view
- SAR generation inside case
- Basic workflow states
"""

import sys
import os
import streamlit as st
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

# Ensure project root is in Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from backend.llm.model import SARLLM, SARInput
from backend.explainability.trace import ExplainabilityEngine

# -------------------------------
# App Configuration
# -------------------------------
st.set_page_config(page_title="SAR AI Copilot", layout="wide")

# -------------------------------
# Theme State
# -------------------------------
if "theme" not in st.session_state:
    st.session_state.theme = "light"

def apply_theme():
    if st.session_state.theme == "light":
        primary = "#00AEEF"
        background = "#F5F7FA"
        text = "#1A1A1A"
        card = "#FFFFFF"
    else:
        primary = "#00AEEF"
        background = "#0F172A"
        text = "#E5E7EB"
        card = "#1E293B"

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {background};
            color: {text};
        }}

        /* Remove top black spacing */
        header {{visibility: hidden;}}
        .block-container {{
            padding-top: 1.5rem;
        }}

        /* Sidebar styling */
        section[data-testid="stSidebar"] {{
            background-color: {card};
        }}

        .sidebar-title {{
            font-size: 22px;
            font-weight: 700;
            margin-bottom: 4px;
        }}

        .sidebar-sub {{
            font-size: 13px;
            color: #64748B;
            margin-bottom: 16px;
        }}

        .kpi-card {{
            background-color: {card};
            padding: 18px;
            border-radius: 10px;
            border: 1px solid #E2E8F0;
        }}

        .kpi-title {{
            font-size: 13px;
            color: #64748B;
        }}

        .kpi-value {{
            font-size: 26px;
            font-weight: 600;
        }}

        .case-table-header {{
            font-size: 13px;
            font-weight: 600;
            color: #64748B;
            padding: 10px 0;
            border-bottom: 1px solid #E2E8F0;
            margin-top: 25px;
        }}

        .case-row {{
            padding: 18px 0;
            border-bottom: 1px solid #E2E8F0;
        }}

        .case-id-badge {{
            background-color: #0F172A;
            color: #22C55E;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 12px;
            display: inline-block;
        }}

        .risk-badge {{
            background-color: #0F172A;
            color: #22C55E;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 12px;
            display: inline-block;
        }}

        .open-btn-container {{
            display: flex;
            justify-content: flex-end;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

apply_theme()

# -------------------------------
# Sidebar Navigation
# -------------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-title">SAR AI Copilot</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-sub">Compliance Platform</div>', unsafe_allow_html=True)

    st.markdown("---")

    selected_tab = st.radio(
        "Navigation",
        ["Dashboard", "Governance"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    st.markdown("**Theme**")
    theme_choice = st.radio(
        "",
        ["Light Mode", "Dark Mode"],
        index=0 if st.session_state.theme == "light" else 1,
        horizontal=True,
        label_visibility="collapsed"
    )

    new_theme = "light" if theme_choice == "Light Mode" else "dark"
    if new_theme != st.session_state.theme:
        st.session_state.theme = new_theme
        st.rerun()

    st.markdown("---")

    st.markdown("**Demo Analyst**")
    st.caption("analyst@bank.com")
    st.caption("ANALYST")

    st.markdown("---")
    st.button("Sign Out")

llm = SARLLM()
explain_engine = ExplainabilityEngine()

# -------------------------------
# Mock Case Data (Hackathon Demo)
# -------------------------------
if "cases" not in st.session_state:
    st.session_state.cases = [
        {
            "case_id": 1,
            "customer_id": "CUST-001",
            "customer_name": "John Doe",
            "risk_score": 86.5,
            "status": "NEW",
            "alert_reason": "Unusual spike in cross-border transfers.",
            "transaction_summary": "Multiple high-value transfers to offshore accounts within 7 days."
        },
        {
            "case_id": 2,
            "customer_id": "CUST-002",
            "customer_name": "Priya Sharma",
            "risk_score": 72.3,
            "status": "UNDER_REVIEW",
            "alert_reason": "Structuring detected below reporting threshold.",
            "transaction_summary": "Frequent cash deposits slightly below compliance threshold."
        }
    ]

if "selected_case" not in st.session_state:
    st.session_state.selected_case = None

# -------------------------------
# Dashboard View
# -------------------------------
if st.session_state.selected_case is None:

    if selected_tab != "Dashboard":
        st.title("Governance & Administration")
        st.info("Governance module coming soon.")
        st.stop()

    st.title("Case Intake Dashboard")
    st.caption("Alert queue and case assignment")

    # -------------------------------
    # Filters
    # -------------------------------
    col1, col2, col3, col4, col5 = st.columns([2,1,1,1,0.6])

    search_query = col1.text_input("Search cases", placeholder="Search by customer or case ID")
    risk_filter = col2.selectbox("Risk Level", ["All", "High", "Medium", "Low"])
    status_filter = col3.selectbox("Status", ["All", "NEW", "UNDER_REVIEW", "SAR_DRAFTED"])
    geography_filter = col4.selectbox("Geography", ["All", "APAC", "EMEA", "US"])

    with col5:
        clear_filters = st.button("Clear")

    if clear_filters:
        st.rerun()

    st.markdown("")

    # -------------------------------
    # KPI Cards
    # -------------------------------
    total_cases = len(st.session_state.cases)
    high_risk = len([c for c in st.session_state.cases if c["risk_score"] >= 80])
    open_cases = len([c for c in st.session_state.cases if c["status"] in ["NEW", "UNDER_REVIEW"]])
    overdue = 0  # demo placeholder

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Total Cases</div><div class="kpi-value">{total_cases}</div></div>', unsafe_allow_html=True)

    with k2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">High Risk</div><div class="kpi-value">{high_risk}</div></div>', unsafe_allow_html=True)

    with k3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Open Cases</div><div class="kpi-value">{open_cases}</div></div>', unsafe_allow_html=True)

    with k4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Overdue</div><div class="kpi-value">{overdue}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="case-table-header"></div>', unsafe_allow_html=True)

    h1, h2, h3, h4, h5, h6, h7 = st.columns([0.5,2,1,1,1,1,1])

    h1.markdown('<div style="text-align:center; font-weight:600;">#</div>', unsafe_allow_html=True)
    h2.markdown('<div style="text-align:center; font-weight:600;">Customer</div>', unsafe_allow_html=True)
    h3.markdown('<div style="text-align:center; font-weight:600;">Risk Score</div>', unsafe_allow_html=True)
    h4.markdown('<div style="text-align:center; font-weight:600;">Status</div>', unsafe_allow_html=True)
    h5.markdown('<div style="text-align:center; font-weight:600;">Type</div>', unsafe_allow_html=True)
    h6.markdown('<div style="text-align:center; font-weight:600;">Region</div>', unsafe_allow_html=True)
    h7.markdown('<div style="text-align:center; font-weight:600;">Action</div>', unsafe_allow_html=True)

    for case in st.session_state.cases:
        c1, c2, c3, c4, c5, c6, c7 = st.columns([0.5,2,1,1,1,1,1])

        c1.markdown(
            f'<div style="display:flex; justify-content:center; align-items:center;">'
            f'<span class="case-id-badge">{case["case_id"]}</span></div>',
            unsafe_allow_html=True
        )

        c2.markdown(
            f'<div style="display:flex; justify-content:center; align-items:center; font-weight:500;">'
            f'{case["customer_name"]}</div>',
            unsafe_allow_html=True
        )

        c3.markdown(
            f'<div style="display:flex; justify-content:center; align-items:center;">'
            f'<span class="risk-badge">{case["risk_score"]}</span></div>',
            unsafe_allow_html=True
        )

        c4.markdown(
            f'<div style="display:flex; justify-content:center; align-items:center;">'
            f'{case["status"]}</div>',
            unsafe_allow_html=True
        )

        c5.markdown(
            '<div style="display:flex; justify-content:center; align-items:center;">AML</div>',
            unsafe_allow_html=True
        )

        c6.markdown(
            '<div style="display:flex; justify-content:center; align-items:center;">APAC</div>',
            unsafe_allow_html=True
        )

        with c7:
            st.markdown('<div style="display:flex; justify-content:center; align-items:center;">', unsafe_allow_html=True)
            if st.button("Open", key=f"open_{case['case_id']}"):
                st.session_state.selected_case = case
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------
# Case Detail View
# -------------------------------
else:
    case = st.session_state.selected_case

    st.subheader(f"📄 Case #{case['case_id']} - {case['customer_name']}")

    st.markdown(f"**Customer ID:** {case['customer_id']}")
    st.markdown(f"**Risk Score:** {case['risk_score']}")
    st.markdown(f"**Current Status:** {case['status']}")

    st.markdown("---")
    st.markdown("### 🚨 Risk Breakdown")

    risk_signals = []

    # Rule-based risk indicators for demo realism
    if case["risk_score"] >= 80:
        risk_signals.append("🔴 High Overall Risk Score")
    elif case["risk_score"] >= 70:
        risk_signals.append("🟠 Elevated Risk Score")

    if "offshore" in case["transaction_summary"].lower() or "cross-border" in case["alert_reason"].lower():
        risk_signals.append("🔴 Cross-Border / Offshore Activity Detected")

    if "spike" in case["alert_reason"].lower() or "multiple" in case["transaction_summary"].lower():
        risk_signals.append("🟠 Sudden Transaction Volume Increase")

    if "new" in case["transaction_summary"].lower() or "beneficiary" in case["transaction_summary"].lower():
        risk_signals.append("🟡 Newly Added Beneficiary Activity")

    if not risk_signals:
        risk_signals.append("🟢 No major rule-based red flags detected")

    for signal in risk_signals:
        st.write(signal)

    st.markdown("---")

    st.markdown("### 🔎 Alert Details")
    st.write("**Alert Reason:**", case["alert_reason"])
    st.write("**Transaction Summary:**", case["transaction_summary"])

    st.markdown("---")

    # Generate SAR
    if st.button("Generate SAR"):
        customer_profile = {
            "customer_id": case["customer_id"],
            "customer_name": case["customer_name"],
            "risk_score": case["risk_score"],
        }

        sar_input = SARInput(
            customer_profile=customer_profile,
            transaction_summary={"summary": case["transaction_summary"]},
            alert_reason=case["alert_reason"],
        )

        sar_output = llm.generate_sar(sar_input)

        trace = explain_engine.capture_trace(
            case_id=case["case_id"],
            model_name="mistral (ollama)",
            input_signals={
                "customer_profile": customer_profile,
                "transaction_summary": case["transaction_summary"],
                "alert_reason": case["alert_reason"],
            },
            retrieved_context="",
        )

        case["status"] = "SAR_DRAFTED"

        # Store SAR in session for PDF export
        st.session_state.generated_sar = sar_output
        st.session_state.generated_trace = trace

        st.success("SAR Draft Generated Successfully")

    # Display SAR if already generated
    if "generated_sar" in st.session_state:
        st.text_area("SAR Draft", st.session_state.generated_sar, height=400)

        with st.expander("View Reasoning Trace"):
            st.json(st.session_state.generated_trace.to_dict())

        # PDF Export
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("Suspicious Activity Report (SAR)", styles["Title"]))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph(f"Case ID: {case['case_id']}", styles["Normal"]))
        elements.append(Paragraph(f"Customer: {case['customer_name']}", styles["Normal"]))
        elements.append(Paragraph(f"Risk Score: {case['risk_score']}", styles["Normal"]))
        elements.append(Spacer(1, 12))

        for line in st.session_state.generated_sar.split("\n"):
            elements.append(Paragraph(line, styles["Normal"]))
            elements.append(Spacer(1, 6))

        doc.build(elements)
        buffer.seek(0)

        st.download_button(
            label="📄 Download SAR as PDF",
            data=buffer,
            file_name=f"SAR_Case_{case['case_id']}.pdf",
            mime="application/pdf"
        )

    st.markdown("---")

    if st.button("⬅ Back to Dashboard"):
        st.session_state.selected_case = None
        st.rerun()