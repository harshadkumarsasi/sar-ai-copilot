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
        "Navigation Menu",
        ["Dashboard", "Governance"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    st.markdown("**Theme**")
    theme_choice = st.radio(
        "Theme Selection",
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

        st.markdown("""
        <style>
        .gov-header {
            padding: 20px 0 10px 0;
        }
        .gov-title {
            font-size: 28px;
            font-weight: 700;
        }
        .gov-sub {
            font-size: 14px;
            color: #94A3B8;
            margin-top: 6px;
        }
        .gov-card {
            padding: 18px;
            border-radius: 12px;
            border: 1px solid #334155;
            background-color: rgba(30,41,59,0.4);
        }
        .gov-metric {
            font-size: 26px;
            font-weight: 700;
            margin-top: 8px;
        }
        .gov-label {
            font-size: 13px;
            color: #94A3B8;
        }
        .role-badge {
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 600;
        }
        .role-analyst { background:#1E40AF; color:white; }
        .role-manager { background:#6D28D9; color:white; }
        .role-admin { background:#B91C1C; color:white; }
        .timeline-item {
            padding: 10px 0;
            border-bottom: 1px solid #334155;
            font-size: 14px;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown('<div class="gov-header">', unsafe_allow_html=True)
        st.markdown('<div class="gov-title">Governance & Administration</div>', unsafe_allow_html=True)
        st.markdown('<div class="gov-sub">Role-based access control, audit monitoring, and model oversight.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # KPI CARDS
        g1, g2, g3, g4 = st.columns(4)

        with g1:
            st.markdown('<div class="gov-card">👥<div class="gov-metric">12</div><div class="gov-label">Total Users</div></div>', unsafe_allow_html=True)

        with g2:
            st.markdown('<div class="gov-card">🧑‍💻<div class="gov-metric">6</div><div class="gov-label">Analysts</div></div>', unsafe_allow_html=True)

        with g3:
            st.markdown('<div class="gov-card">🛡<div class="gov-metric">3</div><div class="gov-label">Managers</div></div>', unsafe_allow_html=True)

        with g4:
            st.markdown('<div class="gov-card">🔐<div class="gov-metric">3</div><div class="gov-label">Admins</div></div>', unsafe_allow_html=True)

        st.markdown("")

        # USER TABLE
        st.markdown('<div class="gov-card">', unsafe_allow_html=True)
        st.markdown("**User Directory**")

        th1, th2, th3, th4 = st.columns([1.5,2,2,1.5])
        th1.markdown("**User ID**")
        th2.markdown("**Full Name**")
        th3.markdown("**Email**")
        th4.markdown("**Role**")

        users = [
            ("U-001", "John Doe", "john@bank.com", "Analyst"),
            ("U-002", "Priya Sharma", "priya@bank.com", "Manager"),
            ("U-003", "Alex Tan", "alex@bank.com", "Admin"),
        ]

        for uid, name, email, role in users:
            c1, c2, c3, c4 = st.columns([1.5,2,2,1.5])
            c1.markdown(uid)
            c2.markdown(name)
            c3.markdown(email)

            if role == "Analyst":
                c4.markdown('<span class="role-badge role-analyst">Analyst</span>', unsafe_allow_html=True)
            elif role == "Manager":
                c4.markdown('<span class="role-badge role-manager">Manager</span>', unsafe_allow_html=True)
            else:
                c4.markdown('<span class="role-badge role-admin">Admin</span>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("")

        # SYSTEM STATUS
        s1, s2 = st.columns(2)

        with s1:
            st.markdown('<div class="gov-card">', unsafe_allow_html=True)
            st.markdown("**System Health**")
            st.markdown("""
            🟢 AML Engine: Operational  
            🟢 Database: Connected  
            🟢 Audit Logging: Enabled  
            🟢 LLM Model: mistral-v0.3
            """)
            st.markdown('</div>', unsafe_allow_html=True)

        with s2:
            st.markdown('<div class="gov-card">', unsafe_allow_html=True)
            st.markdown("**Recent Activity Logs**")
            st.markdown("""
            <div class="timeline-item">🕒 19:42 — SAR generated for Case #1</div>
            <div class="timeline-item">🕒 19:38 — Analyst login detected</div>
            <div class="timeline-item">🕒 19:30 — Governance settings updated</div>
            <div class="timeline-item">🕒 19:12 — Risk model version updated</div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.stop()

    st.markdown("## Case Intake Dashboard")
    st.caption("Operational AML monitoring and case workflow management")

    # ===============================
    # TOP METRICS ROW
    # ===============================
    total_cases = len(st.session_state.cases)
    high_risk = len([c for c in st.session_state.cases if c["risk_score"] >= 80])
    medium_risk = len([c for c in st.session_state.cases if 70 <= c["risk_score"] < 80])
    low_risk = len([c for c in st.session_state.cases if c["risk_score"] < 70])

    m1, m2, m3, m4 = st.columns(4)

    m1.metric("Total Active Cases", total_cases)
    m2.metric("High Risk Cases", high_risk)
    m3.metric("Medium Risk Cases", medium_risk)
    m4.metric("Low Risk Cases", low_risk)

    st.markdown("---")

    # ===============================
    # WORKFLOW PIPELINE
    # ===============================
    st.markdown("### Case Workflow Pipeline")

    new_cases = len([c for c in st.session_state.cases if c["status"] == "NEW"])
    under_review = len([c for c in st.session_state.cases if c["status"] == "UNDER_REVIEW"])
    drafted = len([c for c in st.session_state.cases if c["status"] == "SAR_DRAFTED"])

    p1, p2, p3 = st.columns(3)
    p1.metric("NEW", new_cases)
    p2.metric("UNDER REVIEW", under_review)
    p3.metric("SAR DRAFTED", drafted)

    st.markdown("---")

    # ===============================
    # FILTERS
    # ===============================
    f1, f2, f3, f4 = st.columns(4)

    search_query = f1.text_input("Search", placeholder="Customer name or Case ID")
    risk_filter = f2.selectbox("Risk Level", ["All", "High", "Medium", "Low"])
    status_filter = f3.selectbox("Status", ["All", "NEW", "UNDER_REVIEW", "SAR_DRAFTED"])
    geography_filter = f4.selectbox("Region", ["All", "APAC", "EMEA", "US"])

    st.markdown("---")

    # ===============================
    # CASE TABLE HEADER
    # ===============================
    h1, h2, h3, h4, h5, h6, h7, h8 = st.columns([0.6,2,1.2,1.2,1,1,1.2,1])

    h1.markdown("**#**")
    h2.markdown("**Customer**")
    h3.markdown("**Risk Score**")
    h4.markdown("**Risk Tier**")
    h5.markdown("**Status**")
    h6.markdown("**Type**")
    h7.markdown("**SLA (hrs)**")
    h8.markdown("**Action**")

    st.markdown("---")

    # ===============================
    # CASE ROWS
    # ===============================
    for case in st.session_state.cases:

        if risk_filter == "High" and case["risk_score"] < 80:
            continue
        if risk_filter == "Medium" and not (70 <= case["risk_score"] < 80):
            continue
        if risk_filter == "Low" and case["risk_score"] >= 70:
            continue
        if status_filter != "All" and case["status"] != status_filter:
            continue
        if search_query and search_query.lower() not in case["customer_name"].lower():
            continue

        if case["risk_score"] >= 80:
            risk_tier = "High"
            risk_color = "🔴"
        elif case["risk_score"] >= 70:
            risk_tier = "Medium"
            risk_color = "🟠"
        else:
            risk_tier = "Low"
            risk_color = "🟢"

        sla_hours = 4 - case["case_id"]  # demo SLA logic

        c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([0.6,2,1.2,1.2,1,1,1.2,1])

        c1.write(case["case_id"])
        c2.write(case["customer_name"])
        c3.write(case["risk_score"])
        c4.write(f"{risk_color} {risk_tier}")
        c5.write(case["status"])
        c6.write("AML")
        c7.write(f"{sla_hours}h")

        with c8:
            if st.button("Open", key=f"open_case_{case['case_id']}"):
                st.session_state.selected_case = case
                st.rerun()

else:
    case = st.session_state.selected_case

    st.markdown("""
    <style>
    .bb-header {
        padding: 20px 0;
        border-bottom: 1px solid #334155;
        margin-bottom: 20px;
    }
    .bb-title {
        font-size: 28px;
        font-weight: 800;
        letter-spacing: 0.5px;
    }
    .bb-meta {
        font-size: 13px;
        color: #94A3B8;
        margin-top: 6px;
    }
    .bb-badge-high {
        background:#7F1D1D;
        color:#FCA5A5;
        padding:4px 10px;
        border-radius:6px;
        font-size:12px;
        font-weight:600;
    }
    .bb-card {
        background:#111827;
        border:1px solid #1F2937;
        border-radius:10px;
        padding:18px;
        margin-bottom:18px;
    }
    .bb-card:empty {
        display: none !important;
    }
    .bb-section-title {
        font-size:14px;
        font-weight:700;
        letter-spacing:0.5px;
        color:#9CA3AF;
        margin-bottom:12px;
        text-transform:uppercase;
    }
    .bb-metric {
        font-size:22px;
        font-weight:700;
    }
    .bb-small {
        font-size:12px;
        color:#6B7280;
    }
    .bb-risk-gauge {
        width:120px;
        height:120px;
        border-radius:50%;
        background:conic-gradient(#DC2626 calc(var(--risk)*1%), #1F2937 0%);
        display:flex;
        align-items:center;
        justify-content:center;
        font-size:26px;
        font-weight:700;
        color:white;
        margin:auto;
    }
    .bb-divider {
        border-top:1px solid #1F2937;
        margin:20px 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # ===============================
    # HEADER
    # ===============================
    st.markdown("""
    <div style="font-size:36px; font-weight:900; letter-spacing:1.5px; text-transform:uppercase; color:#F1F5F9; margin-bottom:18px;">
    Case Details Overview
    </div>
    """, unsafe_allow_html=True)

    header_left, header_right = st.columns([4,1])

    with header_left:
        st.markdown('<div class="bb-header">', unsafe_allow_html=True)
        st.markdown(
            f'<div class="bb-title">CASE #{case["case_id"]} — {case["customer_name"]} '
            f'<span class="bb-badge-high">HIGH RISK</span></div>'
            f'<div class="bb-small" style="margin-top:4px;">'
            f'Case Severity: Critical | Escalation Tier: 3 | Monitoring Priority: Immediate'
            f'</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            f'<div class="bb-meta">Customer ID: {case["customer_id"]} | '
            f'Risk Score: {case["risk_score"]} | '
            f'Status: {case["status"]} | Region: APAC | Tier: 3</div>',
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with header_right:
        st.markdown("<div style='height:60px;'></div>", unsafe_allow_html=True)
        if st.button("Back to Dashboard", use_container_width=True):
            st.session_state.selected_case = None
            st.rerun()

    left, right = st.columns([2,1])

    # ===============================
    # LEFT COLUMN – DATA HEAVY
    # ===============================
    with left:

        # -----------------------------
        # TRANSACTION INTELLIGENCE
        # -----------------------------
        st.markdown('<div class="bb-card">', unsafe_allow_html=True)
        st.markdown('<div class="bb-section-title">Transaction Intelligence</div>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.markdown('<div class="bb-metric">17</div><div class="bb-small">Flagged Transactions</div>', unsafe_allow_html=True)
        c2.markdown('<div class="bb-metric">$482K</div><div class="bb-small">Total Exposure</div>', unsafe_allow_html=True)
        c3.markdown('<div class="bb-metric">+240%</div><div class="bb-small">Peer Deviation</div>', unsafe_allow_html=True)

        st.markdown('<div class="bb-divider"></div>', unsafe_allow_html=True)

        st.markdown("**Top Risk Drivers**")
        st.markdown("""
        • Cross-border velocity anomaly  
        • Offshore beneficiary linkage  
        • Sudden transaction spike  
        • Behavioural deviation from baseline  
        """)

        st.markdown('</div>', unsafe_allow_html=True)

        # -----------------------------
        # TRANSACTION VELOCITY (MOVED HERE)
        # -----------------------------
        st.markdown('<div class="bb-card">', unsafe_allow_html=True)
        st.markdown('<div class="bb-section-title">Transaction Velocity (Last 7 Days)</div>', unsafe_allow_html=True)

        v1, v2 = st.columns([3,1])
        with v1:
            st.progress(85)
            st.caption("Cross-border transaction velocity vs historical baseline")

        with v2:
            st.markdown('<div class="bb-metric">+12%</div><div class="bb-small">Weekly Increase</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # -----------------------------
        # FINANCIAL EXPOSURE
        # -----------------------------
        st.markdown('<div class="bb-card">', unsafe_allow_html=True)
        st.markdown('<div class="bb-section-title">Financial Exposure Breakdown</div>', unsafe_allow_html=True)

        st.markdown("""
        Highest Single Transfer: $125,000  
        Offshore Jurisdictions: 3  
        PEP Screening: Negative  
        Sanctions Hit: None  
        Monitoring Window: 30 Days  
        """)

        st.markdown('</div>', unsafe_allow_html=True)

        # -----------------------------
        # RECENT TRANSACTION TIMELINE (MOVED HERE)
        # -----------------------------
        st.markdown('<div class="bb-card">', unsafe_allow_html=True)
        st.markdown('<div class="bb-section-title">Recent Transaction Timeline</div>', unsafe_allow_html=True)

        st.markdown("""
        • Day -7: $45,000 transfer to SG entity  
        • Day -5: $62,000 transfer to HK beneficiary  
        • Day -3: $125,000 offshore wire (flagged)  
        • Day -1: $38,000 cross-border movement  
        """)

        st.markdown('</div>', unsafe_allow_html=True)

        # -----------------------------
        # ALERT NARRATIVE (NOW LAST)
        # -----------------------------
        st.markdown('<div class="bb-card">', unsafe_allow_html=True)
        st.markdown('<div class="bb-section-title">Alert Narrative</div>', unsafe_allow_html=True)
        st.write("**Alert Reason:**", case["alert_reason"])
        st.write("**Transaction Summary:**", case["transaction_summary"])
        st.markdown('</div>', unsafe_allow_html=True)

    # ===============================
    # RIGHT COLUMN – RISK + ACTIONS
    # ===============================
    with right:

        st.markdown('<div class="bb-card">', unsafe_allow_html=True)
        st.markdown('<div class="bb-section-title">Risk Assessment</div>', unsafe_allow_html=True)

        st.markdown(
            f'<div class="bb-risk-gauge" style="--risk:{case["risk_score"]};">'
            f'{case["risk_score"]}</div>',
            unsafe_allow_html=True
        )

        st.markdown("""
        <div class="bb-small" style="text-align:center; margin-top:10px;">
        Risk Trend: ↑ 12% (7 days) <br>
        Model Confidence: 92% <br>
        AML Model: Hybrid v2.3
        </div>
        """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # --- Model Explainability + Regulatory Impact card ---
        st.markdown('<div class="bb-card">', unsafe_allow_html=True)
        st.markdown('<div class="bb-section-title">Model Explainability</div>', unsafe_allow_html=True)

        st.markdown("""
        Primary Model: Hybrid Rules + ML  
        SHAP Feature Impact: High on cross-border weight  
        Anomaly Score Percentile: 94th  
        False Positive Probability: 8%  
        """)

        st.markdown('<div class="bb-divider"></div>', unsafe_allow_html=True)

        st.markdown("**Regulatory Impact Assessment**")
        st.markdown("""
        • CTR Threshold Interaction: Yes  
        • SAR Filing Threshold: Breached  
        • Jurisdiction Risk Level: Elevated (APAC Offshore)  
        • Escalation Requirement: Tier 3 Mandatory Review  
        """)

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="bb-card">', unsafe_allow_html=True)
        st.markdown('<div class="bb-section-title">Action Center</div>', unsafe_allow_html=True)

        generate_clicked = st.button("Generate SAR", use_container_width=True)
        escalate_clicked = st.button("Escalate to Manager", use_container_width=True)
        false_positive_clicked = st.button("Mark as False Positive", use_container_width=True)

        if generate_clicked:
            with st.spinner("Generating Suspicious Activity Report..."):
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

                case["status"] = "SAR_DRAFTED"
                st.session_state.generated_sar = sar_output

            st.success("SAR Draft Generated Successfully")

        if escalate_clicked:
            st.warning("Case escalated to Manager")

        if false_positive_clicked:
            case["status"] = "CLOSED_FALSE_POSITIVE"
            st.success("Marked as False Positive")


        st.markdown('</div>', unsafe_allow_html=True)

    if "generated_sar" in st.session_state:
        st.markdown("---")
        st.subheader("Generated SAR Narrative Report")

        st.text_area(
            "SAR Narrative",
            st.session_state.generated_sar,
            height=350
        )

        # -------- Generate PDF Button BELOW narrative --------
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []

        styles = getSampleStyleSheet()
        elements.append(Paragraph("<b>Suspicious Activity Report</b>", styles["Title"]))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph(f"Case ID: {case['case_id']}", styles["Normal"]))
        elements.append(Paragraph(f"Customer ID: {case['customer_id']}", styles["Normal"]))
        elements.append(Paragraph(f"Risk Score: {case['risk_score']}", styles["Normal"]))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph(st.session_state.generated_sar.replace("\n", "<br/>"), styles["Normal"]))

        doc.build(elements)
        buffer.seek(0)

        st.download_button(
            label="Download SAR as PDF",
            data=buffer,
            file_name=f"SAR_Case_{case['case_id']}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
