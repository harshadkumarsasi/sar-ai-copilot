"""Streamlit interface for the SAR AI Copilot demo."""

import os
import sys
from datetime import datetime
from html import escape
from io import BytesIO

import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from backend.llm.model import SARGenerationError, SARInput, SARLLM

st.set_page_config(page_title="SAR Studio | AML casework", page_icon="◈", layout="wide")

MODEL_NAME = "mistral"
STATUS_LABELS = {
    "NEW": "New",
    "UNDER_REVIEW": "In review",
    "SAR_DRAFTED": "SAR drafted",
    "CLOSED_FALSE_POSITIVE": "Closed · false positive",
}

DEMO_DETAILS = {
    1: {
        "geography": "EMEA",
        "corridor": "United Kingdom → Singapore",
        "sla_hours": 3,
        "flagged_transactions": 17,
        "total_exposure": 482_000,
        "peer_deviation": 240,
        "velocity": 85,
        "weekly_change": 12,
        "highest_transfer": 125_000,
        "offshore_jurisdictions": 3,
        "pep_screening": "No match",
        "sanctions_screening": "No match",
        "monitoring_window": "30 days",
        "risk_trend": "+12% over 7 days",
        "model_confidence": 92,
        "model_name": "Hybrid rules + ML v2.3",
        "risk_drivers": [
            "Cross-border velocity anomaly",
            "Offshore beneficiary linkage",
            "Sudden transaction spike",
            "Behaviour differs from customer baseline",
        ],
        "timeline": [
            ("Day -7", 45_000, "Transfer to a Singapore-based entity"),
            ("Day -5", 62_000, "Payment to a new Hong Kong beneficiary"),
            ("Day -3", 125_000, "Offshore wire flagged for review"),
            ("Day -1", 38_000, "Additional cross-border movement"),
        ],
        "regulatory_signals": [
            "Activity exceeds the internal SAR review threshold",
            "Cross-border activity involves three offshore jurisdictions",
            "Enhanced monitoring recommended pending analyst review",
        ],
    },
    2: {
        "geography": "APAC",
        "corridor": "India · domestic cash activity",
        "sla_hours": 2,
        "flagged_transactions": 9,
        "total_exposure": 74_500,
        "peer_deviation": 118,
        "velocity": 68,
        "weekly_change": 8,
        "highest_transfer": 9_800,
        "offshore_jurisdictions": 0,
        "pep_screening": "No match",
        "sanctions_screening": "No match",
        "monitoring_window": "14 days",
        "risk_trend": "+8% over 7 days",
        "model_confidence": 88,
        "model_name": "Hybrid rules + ML v2.3",
        "risk_drivers": [
            "Repeated deposits close to the reporting threshold",
            "Deposit frequency increased over the last two weeks",
            "Cash activity differs from the expected account pattern",
        ],
        "timeline": [
            ("Day -6", 9_700, "Cash deposit below review threshold"),
            ("Day -4", 9_800, "Second deposit at a separate branch"),
            ("Day -2", 9_600, "Deposit followed by same-day transfer"),
            ("Day -1", 8_900, "Additional cash deposit"),
        ],
        "regulatory_signals": [
            "Repeated sub-threshold deposits require review",
            "No sanctions or PEP match in the demo screening data",
            "Confirm source of funds and expected cash profile",
        ],
    },
    3: {
        "geography": "EMEA",
        "corridor": "United Arab Emirates → United Kingdom",
        "sla_hours": 1,
        "flagged_transactions": 12,
        "total_exposure": 615_000,
        "peer_deviation": 310,
        "velocity": 94,
        "weekly_change": 31,
        "highest_transfer": 280_000,
        "offshore_jurisdictions": 4,
        "pep_screening": "Review required",
        "sanctions_screening": "No match",
        "monitoring_window": "48 hours",
        "risk_trend": "+31% over 7 days",
        "model_confidence": 95,
        "model_name": "Hybrid rules + ML v2.3",
        "risk_drivers": [
            "Rapid movement across multiple jurisdictions",
            "Funds pass through newly observed counterparties",
            "Transaction timing is inconsistent with prior activity",
        ],
        "timeline": [
            ("Day -2", 160_000, "Inbound international wire"),
            ("Day -2", 175_000, "Funds moved to a new intermediary"),
            ("Day -1", 280_000, "Outbound transfer to a high-risk corridor"),
        ],
        "regulatory_signals": [
            "Rapid movement of funds warrants expedited review",
            "Several intermediary entities appear in the transaction path",
            "Confirm beneficial ownership before filing decisions",
        ],
    },
    4: {
        "geography": "North America",
        "corridor": "United States · domestic business activity",
        "sla_hours": 4,
        "flagged_transactions": 6,
        "total_exposure": 128_000,
        "peer_deviation": 74,
        "velocity": 42,
        "weekly_change": -3,
        "highest_transfer": 42_000,
        "offshore_jurisdictions": 1,
        "pep_screening": "No match",
        "sanctions_screening": "No match",
        "monitoring_window": "30 days",
        "risk_trend": "Stable over 7 days",
        "model_confidence": 81,
        "model_name": "Hybrid rules + ML v2.3",
        "risk_drivers": [
            "Account activity differs from declared business revenue",
            "One transfer involves an unfamiliar offshore counterparty",
            "Transaction volume is elevated but not accelerating",
        ],
        "timeline": [
            ("Day -9", 18_000, "Incoming business payment"),
            ("Day -6", 42_000, "Transfer to an unfamiliar counterparty"),
            ("Day -3", 24_000, "Outgoing transfer following cash deposit"),
        ],
        "regulatory_signals": [
            "Review the mismatch with the declared business profile",
            "No sanctions or PEP match in the demo screening data",
            "Current signal supports analyst review, not an automated conclusion",
        ],
    },
    5: {
        "geography": "APAC",
        "corridor": "India → Singapore",
        "sla_hours": 2,
        "flagged_transactions": 14,
        "total_exposure": 206_000,
        "peer_deviation": 186,
        "velocity": 79,
        "weekly_change": 19,
        "highest_transfer": 58_000,
        "offshore_jurisdictions": 2,
        "pep_screening": "No match",
        "sanctions_screening": "No match",
        "monitoring_window": "5 days",
        "risk_trend": "+19% over 7 days",
        "model_confidence": 90,
        "model_name": "Hybrid rules + ML v2.3",
        "risk_drivers": [
            "Sub-threshold deposits span multiple linked accounts",
            "Activity increased across a short monitoring window",
            "Funds move quickly to an overseas beneficiary",
        ],
        "timeline": [
            ("Day -5", 8_500, "Deposit to linked account A"),
            ("Day -4", 9_200, "Deposit to linked account B"),
            ("Day -2", 58_000, "Consolidated transfer to Singapore"),
            ("Day -1", 31_000, "Follow-on international transfer"),
        ],
        "regulatory_signals": [
            "Linked-account activity requires consolidated review",
            "Repeated deposits are followed by rapid outbound transfers",
            "Confirm account ownership and source of funds",
        ],
    },
}


def apply_theme():
    st.markdown(
        """
        <style>
        :root {
            --canvas: #f4f6f1;
            --surface: #ffffff;
            --ink: #172a23;
            --muted: #5e6d64;
            --line: #e2e8e1;
            --forest: #164b3a;
            --forest-deep: #102b24;
            --lime: #d8f36a;
            --lime-soft: #eff8cf;
            --amber: #a45b12;
            --amber-soft: #fff2d6;
            --red: #a33832;
            --red-soft: #fde9e5;
            --blue: #315a83;
            --blue-soft: #eaf1f8;
            --text-color: #172a23;
            --background-color: #f4f6f1;
            --secondary-background-color: #ffffff;
            --primary-color: #164b3a;
            --border-color: #e2e8e1;
            color-scheme: light;
        }

        header { visibility: hidden; }
        .stApp { background: var(--canvas); color: var(--ink); }
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"],
        [data-testid="stMain"] .block-container {
            background: var(--canvas) !important;
            color: var(--ink);
        }
        [data-testid="stMarkdownContainer"],
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li { color: var(--ink); }
        [data-testid="stWidgetLabel"],
        [data-testid="stWidgetLabel"] p,
        [data-testid="stCaptionContainer"] { color: var(--muted) !important; }
        [data-testid="stMain"] .block-container {
            box-sizing: border-box;
            width: 100%;
            max-width: 1280px;
            margin-inline: auto;
            padding: 32px clamp(18px, 3vw, 42px) 64px !important;
        }
        [data-testid="stSidebar"],
        [data-testid="stSidebarContent"],
        [data-testid="stSidebarUserContent"],
        [data-testid="stSidebarHeader"] {
            background: var(--forest-deep) !important;
        }
        [data-testid="stSidebar"] {
            border-right: 1px solid rgba(255,255,255,.08);
        }
        [data-testid="stSidebarContent"] { padding: 18px 14px 28px !important; }
        [data-testid="stSidebarUserContent"] { background: transparent !important; }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
            color: #c3d3ca !important;
        }
        [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.14); }
        [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--surface);
            border-color: var(--line) !important;
            border-radius: 16px;
        }
        div.stButton > button {
            border-radius: 10px;
            min-height: 2.65rem;
            font-weight: 650;
            border-color: var(--line);
            transition: transform .15s ease, box-shadow .15s ease;
        }
        div.stButton > button[kind="secondary"],
        [data-testid="stDownloadButton"] button {
            background: var(--surface) !important;
            border-color: var(--line) !important;
            color: var(--ink) !important;
        }
        div.stButton > button[kind="secondary"] p,
        [data-testid="stDownloadButton"] button p {
            color: var(--ink) !important;
        }
        div.stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(23,42,35,.10);
            border-color: #9db5a8;
        }
        div.stButton > button[kind="primary"] {
            background: var(--forest) !important;
            border-color: var(--forest) !important;
            color: #fff !important;
        }
        div.stButton > button[kind="primary"] p,
        div.stButton > button[kind="primary"] span {
            color: #fff !important;
        }
        div.stButton > button[kind="primary"]:hover {
            background: #205b45 !important;
            border-color: #205b45 !important;
            color: #fff !important;
        }
        div.stButton > button { white-space: normal; }
        div.stButton > button p { line-height: 1.25; }
        [data-testid="stMetric"] {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 16px 18px;
        }
        [data-testid="stMetricLabel"] {
            color: #5e6d64 !important;
            font-size: 13px !important;
        }
        [data-testid="stMetricValue"],
        [data-testid="stMetricValue"] * {
            color: var(--ink) !important;
            font-size: clamp(18px, 2vw, 29px) !important;
            line-height: 1.15 !important;
        }
        [data-testid="stMetricValue"] {
            overflow: visible !important;
            text-overflow: clip !important;
            white-space: normal !important;
            overflow-wrap: anywhere;
        }
        [data-baseweb="select"] > div {
            background: var(--surface) !important;
            color: var(--ink) !important;
            border-color: var(--line) !important;
        }
        [data-baseweb="select"] *,
        [data-testid="stTextInput"] input {
            color: var(--ink) !important;
        }
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea {
            background: var(--surface) !important;
            border-color: var(--line) !important;
            color: var(--ink) !important;
            -webkit-text-fill-color: var(--ink) !important;
        }
        [data-testid="stTextInput"] input:focus,
        [data-testid="stTextArea"] textarea:focus {
            border-color: var(--forest) !important;
            box-shadow: 0 0 0 1px var(--forest) !important;
        }
        [data-testid="stTextArea"] textarea {
            font-size: 15px !important;
            line-height: 1.6 !important;
        }
        [data-testid="stSidebar"] div.stButton > button[kind="secondary"] {
            background: rgba(255,255,255,.06) !important;
            border-color: rgba(255,255,255,.18) !important;
            color: #f3f7f4 !important;
        }
        [data-testid="stSidebar"] div.stButton > button[kind="secondary"] p {
            color: #f3f7f4 !important;
        }
        [data-testid="stSidebar"] div.stButton > button[kind="primary"] {
            background: var(--lime) !important;
            border-color: var(--lime) !important;
            color: var(--forest-deep) !important;
        }
        [data-testid="stSidebar"] div.stButton > button[kind="primary"] p {
            color: var(--forest-deep) !important;
        }
        [data-testid="stProgressBar"] > div > div {
            background: var(--forest);
        }
        .brand-mark {
            display: inline-flex;
            width: 38px;
            height: 38px;
            align-items: center;
            justify-content: center;
            margin-right: 9px;
            border-radius: 12px;
            background: var(--lime);
            color: var(--forest-deep);
            font-size: 21px;
            font-weight: 900;
            vertical-align: middle;
        }
        .eyebrow {
            color: var(--forest);
            font-size: 11px;
            font-weight: 800;
            letter-spacing: .14em;
            text-transform: uppercase;
        }
        .hero {
            padding: 26px 30px;
            margin: 8px 0 22px;
            border-radius: 20px;
            background: var(--forest-deep);
            color: #f4f8f2;
        }
        .hero h1 {
            color: #f4f8f2;
            font-size: clamp(30px, 4vw, 46px);
            letter-spacing: -.04em;
            line-height: 1.08;
            margin: 10px 0 8px;
        }
        .hero p { color: #c1d2c8; margin: 0; }
        .hero-tag {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 999px;
            background: rgba(216,243,106,.14);
            color: var(--lime);
            font-size: 11px;
            font-weight: 750;
            letter-spacing: .08em;
            text-transform: uppercase;
        }
        .metric-note { color: var(--muted); font-size: 12px; }
        .case-name { color: var(--ink); font-size: 17px; font-weight: 750; }
        .case-id { color: var(--muted); font-size: 12px; }
        .risk-pill, .status-pill {
            display: inline-block;
            padding: 5px 9px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: .04em;
            white-space: nowrap;
        }
        .risk-high { background: var(--red-soft); color: var(--red); }
        .risk-medium { background: var(--amber-soft); color: var(--amber); }
        .risk-low { background: var(--lime-soft); color: var(--forest); }
        .status-new { background: var(--blue-soft); color: var(--blue); }
        .status-review { background: var(--amber-soft); color: var(--amber); }
        .status-drafted { background: var(--lime-soft); color: var(--forest); }
        .status-closed { background: #edf0ed; color: #66716b; }
        .section-heading {
            color: var(--ink);
            font-size: 16px;
            font-weight: 800;
            letter-spacing: -.01em;
        }
        .section-kicker {
            color: var(--muted);
            font-size: 12px;
            margin-top: -6px;
        }
        .timeline-item {
            padding: 10px 0;
            border-bottom: 1px solid var(--line);
        }
        .timeline-item:last-child { border-bottom: 0; }
        .timeline-day {
            color: var(--forest);
            font-size: 11px;
            font-weight: 800;
            text-transform: uppercase;
        }
        .risk-driver {
            padding: 9px 11px;
            margin: 7px 0;
            border-radius: 10px;
            background: #f4f7f3;
            color: #34483e;
            font-size: 13px;
        }
        .info-note {
            padding: 13px 15px;
            border: 1px solid #dfe9d5;
            border-radius: 12px;
            background: #f7faef;
            color: #51614f;
            font-size: 13px;
        }
        .sidebar-brand {
            color: #fff;
            font-size: 18px;
            font-weight: 800;
            letter-spacing: -.02em;
        }
        .sidebar-brand-row {
            display: flex;
            align-items: center;
            gap: 11px;
            padding: 7px 4px 14px;
        }
        .sidebar-brand-icon {
            display: grid;
            width: 36px;
            height: 36px;
            place-items: center;
            flex: 0 0 36px;
            border-radius: 11px;
            background: var(--lime);
            color: var(--forest-deep);
            font-size: 20px;
            font-weight: 900;
        }
        .sidebar-brand-copy { min-width: 0; }
        .sidebar-brand-subtitle {
            margin-top: 2px;
            color: #a9beb2;
            font-size: 9px;
            font-weight: 750;
            letter-spacing: .11em;
            text-transform: uppercase;
        }
        .sidebar-label {
            color: #a9beb2;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: .15em;
            text-transform: uppercase;
        }
        .sidebar-profile {
            margin: 18px 0 10px;
            padding: 14px;
            border: 1px solid rgba(255,255,255,.12);
            border-radius: 14px;
            background: rgba(255,255,255,.055);
        }
        .sidebar-profile-name {
            color: #fff;
            font-size: 13px;
            font-weight: 750;
        }
        .sidebar-profile-meta {
            margin-top: 5px;
            color: #b7c9bf;
            font-size: 11px;
            line-height: 1.45;
        }
        .stat-card {
            min-width: 0;
            padding: 13px 15px;
            margin: 9px 0;
            border: 1px solid var(--line);
            border-radius: 13px;
            background: var(--surface);
        }
        .stat-label { color: #5e6d64; font-size: 12px; font-weight: 650; }
        .stat-value {
            margin-top: 5px;
            color: var(--ink);
            font-size: clamp(17px, 1.8vw, 23px);
            font-weight: 720;
            line-height: 1.2;
            overflow-wrap: anywhere;
        }
        .timeline-row {
            display: grid;
            grid-template-columns: minmax(4.5rem, .55fr) minmax(8.5rem, 1fr) minmax(0, 3fr);
            align-items: start;
            gap: 14px;
            padding: 13px 0;
            border-bottom: 1px solid var(--line);
        }
        .timeline-row:last-child { border-bottom: 0; }
        .timeline-amount-label {
            color: var(--muted);
            font-size: 11px;
        }
        .timeline-amount-value {
            color: var(--ink);
            font-size: clamp(16px, 1.45vw, 20px);
            font-weight: 750;
            line-height: 1.25;
            font-variant-numeric: tabular-nums;
            white-space: nowrap;
        }
        .timeline-detail {
            min-width: 0;
            padding-top: 2px;
            color: #34483e;
            font-size: 14px;
            line-height: 1.45;
            overflow-wrap: anywhere;
        }
        .evidence-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }
        .evidence-table td {
            padding: 8px 10px;
            border-bottom: 1px solid var(--line);
            vertical-align: top;
            overflow-wrap: anywhere;
        }
        .evidence-table td:first-child {
            width: 35%;
            color: #5e6d64;
            font-weight: 650;
        }
        @media (max-width: 800px) {
            [data-testid="stMain"] .block-container {
                padding: 20px 16px 40px !important;
            }
            .hero { padding: 22px 20px; }
            .timeline-row {
                grid-template-columns: minmax(4rem, .65fr) minmax(0, 2fr);
                gap: 10px;
            }
            .timeline-detail { grid-column: 2; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def risk_level(score):
    if score >= 80:
        return "High", "high"
    if score >= 70:
        return "Medium", "medium"
    return "Low", "low"


def status_class(status):
    return {
        "NEW": "new",
        "UNDER_REVIEW": "review",
        "SAR_DRAFTED": "drafted",
        "CLOSED_FALSE_POSITIVE": "closed",
    }.get(status, "new")


def record_activity(event, case_id=None):
    st.session_state.activity_log.insert(
        0,
        {
            "time": datetime.now().strftime("%H:%M"),
            "event": event,
            "case_id": case_id,
        },
    )
    del st.session_state.activity_log[20:]


def render_pill(label, css_class):
    st.markdown(
        f'<span class="status-pill {css_class}">{escape(label)}</span>',
        unsafe_allow_html=True,
    )


def render_risk_pill(score):
    label, tier = risk_level(score)
    st.markdown(
        f'<span class="risk-pill risk-{tier}">{label} risk</span>',
        unsafe_allow_html=True,
    )


def render_stat_card(label, value):
    st.markdown(
        '<div class="stat-card">'
        f'<div class="stat-label">{escape(label)}</div>'
        f'<div class="stat-value">{escape(str(value))}</div>'
        "</div>",
        unsafe_allow_html=True,
    )


def render_dashboard(cases):
    st.markdown('<div class="eyebrow">AML intelligence / casework</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="hero">
            <span class="hero-tag">Recruiter demo · sample data</span>
            <h1>Review the signal.<br>Make the next move.</h1>
            <p>Prioritize alerts, inspect the evidence, and draft a review-ready SAR narrative with local AI.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    active_cases = [case for case in cases if case["status"] != "CLOSED_FALSE_POSITIVE"]
    high_risk = sum(case["risk_score"] >= 80 for case in active_cases)
    review_count = sum(case["status"] == "UNDER_REVIEW" for case in active_cases)
    drafted_count = sum(case["status"] == "SAR_DRAFTED" for case in active_cases)

    metrics = st.columns(4)
    metrics[0].metric("Active cases", len(active_cases), help="Excludes cases closed as false positives")
    metrics[1].metric("High risk", high_risk, help="Risk score of 80 or higher")
    metrics[2].metric("In review", review_count)
    metrics[3].metric("SAR drafts", drafted_count)

    st.markdown("")
    with st.container():
        st.markdown('<div class="section-heading">Workflow at a glance</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-kicker">Where each active case sits today</div>', unsafe_allow_html=True)
        pipeline = st.columns(3)
        for column, status, title in zip(
            pipeline,
            ("NEW", "UNDER_REVIEW", "SAR_DRAFTED"),
            ("New alerts", "Analyst review", "Drafts prepared"),
        ):
            count = sum(case["status"] == status for case in active_cases)
            column.metric(title, count)

    st.markdown("")
    st.markdown('<div class="section-heading">Case queue</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-kicker">Select a case to review its risk signals, activity timeline, and filing context.</div>',
        unsafe_allow_html=True,
    )
    search_col, risk_col, status_col, geography_col = st.columns([2.2, 1, 1.35, 1.2])
    query = search_col.text_input(
        "Search cases",
        placeholder="Name, customer ID, or case number",
        key="case_search",
    ).strip().lower()
    risk_filter = risk_col.selectbox(
        "Risk level",
        ("All", "High", "Medium", "Low"),
        key="case_risk_filter",
    )
    status_filter = status_col.selectbox(
        "Workflow",
        ("All", *STATUS_LABELS.keys()),
        format_func=lambda value: "All statuses" if value == "All" else STATUS_LABELS[value],
        key="case_status_filter",
    )
    regions = sorted({case["geography"] for case in cases})
    geography_filter = geography_col.selectbox(
        "Geography",
        ("All regions", *regions),
        key="case_geography_filter",
    )

    visible_cases = []
    for case in cases:
        tier, _ = risk_level(case["risk_score"])
        searchable = " ".join(
            (
                str(case["case_id"]),
                f"#{case['case_id']}",
                case["customer_id"],
                case["customer_name"],
                case["alert_reason"],
            )
        ).lower()
        if query and query not in searchable:
            continue
        if risk_filter != "All" and tier != risk_filter:
            continue
        if status_filter != "All" and case["status"] != status_filter:
            continue
        if geography_filter != "All regions" and case["geography"] != geography_filter:
            continue
        visible_cases.append(case)

    visible_cases.sort(key=lambda item: (-item["risk_score"], item["case_id"]))
    st.caption(f"Showing {len(visible_cases)} of {len(cases)} sample cases · sorted by risk")

    if not visible_cases:
        with st.container(border=True):
            st.markdown("**No cases match these filters.**")
            st.caption("Try a different search term or clear one of the filters.")
        return

    for case in visible_cases:
        with st.container(border=True):
            row = st.columns([2.3, 1.05, 1.05, 1.45, 1.2])
            with row[0]:
                st.markdown(
                    f'<div class="case-name">{escape(case["customer_name"])}</div>'
                    f'<div class="case-id">Case #{case["case_id"]} · {escape(case["customer_id"])}</div>',
                    unsafe_allow_html=True,
                )
                st.caption(case["alert_reason"])
            with row[1]:
                st.metric("Risk score", f'{case["risk_score"]:.1f}')
                render_risk_pill(case["risk_score"])
            with row[2]:
                st.caption("Workflow")
                render_pill(STATUS_LABELS[case["status"]], f'status-{status_class(case["status"])}')
                st.caption(f'{case["sla_hours"]}h review SLA')
            with row[3]:
                st.caption("Geography")
                st.markdown(f"**{case['geography']}**")
                st.caption(case["corridor"])
            with row[4]:
                st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)
                if st.button(
                    "Review case →",
                    key=f"open_case_{case['case_id']}",
                    type="primary",
                    use_container_width=True,
                ):
                    st.session_state.selected_case_id = case["case_id"]
                    st.rerun()


def render_timeline(case):
    rows = []
    for day, amount, description in case["timeline"]:
        rows.append(
            '<div class="timeline-row">'
            f'<div class="timeline-day">{escape(day)}</div>'
            '<div><div class="timeline-amount-label">Amount</div>'
            f'<div class="timeline-amount-value">${amount:,.0f}</div></div>'
            f'<div class="timeline-detail">{escape(description)}</div>'
            "</div>"
        )
    st.markdown("".join(rows), unsafe_allow_html=True)


def case_evidence_rows(case):
    return [
        ("Case", f'#{case["case_id"]}'),
        ("Customer", case["customer_name"]),
        ("Customer ID", case["customer_id"]),
        ("Risk score", f'{case["risk_score"]:.1f} / 100'),
        ("Geography and corridor", f'{case["geography"]} · {case["corridor"]}'),
        ("Alert reason", case["alert_reason"]),
        ("Transaction summary", case["transaction_summary"]),
        ("Total exposure", f'${case["total_exposure"]:,.0f}'),
        ("Flagged transaction count", str(case["flagged_transactions"])),
        ("Monitoring window", case["monitoring_window"]),
        ("Highest single transfer", f'${case["highest_transfer"]:,.0f}'),
        ("Offshore jurisdictions", str(case["offshore_jurisdictions"])),
        ("Peer deviation", f'+{case["peer_deviation"]}%'),
        ("Transaction velocity", f'{case["velocity"]}% of expected range'),
        ("Week-over-week change", f'{case["weekly_change"]:+}%'),
        ("Risk trend", case["risk_trend"]),
        ("Model confidence", f'{case["model_confidence"]}%'),
        ("Assessment model", case["model_name"]),
        ("PEP screening", case["pep_screening"]),
        ("Sanctions screening", case["sanctions_screening"]),
    ]


def render_evidence_appendix(case):
    with st.expander("Case evidence and figures", expanded=False):
        table_rows = "".join(
            f"<tr><td>{escape(label)}</td><td>{escape(value)}</td></tr>"
            for label, value in case_evidence_rows(case)
        )
        st.markdown(
            f'<table class="evidence-table">{table_rows}</table>',
            unsafe_allow_html=True,
        )
        st.markdown("**Selected transaction events**")
        render_timeline(case)
        st.markdown("**Risk drivers**")
        for driver in case["risk_drivers"]:
            st.markdown(f"- {escape(driver)}")
        st.markdown("**Review considerations**")
        for signal in case["regulatory_signals"]:
            st.markdown(f"- {escape(signal)}")
        st.caption(
            "The transaction timeline is representative, not necessarily every transaction in "
            "the monitoring window. Demo data is illustrative."
        )


def build_sar_pdf(case, narrative):
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=48,
        leftMargin=48,
        topMargin=48,
        bottomMargin=48,
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="SarBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            spaceAfter=7,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SarSection",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            spaceBefore=8,
            spaceAfter=5,
            textColor=colors.HexColor("#164b3a"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="SarSmall",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
        )
    )
    pdf_narrative = (
        narrative.replace("→", "->")
        .replace("↗", "-")
        .replace("•", "-")
        .encode("cp1252", errors="replace")
        .decode("cp1252")
    )
    elements = [
        Paragraph("Suspicious Activity Report · Draft", styles["Title"]),
        Spacer(1, 14),
        Paragraph(
            "<b>Review required:</b> AI-generated content is not fact-checked. Verify every "
            "statement against source records before filing.",
            styles["BodyText"],
        ),
        Spacer(1, 14),
        Paragraph(f"Case ID: {escape(str(case['case_id']))}", styles["BodyText"]),
        Paragraph(f"Customer ID: {escape(case['customer_id'])}", styles["BodyText"]),
        Paragraph(f"Risk score: {case['risk_score']:.1f}", styles["BodyText"]),
        Paragraph(f"Geography: {escape(case['geography'])}", styles["BodyText"]),
        Spacer(1, 14),
    ]
    for line in pdf_narrative.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("**") and line.endswith("**") and len(line) > 4:
            elements.append(Paragraph(escape(line[2:-2]), styles["SarSection"]))
        elif line.startswith("# "):
            elements.append(Paragraph(escape(line[2:]), styles["SarSection"]))
        elif line.startswith("- "):
            elements.append(Paragraph(f"- {escape(line[2:])}", styles["SarBody"]))
        else:
            elements.append(Paragraph(escape(line.replace("**", "")), styles["SarBody"]))

    elements.extend(
        [
            PageBreak(),
            Paragraph("Case evidence and figures", styles["Heading1"]),
            Paragraph(
                "The following appendix restates the supplied case fields for analyst review. "
                "It does not add independent findings.",
                styles["SarBody"],
            ),
        ]
    )
    evidence_table = [
        [
            Paragraph(escape(label), styles["SarSmall"]),
            Paragraph(escape(value), styles["SarSmall"]),
        ]
        for label, value in case_evidence_rows(case)
    ]
    table = Table(evidence_table, colWidths=[135, document.width - 135], repeatRows=0)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5ef")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#dce5dc")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    elements.append(table)
    elements.extend(
        [
            Spacer(1, 12),
            Paragraph("Selected transaction events", styles["Heading2"]),
        ]
    )
    timeline_rows = [
        [
            Paragraph("Relative time", styles["SarSmall"]),
            Paragraph("Amount", styles["SarSmall"]),
            Paragraph("Description", styles["SarSmall"]),
        ]
    ]
    timeline_rows.extend(
        [
            Paragraph(escape(day), styles["SarSmall"]),
            Paragraph(f'${amount:,.0f}', styles["SarSmall"]),
            Paragraph(escape(description), styles["SarSmall"]),
        ]
        for day, amount, description in case["timeline"]
    )
    timeline_table = Table(
        timeline_rows,
        colWidths=[80, 90, document.width - 170],
        repeatRows=1,
    )
    timeline_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf1eb")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#dce5dc")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    elements.append(timeline_table)
    elements.extend(
        [
            Spacer(1, 12),
            Paragraph("Risk drivers and review considerations", styles["Heading2"]),
        ]
    )
    for item in [*case["risk_drivers"], *case["regulatory_signals"]]:
        elements.append(Paragraph(f"- {escape(item)}", styles["SarSmall"]))
    elements.append(
        Paragraph(
            "Data limitation: expected customer activity, declared income, and calendar dates "
            "are not supplied in this illustrative case record. The timeline is representative "
            "and may not include every transaction.",
            styles["SarSmall"],
        )
    )
    document.build(elements)
    buffer.seek(0)
    return buffer


def render_case_detail(case):
    back_col, status_col, _ = st.columns([1.3, 1.3, 5])
    if back_col.button("← Case queue", key="back_to_queue"):
        st.session_state.selected_case_id = None
        st.rerun()
    with status_col:
        render_pill(STATUS_LABELS[case["status"]], f'status-{status_class(case["status"])}')

    st.markdown('<div class="eyebrow">Case review · evidence-led assessment</div>', unsafe_allow_html=True)
    st.title(f'Case #{case["case_id"]} · {case["customer_name"]}')
    st.caption(f'{case["customer_id"]}  ·  {case["geography"]}  ·  {case["corridor"]}')

    metric_cols = st.columns(4)
    metric_cols[0].metric("Risk score", f'{case["risk_score"]:.1f}', help="Demo risk score")
    metric_cols[1].metric("Flagged transactions", case["flagged_transactions"])
    metric_cols[2].metric("Total exposure", f'${case["total_exposure"]:,.0f}')
    metric_cols[3].metric("Review SLA", f'{case["sla_hours"]}h')

    left, right = st.columns([1.8, 1], gap="large")
    with left:
        with st.container(border=True):
            st.markdown('<div class="section-heading">Why this case was flagged</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-kicker">Alert rationale and transaction context</div>', unsafe_allow_html=True)
            st.markdown("**Alert reason**")
            st.write(case["alert_reason"])
            st.markdown("**Transaction summary**")
            st.write(case["transaction_summary"])
            st.markdown("**Geographic corridor**")
            st.write(case["corridor"])

        with st.container(border=True):
            st.markdown('<div class="section-heading">Recent activity</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-kicker">Illustrative transactions from the case monitoring window</div>', unsafe_allow_html=True)
            render_timeline(case)

        with st.container(border=True):
            st.markdown('<div class="section-heading">Risk signals</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-kicker">Signals are supporting evidence, not a finding of wrongdoing.</div>', unsafe_allow_html=True)
            for driver in case["risk_drivers"]:
                st.markdown(f'<div class="risk-driver">↗ &nbsp;{escape(driver)}</div>', unsafe_allow_html=True)

    with right:
        with st.container(border=True):
            st.markdown('<div class="section-heading">Risk assessment</div>', unsafe_allow_html=True)
            render_risk_pill(case["risk_score"])
            st.progress(min(max(int(case["risk_score"]), 0), 100), text=f'{case["risk_score"]:.1f} / 100')
            st.caption(f'Trend: {case["risk_trend"]} · Model confidence: {case["model_confidence"]}%')
            st.caption(f'Assessment model: {case["model_name"]}')
            render_stat_card("Peer deviation", f'+{case["peer_deviation"]}%')
            render_stat_card(
                "Transaction velocity",
                f'{case["velocity"]}% of expected range',
            )
            render_stat_card("Week-over-week change", f'{case["weekly_change"]:+}%')

        with st.container(border=True):
            st.markdown('<div class="section-heading">Screening & review</div>', unsafe_allow_html=True)
            st.write(f'Highest single transfer: ${case["highest_transfer"]:,.0f}')
            st.write(f'Offshore jurisdictions: {case["offshore_jurisdictions"]}')
            st.write(f'PEP screening: {case["pep_screening"]}')
            st.write(f'Sanctions screening: {case["sanctions_screening"]}')
            st.write(f'Monitoring window: {case["monitoring_window"]}')
            st.markdown("**Review considerations**")
            for signal in case["regulatory_signals"]:
                st.markdown(f"- {signal}")

        with st.container(border=True):
            st.markdown('<div class="section-heading">Next action</div>', unsafe_allow_html=True)
            st.caption(f"Draft with local Ollama · {MODEL_NAME}")
            st.markdown(
                '<div class="info-note">AI creates a draft for analyst review. It does not make a filing decision.</div>',
                unsafe_allow_html=True,
            )
            st.markdown("")
            if st.button(
                "✦  Generate SAR draft",
                key=f"generate_sar_{case['case_id']}",
                type="primary",
                use_container_width=True,
            ):
                sar_input = SARInput(
                    customer_profile={
                        "customer_id": case["customer_id"],
                        "customer_name": case["customer_name"],
                        "risk_score": case["risk_score"],
                        "geography": case["geography"],
                        "corridor": case["corridor"],
                        "declared_income": "Not provided in case data",
                        "expected_activity_profile": "Not provided in case data",
                        "customer_history": "Not provided in case data",
                    },
                    transaction_summary={
                        "summary": case["transaction_summary"],
                        "total_exposure": f'${case["total_exposure"]:,.0f}',
                        "flagged_transaction_count": case["flagged_transactions"],
                        "highest_single_transfer": f'${case["highest_transfer"]:,.0f}',
                        "monitoring_window": case["monitoring_window"],
                        "representative_timeline_events": [
                            {
                                "relative_time": day,
                                "amount": f"${amount:,.0f}",
                                "description": description,
                            }
                            for day, amount, description in case["timeline"]
                        ],
                        "timeline_note": (
                            "The timeline contains selected events, not necessarily every "
                            "transaction in the monitoring window."
                        ),
                        "risk_drivers": case["risk_drivers"],
                        "peer_deviation": f'+{case["peer_deviation"]}%',
                        "transaction_velocity": (
                            f'{case["velocity"]}% of expected range'
                        ),
                        "week_over_week_change": f'{case["weekly_change"]:+}%',
                        "risk_trend": case["risk_trend"],
                        "model_confidence": f'{case["model_confidence"]}%',
                        "assessment_model": case["model_name"],
                        "offshore_jurisdictions": case["offshore_jurisdictions"],
                        "pep_screening": case["pep_screening"],
                        "sanctions_screening": case["sanctions_screening"],
                    },
                    alert_reason=case["alert_reason"],
                )
                try:
                    with st.spinner("Drafting the SAR narrative with local Mistral…"):
                        narrative = llm.generate_sar(sar_input)
                except SARGenerationError as exc:
                    st.error(str(exc))
                else:
                    if not narrative.strip():
                        st.error(
                            "Ollama returned an empty draft. Check the local model and try again."
                        )
                    else:
                        st.session_state.sar_drafts[case["case_id"]] = narrative
                        st.session_state[f"sar_narrative_{case['case_id']}"] = narrative
                        case["status"] = "SAR_DRAFTED"
                        record_activity("SAR draft generated", case["case_id"])
                        st.success("Draft ready for analyst review.")
                        st.rerun()

            escalate_col, close_col = st.columns(2)
            if escalate_col.button("Escalate", key=f"escalate_{case['case_id']}", use_container_width=True):
                record_activity("Case escalated for manager review", case["case_id"])
                st.warning("Escalation recorded for manager review.")
            if close_col.button("Close as false positive", key=f"false_positive_{case['case_id']}", use_container_width=True):
                case["status"] = "CLOSED_FALSE_POSITIVE"
                record_activity("Case closed as false positive", case["case_id"])
                st.success("Case marked as a false positive.")
                st.rerun()

    narrative = st.session_state.sar_drafts.get(case["case_id"])
    if narrative:
        st.markdown("")
        with st.container(border=True):
            title_col, download_col = st.columns([3, 1])
            title_col.markdown('<div class="section-heading">SAR narrative draft</div>', unsafe_allow_html=True)
            title_col.markdown(
                '<div class="section-kicker">AI text is not fact-checked; verify every claim against source records before use.</div>',
                unsafe_allow_html=True,
            )
            narrative_key = f"sar_narrative_{case['case_id']}"
            if narrative_key not in st.session_state:
                st.session_state[narrative_key] = narrative
            edited_narrative = st.text_area(
                "SAR narrative",
                key=narrative_key,
                height=540,
                label_visibility="collapsed",
            )
            st.session_state.sar_drafts[case["case_id"]] = edited_narrative
            pdf_data = build_sar_pdf(case, edited_narrative)
            download_col.download_button(
                "Download PDF",
                data=pdf_data,
                file_name=f"SAR_Case_{case['case_id']}.pdf",
                mime="application/pdf",
                key=f"download_sar_{case['case_id']}",
                use_container_width=True,
            )
        render_evidence_appendix(case)


def render_governance(cases):
    st.markdown('<div class="eyebrow">Workspace / governance</div>', unsafe_allow_html=True)
    st.title("Governance & model oversight")
    st.caption("A transparent view of the demo workflow, sample access roles, and recent case actions.")

    drafted = sum(case["status"] == "SAR_DRAFTED" for case in cases)
    under_review = sum(case["status"] == "UNDER_REVIEW" for case in cases)
    closed = sum(case["status"] == "CLOSED_FALSE_POSITIVE" for case in cases)
    metrics = st.columns(4)
    metrics[0].metric("Sample cases", len(cases))
    metrics[1].metric("In review", under_review)
    metrics[2].metric("SAR drafts", drafted)
    metrics[3].metric("Closed", closed)

    left, right = st.columns([1.1, 1], gap="large")
    with left:
        with st.container(border=True):
            st.markdown('<div class="section-heading">Demo access directory</div>', unsafe_allow_html=True)
            st.caption("Sample identities shown for product walkthroughs; this demo does not authenticate users.")
            users = [
                ("U-001", "Jordan Lee", "Analyst"),
                ("U-002", "Priya Nair", "Manager"),
                ("U-003", "Alex Chen", "Administrator"),
            ]
            for user_id, name, role in users:
                user_col, role_col = st.columns([2, 1])
                user_col.markdown(f"**{user_id} · {name}**")
                role_col.caption(role)

        with st.container(border=True):
            st.markdown('<div class="section-heading">Model configuration</div>', unsafe_allow_html=True)
            st.write("Provider: Ollama running locally")
            st.write(f"Model: {MODEL_NAME}")
            st.write("SAR drafts are generated on demand and remain in this Streamlit session.")
            st.markdown(
                '<div class="info-note">Sample metrics and screening signals are illustrative, not production compliance controls.</div>',
                unsafe_allow_html=True,
            )

    with right:
        with st.container(border=True):
            st.markdown('<div class="section-heading">Recent activity</div>', unsafe_allow_html=True)
            if not st.session_state.activity_log:
                st.caption("No activity recorded in this session.")
            for item in st.session_state.activity_log:
                case_text = f' · Case #{item["case_id"]}' if item["case_id"] is not None else ""
                st.markdown(f'**{item["time"]}**  {item["event"]}{case_text}')
                st.divider()


def initialize_state():
    default_cases = [
        {
            "case_id": 1,
            "customer_id": "CUST-001",
            "customer_name": "John Doe",
            "risk_score": 86.5,
            "status": "NEW",
            "alert_reason": "Unusual spike in cross-border transfers.",
            "transaction_summary": "Multiple high-value transfers to offshore accounts within 7 days.",
        },
        {
            "case_id": 2,
            "customer_id": "CUST-002",
            "customer_name": "Priya Sharma",
            "risk_score": 72.3,
            "status": "UNDER_REVIEW",
            "alert_reason": "Structuring detected below reporting threshold.",
            "transaction_summary": "Frequent cash deposits slightly below compliance threshold.",
        },
        {
            "case_id": 3,
            "customer_id": "CUST-003",
            "customer_name": "Michael Tan",
            "risk_score": 91.2,
            "status": "NEW",
            "alert_reason": "Rapid movement of funds across high-risk jurisdictions.",
            "transaction_summary": "Three large transfers routed through layered shell accounts in 48 hours.",
        },
        {
            "case_id": 4,
            "customer_id": "CUST-004",
            "customer_name": "Sara Williams",
            "risk_score": 67.4,
            "status": "UNDER_REVIEW",
            "alert_reason": "Inconsistent income declaration patterns.",
            "transaction_summary": "Account activity inconsistent with declared business revenue profile.",
        },
        {
            "case_id": 5,
            "customer_id": "CUST-005",
            "customer_name": "Arjun Mehta",
            "risk_score": 78.9,
            "status": "NEW",
            "alert_reason": "Structuring behavior across multiple accounts.",
            "transaction_summary": "Repeated sub-threshold deposits across linked accounts within 5 days.",
        },
    ]
    if "cases" not in st.session_state:
        st.session_state.cases = default_cases
    for case in st.session_state.cases:
        for key, value in DEMO_DETAILS[case["case_id"]].items():
            case.setdefault(key, value)
    st.session_state.setdefault("selected_tab", "Dashboard")
    st.session_state.setdefault("selected_case_id", None)
    st.session_state.setdefault("sar_drafts", {})
    st.session_state.setdefault("activity_log", [])


apply_theme()
initialize_state()
llm = SARLLM()

with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand-row">'
        '<div class="sidebar-brand-icon">◈</div>'
        '<div class="sidebar-brand-copy">'
        '<div class="sidebar-brand">SAR Studio</div>'
        '<div class="sidebar-brand-subtitle">AML casework workspace</div>'
        "</div></div>",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sidebar-label">Workspace</div>', unsafe_allow_html=True)
    st.caption("Navigate")
    if st.button(
        "Case queue",
        key="nav_dashboard",
        type="primary" if st.session_state.selected_tab == "Dashboard" else "secondary",
        use_container_width=True,
    ):
        st.session_state.selected_tab = "Dashboard"
        st.session_state.selected_case_id = None
        st.rerun()
    if st.button(
        "Governance",
        key="nav_governance",
        type="primary" if st.session_state.selected_tab == "Governance" else "secondary",
        use_container_width=True,
    ):
        st.session_state.selected_tab = "Governance"
        st.session_state.selected_case_id = None
        st.rerun()
    st.markdown(
        '<div class="sidebar-profile">'
        '<div class="sidebar-profile-name">Demo analyst</div>'
        '<div class="sidebar-profile-meta">Analyst workspace<br>'
        f'Local AI · {escape(MODEL_NAME)}</div></div>',
        unsafe_allow_html=True,
    )
    st.caption("Sample identities and activity are illustrative.")

cases = st.session_state.cases
selected_case = next(
    (case for case in cases if case["case_id"] == st.session_state.selected_case_id),
    None,
)

if selected_case is not None:
    render_case_detail(selected_case)
elif st.session_state.selected_tab == "Governance":
    render_governance(cases)
else:
    render_dashboard(cases)
