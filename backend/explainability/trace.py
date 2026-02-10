

"""
Explainability and reasoning trace module for SAR AI Copilot.

Responsibilities:
- Capture AI decision context
- Log reasoning traces for auditability
- Provide human-readable explanations for regulators and analysts

This module bridges AI output with compliance expectations.
"""

from typing import Dict, Any, List
from datetime import datetime
import uuid


class ReasoningTrace:
    """
    Represents a single explainability trace for a SAR case.
    """

    def __init__(
        self,
        case_id: int,
        model_name: str,
        input_signals: Dict[str, Any],
        retrieved_context: str,
    ):
        self.trace_id = str(uuid.uuid4())
        self.case_id = case_id
        self.model_name = model_name
        self.input_signals = input_signals
        self.retrieved_context = retrieved_context
        self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert trace to a serializable dictionary.
        """
        return {
            "trace_id": self.trace_id,
            "case_id": self.case_id,
            "model_name": self.model_name,
            "input_signals": self.input_signals,
            "retrieved_context": self.retrieved_context,
            "created_at": self.created_at.isoformat(),
        }


class ExplainabilityEngine:
    """
    Central explainability engine for SAR AI Copilot.
    """

    def __init__(self):
        self.traces: List[ReasoningTrace] = []

    def capture_trace(
        self,
        case_id: int,
        model_name: str,
        input_signals: Dict[str, Any],
        retrieved_context: str,
    ) -> ReasoningTrace:
        """
        Capture and store a reasoning trace.
        """
        trace = ReasoningTrace(
            case_id=case_id,
            model_name=model_name,
            input_signals=input_signals,
            retrieved_context=retrieved_context,
        )
        self.traces.append(trace)
        return trace

    def get_traces_for_case(self, case_id: int) -> List[Dict[str, Any]]:
        """
        Retrieve all traces associated with a SAR case.
        """
        return [
            trace.to_dict()
            for trace in self.traces
            if trace.case_id == case_id
        ]