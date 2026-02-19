# SAR AI Copilot

AI-Driven Suspicious Activity Report Automation Platform

## Overview

SAR AI Copilot is an AI-powered compliance assistant designed to streamline the Suspicious Activity Report (SAR) drafting process in Anti-Money Laundering (AML) operations. The platform automates SAR narrative generation while maintaining audit transparency and regulatory defensibility.

The system integrates case management, risk signal analysis, LLM-based drafting, explainability tracing, and PDF export within a governed workflow environment.

---

## Problem Statement

Financial institutions face increasing regulatory pressure to detect and report suspicious activities accurately and efficiently. SAR drafting remains largely manual, time-intensive, and inconsistent, leading to operational inefficiencies and compliance risk.

---

## Solution

SAR AI Copilot provides:

- Case Intake Dashboard
- Risk Breakdown Analysis
- AI-Generated SAR Drafts
- Explainability & Trace Capture
- PDF Export of Regulator-Ready SAR Reports
- Case Lifecycle Status Management

---

## System Architecture

Frontend (Streamlit UI)  
→ Backend Orchestration Layer (Python)  
→ Risk Signal Processing  
→ LLM Engine (Mistral via Ollama)  
→ Explainability Engine  
→ PDF Generation Module  
→ Audit & Governance Layer

---

## Tech Stack

- Python
- Streamlit
- Mistral (via Ollama)
- ReportLab (PDF generation)
- Git

---

## Key Features

- Automated SAR narrative generation
- Structured risk signal preprocessing
- Human-in-the-loop workflow
- Audit-ready explainability trace
- Secure local LLM deployment option

---

## Future Scope

- Integration with core banking systems
- Real-time alert ingestion
- Multi-model risk scoring
- Continuous feedback learning loop
- Multi-jurisdiction SAR templates

---

## How to Run

1. Clone the repository: git clone
2. Install dependencies: pip install -r requirements.txt
3. Run the application: streamlit run frontend/app.py

---

## Team

Team Name: FinNova  
Campus: SRMKTR  
Hack-O-Hire 2026
