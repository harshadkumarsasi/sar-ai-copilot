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
# Dark Theme (Fixed – No Toggle)
# -------------------------------
def apply_theme():
    css_vars = {
        "bg": "#0F172A",
        "card": "#111827",
        "text_primary": "#F1F5F9",
        "text_secondary": "#94A3B8",
        "border": "#1F2937",
        "primary": "#00AEEF",
        "accent_success": "#22C55E",
        "accent_danger": "#DC2626",
        "card_overlay": "rgba(30,41,59,0.4)",
        "gauge_rest": "#1F2937",
        "role_analyst": "#1E40AF",
        "role_manager": "#6D28D9",
        "role_admin": "#B91C1C",
    }

    st.markdown(
        f"""
        <style>
        :root {{
            --bg: {css_vars['bg']};
            --card: {css_vars['card']};
            --text-primary: {css_vars['text_primary']};
            --text-secondary: {css_vars['text_secondary']};
            --border: {css_vars['border']};
            --primary: {css_vars['primary']};
            --accent-success: {css_vars['accent_success']};
            --accent-danger: {css_vars['accent_danger']};
            --card-overlay: {css_vars['card_overlay']};
            --gauge-rest: {css_vars['gauge_rest']};
            --role-analyst: {css_vars['role_analyst']};
            --role-manager: {css_vars['role_manager']};
            --role-admin: {css_vars['role_admin']};
        }}

        .stApp {{
            background-color: var(--bg);
            color: var(--text-primary);
        }}

        .block-container {{
            padding-top: 0rem;
        }}

        section[data-testid="stSidebar"] {{
            background-color: var(--card);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

apply_theme()

# -------------------------------
# Sidebar Navigation
# -------------------------------
# -------------------------------
# Navigation State Initialization
# -------------------------------
if "selected_tab" not in st.session_state:
    st.session_state.selected_tab = "Dashboard"

selected_tab = st.session_state.selected_tab

with st.sidebar:
    st.markdown("""
    <style>
    section[data-testid="stSidebar"] > div:first-child {
        display: flex;
        flex-direction: column;
        height: 100vh;
        padding-top: 0px !important;
        margin-top: 0px !important;
    }

    .sidebar-top {
        margin-top: -80px;
        padding-top: 0px;
    }

    .sidebar-title {
        font-size: 36px;
        font-weight: 900;
        letter-spacing: 1px;
        color: var(--text-primary);
        margin-top: 0px;
        margin-bottom: 4px;
    }

    .sidebar-sub {
        font-size: 18px;
        font-weight: 700;
        color: var(--text-secondary);
        margin-bottom: 20px;
    }

    .sidebar-bottom {
        margin-top: auto;
        padding-top: 20px;
        border-top: 1px solid var(--border);
    }

    /* Navigation Button Styling */
    .stSidebar .stButton > button {
        background: #1E293B;
        color: var(--text-primary);
        border: 1px solid var(--border);
        border-radius: 10px;
        height: 44px;
        font-weight: 600;
        transition: all 0.25s ease;
    }

    .stSidebar .stButton > button:hover {
        background: linear-gradient(90deg, #00E5FF 0%, #3B82F6 40%, #7C3AED 100%);
        color: #FFFFFF;
        border: 1px solid #00E5FF;
        box-shadow: 0 0 12px rgba(0, 229, 255, 0.6);
        transform: translateY(-1px);
    }

    /* Selected (Primary) Navigation Button */
    .stSidebar .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #2563EB, #1E40AF);
        color: white;
        border: none;
    }

    .stSidebar .stButton > button[kind="primary"]:hover {
        background: linear-gradient(90deg, #00F5FF 0%, #2563EB 50%, #8B5CF6 100%);
        box-shadow: 0 0 14px rgba(59, 130, 246, 0.7);
        transform: translateY(-1px);
    }
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="sidebar-top">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-title">SAR AI Copilot</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-sub">Compliance Platform</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


    selected_tab = st.session_state.selected_tab

    # --- Clean Navigation Cells ---
    def nav_button(label):
        is_selected = st.session_state.selected_tab == label

        if st.button(
            label,
            use_container_width=True,
            key=f"nav_{label}",
            type="primary" if is_selected else "secondary"
        ):
            st.session_state.selected_tab = label
            st.rerun()

    nav_button("Dashboard")
    nav_button("Governance")

    st.markdown('<div class="sidebar-bottom">', unsafe_allow_html=True)

    st.markdown("**Demo Analyst**")
    st.caption("analyst@bank.com")
    st.caption("ANALYST")

    st.markdown("---")
    st.button("Sign Out")
    st.markdown('</div>', unsafe_allow_html=True)

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
        },
        {
            "case_id": 3,
            "customer_id": "CUST-003",
            "customer_name": "Michael Tan",
            "risk_score": 91.2,
            "status": "NEW",
            "alert_reason": "Rapid movement of funds across high-risk jurisdictions.",
            "transaction_summary": "Three large transfers routed through layered shell accounts in 48 hours."
        },
        {
            "case_id": 4,
            "customer_id": "CUST-004",
            "customer_name": "Sara Williams",
            "risk_score": 67.4,
            "status": "UNDER_REVIEW",
            "alert_reason": "Inconsistent income declaration patterns.",
            "transaction_summary": "Account activity inconsistent with declared business revenue profile."
        },
        {
            "case_id": 5,
            "customer_id": "CUST-005",
            "customer_name": "Arjun Mehta",
            "risk_score": 78.9,
            "status": "NEW",
            "alert_reason": "Structuring behavior across multiple accounts.",
            "transaction_summary": "Repeated sub-threshold deposits across linked accounts within 5 days."
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
            color: var(--text-secondary);
            margin-top: 6px;
        }
        .gov-card {
            padding: 18px;
            border-radius: 12px;
            border: 1px solid var(--border);
            background-color: var(--card-overlay);
        }
        .gov-metric {
            font-size: 26px;
            font-weight: 700;
            margin-top: 8px;
        }
        .gov-label {
            font-size: 13px;
            color: var(--text-secondary);
        }
        .role-badge {
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 600;
        }
        .role-analyst { background: var(--role-analyst); color: var(--card); }
        .role-manager { background: var(--role-manager); color: var(--card); }
        .role-admin { background: var(--role-admin); color: var(--card); }
        .timeline-item {
            padding: 10px 0;
            border-bottom: 1px solid var(--border);
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

    st.markdown(
        """
        <div style="
            display:flex;
            align-items:center;
            gap:10px;
            font-size:14px;
            font-weight:700;
            letter-spacing:1px;
            text-transform:uppercase;
            color:#F59E0B;
            padding-top: 15px;
            margin-bottom:15px;
        ">
            <span style="font-size:16px;">⚠️</span>
            AML Fraud Detection
        </div>
        """,
        unsafe_allow_html=True
    )
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

    m1.markdown(f"""
        <div style="font-size:14px; color:var(--text-secondary);">Total Active Cases</div>
        <div style="font-size:34px; font-weight:800; color:#00AEEF;">{total_cases}</div>
    """, unsafe_allow_html=True)
    m2.markdown(f"""
        <div style="font-size:14px; color:var(--text-secondary);">High Risk Cases</div>
        <div style="font-size:34px; font-weight:800; color:#DC2626;">{high_risk}</div>
    """, unsafe_allow_html=True)
    m3.markdown(f"""
        <div style="font-size:14px; color:var(--text-secondary);">Medium Risk Cases</div>
        <div style="font-size:34px; font-weight:800; color:#F59E0B;">{medium_risk}</div>
    """, unsafe_allow_html=True)
    m4.markdown(f"""
        <div style="font-size:14px; color:var(--text-secondary);">Low Risk Cases</div>
        <div style="font-size:34px; font-weight:800; color:#22C55E;">{low_risk}</div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ===============================
    # WORKFLOW PIPELINE
    # ===============================
    st.markdown("### Case Workflow Pipeline")

    new_cases = len([c for c in st.session_state.cases if c["status"] == "NEW"])
    under_review = len([c for c in st.session_state.cases if c["status"] == "UNDER_REVIEW"])
    drafted = len([c for c in st.session_state.cases if c["status"] == "SAR_DRAFTED"])

    p1, p2, p3 = st.columns(3)
    p1.markdown(f"""
        <div style="font-size:13px; color:var(--text-secondary);">NEW</div>
        <div style="font-size:30px; font-weight:800; color:#00AEEF;">{new_cases}</div>
    """, unsafe_allow_html=True)
    p2.markdown(f"""
        <div style="font-size:13px; color:var(--text-secondary);">UNDER REVIEW</div>
        <div style="font-size:30px; font-weight:800; color:#F59E0B;">{under_review}</div>
    """, unsafe_allow_html=True)
    p3.markdown(f"""
        <div style="font-size:13px; color:var(--text-secondary);">SAR DRAFTED</div>
        <div style="font-size:30px; font-weight:800; color:#22C55E;">{drafted}</div>
    """, unsafe_allow_html=True)

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

    st.markdown("""
<style>
[data-testid="stHorizontalBlock"] > div:hover {
    background-color: rgba(59,130,246,0.05);
    transition: background-color 0.2s ease;
}
</style>
""", unsafe_allow_html=True)
    # ===============================
    # INSTITUTIONAL TERMINAL HEADER
    # ===============================
    header_cols = st.columns([0.6, 2.2, 1, 1, 1.2, 0.8, 1, 1])

    header_cols[0].markdown("**ID**")
    header_cols[1].markdown("**CUSTOMER**")
    header_cols[2].markdown("**RISK SCORE**")
    header_cols[3].markdown("**RISK**")
    header_cols[4].markdown("**STATUS**")
    header_cols[5].markdown("**SLA (HRS)**")
    header_cols[6].markdown("**GEOGRAPHY**")
    header_cols[7].markdown("**ACTION**")

    st.divider()

    # ===============================
    # CASE ROWS
    # ===============================
    for case in st.session_state.cases:

        # Filtering logic
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

        # Risk tier logic
        if case["risk_score"] >= 80:
            risk_label = "HIGH"
            risk_color = "#DC2626"
        elif case["risk_score"] >= 70:
            risk_label = "MED"
            risk_color = "#F59E0B"
        else:
            risk_label = "LOW"
            risk_color = "#22C55E"

        # SLA logic
        sla_hours = max(0, 4 - case["case_id"])

        if sla_hours <= 0:
            sla_color = "#DC2626"
        elif sla_hours <= 1:
            sla_color = "#F59E0B"
        else:
            sla_color = "#22C55E"

        # Geography (demo value)
        geography = "APAC" if case["case_id"] % 2 == 0 else "EMEA"

        row_cols = st.columns([0.6, 2.2, 1, 1, 1.2, 0.8, 1, 1])

        # ID
        row_cols[0].markdown(f"#{case['case_id']}")

        # Customer
        row_cols[1].markdown(
            f"**{case['customer_name']}**  \n"
            f"<span style='color:#64748B; font-size:12px;'>{case['customer_id']} | {case['status']}</span>",
            unsafe_allow_html=True
        )

        # Risk Score
        row_cols[2].markdown(
            f"<div style='font-weight:700; text-align:right; font-family:monospace;'>{case['risk_score']:.1f}</div>",
            unsafe_allow_html=True
        )

        # Risk Tier
        row_cols[3].markdown(
            f"<span style='font-weight:700; color:{risk_color};'>{risk_label}</span>",
            unsafe_allow_html=True
        )

        # Status
        row_cols[4].markdown(case["status"])

        # SLA (colored text only)
        row_cols[5].markdown(
            f"<div style='font-weight:700; color:{sla_color}; text-align:right; font-family:monospace;'>{sla_hours}h</div>",
            unsafe_allow_html=True
        )

        # Geography
        row_cols[6].markdown(geography)

        if row_cols[7].button(
            "Open",
            key=f"open_case_{case['case_id']}",
            use_container_width=True
        ):
            st.session_state.selected_case = case
            st.rerun()

        st.divider()

else:
    case = st.session_state.selected_case

    # Use CSS variables (defined in apply_theme) for all case detail colors
    st.markdown(f"""
    <style>
    .bb-header {{
        padding: 20px 0;
        border-bottom: 1px solid var(--border);
        margin-bottom: 20px;
    }}
    .bb-title {{
        font-size: 28px;
        font-weight: 800;
        letter-spacing: 0.5px;
    }}
    .bb-meta {{
        font-size: 13px;
        color: var(--text-secondary);
        margin-top: 6px;
    }}
    .bb-badge-high {{
        background: var(--accent-danger);
        color: var(--card);
        padding:4px 10px;
        border-radius:6px;
        font-size:12px;
        font-weight:600;
    }}
    .bb-card {{
        background: var(--card);
        border:1px solid var(--border);
        border-radius:10px;
        padding:18px;
        margin-bottom:18px;
    }}
    .bb-card:empty {{
        display: none !important;
    }}
    .bb-section-title {{
        font-size:14px;
        font-weight:700;
        letter-spacing:0.5px;
        color: var(--text-secondary);
        margin-bottom:12px;
        text-transform:uppercase;
    }}
    .bb-metric {{
        font-size:22px;
        font-weight:700;
    }}
    .bb-small {{
        font-size:12px;
        color: var(--text-secondary);
    }}
    .bb-risk-gauge {{
        width:120px;
        height:120px;
        border-radius:50%;
        background:conic-gradient(var(--accent-danger) calc(var(--risk)*1%), var(--gauge-rest) 0%);
        display:flex;
        align-items:center;
        justify-content:center;
        font-size:26px;
        font-weight:700;
        color: var(--text-primary);
        margin:auto;
    }}
    .bb-divider {{
        border-top:1px solid var(--border);
        margin:20px 0;
    }}
    </style>
    """, unsafe_allow_html=True)

    # ===============================
    # HEADER
    # ===============================
    st.markdown(
        f"""
        <div style="font-size:36px; font-weight:900; letter-spacing:1.5px; text-transform:uppercase; color:var(--text-primary); margin-bottom:18px;">
        Case Details Overview
        </div>
        """,
        unsafe_allow_html=True
    )

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
