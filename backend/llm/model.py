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
You are a compliance-grade AI assistant helping draft a Suspicious Activity Report (SAR).

Rules:
- Use formal regulator-ready tone
- Do NOT make accusations
- Base reasoning strictly on provided data
- Be structured and concise

Output format:

SITUATION:
<describe what triggered the alert>

ASSESSMENT:
<analyze risk indicators>

RECOMMENDATION:
<justify SAR consideration>
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