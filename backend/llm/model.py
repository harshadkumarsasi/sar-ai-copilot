"""
LLM interface for SAR AI Copilot.

Responsibilities:
- Initialize the language model
- Enforce system-level SAR instructions
- Generate structured SAR narratives (Situation, Assessment, Recommendation)

This file is model-agnostic and can switch between providers later.
"""

from typing import Dict, Any
from dataclasses import dataclass

from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.chat_models import ChatOpenAI


@dataclass
class SARInput:
    customer_profile: Dict[str, Any]
    transaction_summary: Dict[str, Any]
    alert_reason: str


class SARLLM:
    def __init__(self, temperature: float = 0.2):
        """
        Initialize the LLM.
        Low temperature is intentional for compliance-style writing.
        """
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=temperature,
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
You are a compliance-grade AI assistant helping a bank analyst draft a Suspicious Activity Report (SAR).

Rules you MUST follow:
- Write in formal, regulator-ready language
- Do NOT make accusations; describe observations objectively
- Base reasoning strictly on provided data
- Be concise, structured, and explainable

Output format MUST be:

SITUATION:
<what triggered the alert>

ASSESSMENT:
<analysis of transactions and risk indicators>

RECOMMENDATION:
<why this activity merits SAR consideration>
                    """,
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
                    """,
                ),
            ]
        )

        self.chain = self.prompt | self.llm | StrOutputParser()

    def generate_sar(self, sar_input: SARInput) -> str:
        """
        Generate a SAR narrative draft.
        """
        return self.chain.invoke(
            {
                "customer_profile": sar_input.customer_profile,
                "transaction_summary": sar_input.transaction_summary,
                "alert_reason": sar_input.alert_reason,
            }
        )
