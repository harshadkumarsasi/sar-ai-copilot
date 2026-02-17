from dataclasses import dataclass
from typing import Dict, Any

from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


@dataclass
class SARInput:
    customer_profile: Dict[str, Any]
    transaction_summary: Dict[str, Any]
    alert_reason: str


class SARLLM:
    def __init__(self):
        # Local Ollama model (must be running via `ollama serve`)
        self.llm = ChatOllama(
            model="mistral",  # change to "llama3" if you downloaded that instead
            temperature=0.2
        )

        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
You are a senior AML compliance analyst drafting a professional Suspicious Activity Report (SAR) for regulatory submission.

You must produce a detailed, regulator-ready report suitable for bank compliance teams.

Rules:
- Use formal, objective language
- Do NOT make direct accusations
- Base reasoning strictly on provided data
- Expand analysis clearly and professionally
- Each section must contain multiple detailed paragraphs

The report must include:

1. SITUATION
   - Describe triggering events
   - Include transaction timing and pattern observations
   - Mention risk score

2. CUSTOMER PROFILE ANALYSIS
   - Compare observed behavior with expected behavior
   - Discuss declared income/turnover mismatch if applicable

3. TRANSACTION ANALYSIS
   - Describe frequency, velocity, and beneficiary patterns
   - Identify suspicious structuring if present

4. RED FLAGS IDENTIFIED
   - Bullet list of risk indicators

5. ASSESSMENT
   - Explain why the activity is inconsistent or high-risk
   - Reference AML typologies (layering, structuring, etc.)

6. RECOMMENDATION
   - Justify SAR filing
   - Suggest enhanced monitoring or escalation

Write a comprehensive, professional-grade report.
"""
            ),
            (
                "human",
                """
Customer Profile:
{customer_profile}

Transaction Summary:
{transaction_summary}

Alert Reason:
{alert_reason}
"""
            )
        ])

        self.chain = self.prompt | self.llm | StrOutputParser()

    def generate_sar(self, sar_input: SARInput) -> str:
        return self.chain.invoke({
            "customer_profile": sar_input.customer_profile,
            "transaction_summary": sar_input.transaction_summary,
            "alert_reason": sar_input.alert_reason
        })