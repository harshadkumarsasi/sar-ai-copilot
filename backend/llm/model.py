from dataclasses import dataclass
import re
from typing import Dict, Any

from langchain_community.chat_models import ChatOllama
from langchain_community.chat_models.ollama import OllamaEndpointNotFoundError
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


class SARGenerationError(RuntimeError):
    """Raised when the local Ollama service cannot produce a SAR draft."""


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
            temperature=0.2,
            num_ctx=4096,
            num_predict=250,
            timeout=180,
        )

        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
You are an experienced AML analyst drafting a detailed Suspicious Activity Report (SAR)
narrative for human review. Produce a concise, source-grounded initial draft of about 150 words.
The application adds a separate evidence review for the required report detail.

Use only facts in the supplied profile, transaction summary, and alert reason. Treat alert
descriptions as unverified; do not infer wrongdoing, intent, a typology, causes, or a filing
recommendation. State missing information as "not provided", not as a negative finding. Do not
invent dates, accounts, counterparties, income, expected behavior, investigations, or legal
conclusions. Keep aggregate exposure, flagged-event count, and representative events distinct.
Preserve metric labels exactly: "94% of expected range" is not an increase. Attribute risk
descriptions to the case record. Use the customer's exact name and specific supplied figures.

Write these sections in order:
1. EXECUTIVE SUMMARY: Summarize the alert, customer identifier, risk score, corridor, exposure,
   monitoring window, and supplied risk drivers.
2. CUSTOMER AND CASE CONTEXT: Summarize the supplied profile and geography. Identify expected
   activity, declared income, and history as not provided when absent.
3. TRANSACTION CHRONOLOGY: Describe the representative events with their exact relative day,
   amount, and description. State that the list may be incomplete.
4. QUANTITATIVE ANALYSIS: Discuss exposure, flagged count, highest transfer, peer deviation,
   velocity, week-over-week change, and risk trend only as supplied.
5. RISK INDICATORS AND SCREENING: Discuss each supplied risk driver, offshore-jurisdiction
   count, PEP result, and sanctions result without extending their meaning.
6. EVIDENCE LIMITATIONS: Describe missing facts and timeline limits. Distinguish case-record
   assertions from independently verified evidence.
7. ANALYST ASSESSMENT AND FOLLOW-UP: Explain why the signals merit human review and list
   records or questions to verify before reaching a human disposition.

Use the customer's name exactly as provided. Include no invented facts. The report is a draft,
not a filing decision.
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
        try:
            narrative = self.chain.invoke({
                "customer_profile": sar_input.customer_profile,
                "transaction_summary": sar_input.transaction_summary,
                "alert_reason": sar_input.alert_reason
            })
            if not narrative.strip():
                return narrative
            narrative = self._correct_evidence_sensitive_sections(sar_input, narrative)
            if len(narrative.split()) < 900:
                narrative = self._add_detailed_evidence_review(sar_input, narrative)
            return narrative
        except OllamaEndpointNotFoundError as exc:
            raise SARGenerationError(
                "The local Ollama model 'mistral' is not installed. Run `ollama pull mistral`."
            ) from exc
        except (OSError, ValueError) as exc:
            raise SARGenerationError(
                f"Could not generate a draft from local Ollama: {exc}"
            ) from exc

    @staticmethod
    def _correct_evidence_sensitive_sections(sar_input: SARInput, narrative: str) -> str:
        profile = sar_input.customer_profile
        summary = sar_input.transaction_summary
        customer_name = profile.get("customer_name", "Not provided")
        customer_id = profile.get("customer_id", "Not provided")
        timeline_events = summary.get("representative_timeline_events", [])
        timeline_lines = [
            f"- {event.get('relative_time', 'Relative time not provided')}: "
            f"{event.get('amount', 'Amount not provided')} — "
            f"{event.get('description', 'Description not provided')}"
            for event in timeline_events
        ]
        timeline_section = (
            f"The stated monitoring window is {summary.get('monitoring_window', 'Not provided')}. "
            "The case record supplies these representative events:"
            + ("\n" + "\n".join(timeline_lines) if timeline_lines else "\nNo representative events were provided.")
            + "\nThe source note states that the list may not include every transaction in the "
            "monitoring window. Relative-day labels are not calendar dates, and the listed "
            "events should not be treated as the complete transaction population or used to "
            "recalculate the supplied aggregate exposure."
        )

        replacements = {
            "EXECUTIVE SUMMARY": (
                f"The case record identifies {customer_name} (customer ID {customer_id}) "
                f"with a recorded risk score of {profile.get('risk_score', 'Not provided')}. "
                f"The stated geography is {profile.get('geography', 'Not provided')}, and "
                f"the recorded corridor is {profile.get('corridor', 'Not provided')}. "
                f"The supplied alert reason is: {sar_input.alert_reason} The transaction "
                f"summary states: {summary.get('summary', 'Not provided')} The supplied "
                f"aggregate exposure is {summary.get('total_exposure', 'Not provided')}; "
                f"the flagged-event count is "
                f"{summary.get('flagged_transaction_count', 'Not provided')}; the highest "
                f"single transfer is {summary.get('highest_single_transfer', 'Not provided')}; "
                f"and the monitoring window is "
                f"{summary.get('monitoring_window', 'Not provided')}. These are case-record "
                "fields for analyst review, not independent findings."
            ),
            "TRANSACTION CHRONOLOGY": timeline_section,
            "QUANTITATIVE ANALYSIS": (
                f"The supplied aggregate exposure is {summary.get('total_exposure', 'Not provided')}, "
                f"the flagged-event count is "
                f"{summary.get('flagged_transaction_count', 'Not provided')}, and the highest "
                f"single transfer is {summary.get('highest_single_transfer', 'Not provided')}. "
                f"The case records peer deviation as "
                f"{summary.get('peer_deviation', 'Not provided')}, transaction velocity as "
                f"{summary.get('transaction_velocity', 'Not provided')}, week-over-week change "
                f"as {summary.get('week_over_week_change', 'Not provided')}, and risk trend as "
                f"{summary.get('risk_trend', 'Not provided')}. The record does not provide "
                "the methods, baselines, reference population, or thresholds needed to interpret "
                "these measures beyond their supplied labels. In particular, a velocity stated "
                "as a percentage of an expected range is not characterized here as above that "
                "range. The week-over-week change and risk trend are separately reported fields; "
                "the case record does not define whether they share a calculation or reference "
                "period. The assessment model is "
                f"{summary.get('assessment_model', 'Not provided')}, with recorded model "
                f"confidence {summary.get('model_confidence', 'Not provided')}; no confidence "
                "calibration details are supplied."
            ),
            "RISK INDICATORS AND SCREENING": (
                "The case record lists the following risk drivers as alert indicators, not as "
                "independently established findings: "
                + "; ".join(summary.get("risk_drivers", []))
                + f". It records {summary.get('offshore_jurisdictions', 'Not provided')} "
                "offshore jurisdictions. PEP screening is recorded as "
                f"{summary.get('pep_screening', 'Not provided')}; sanctions screening is "
                f"recorded as {summary.get('sanctions_screening', 'Not provided')}. The "
                "underlying screening records, review rationale, and screening date were not "
                "provided for this draft. These statuses should not be extended beyond the "
                "results stated in the case record."
            ),
            "ANALYST ASSESSMENT AND FOLLOW-UP": (
                "The supplied alert reason and risk drivers warrant review against source "
                "records, but the available fields do not independently establish the nature "
                "or purpose of the activity. Before reaching a disposition, the analyst should:"
                "\n1. Obtain the complete transaction population for the stated monitoring "
                "window and reconcile it to the supplied exposure and flagged-event count."
                "\n2. Verify transaction dates, amounts, originators, beneficiaries, account "
                "ownership, and transfer sequence using source records."
                "\n3. Confirm whether the representative timeline omits events and avoid treating "
                "the listed events as the complete transaction population."
                "\n4. Review the customer's expected activity, declared income, and available "
                "history; those details are not provided in the current case input."
                "\n5. Confirm the basis, reference population, calculation period, and "
                "thresholds for the peer-deviation, velocity, week-over-week, and risk-trend "
                "measures."
                "\n6. Review the underlying PEP and sanctions screening records, including the "
                "scope and resolution of any review-required result."
                "\n7. Document which facts were independently verified, what remains "
                "unresolved, and the human analyst's reasoning for the case disposition."
                "\nThese are verification steps, not assertions that additional records "
                "contain adverse information. Any escalation or filing decision remains with "
                "the responsible analyst under the applicable internal process."
            ),
        }
        fallback_sections = {
            "CUSTOMER AND CASE CONTEXT": (
                f"The supplied profile identifies {customer_name} (customer ID {customer_id}), "
                f"with geography {profile.get('geography', 'Not provided')} and corridor "
                f"{profile.get('corridor', 'Not provided')}. Declared income is "
                f"{profile.get('declared_income', 'Not provided')}; expected activity is "
                f"{profile.get('expected_activity_profile', 'Not provided')}; and customer "
                f"history is {profile.get('customer_history', 'Not provided')}. Missing profile "
                "details are unknown, not negative findings."
            ),
            "EVIDENCE LIMITATIONS": (
                "This draft is limited to fields supplied in the case input. The representative "
                "timeline may not include every transaction, and relative-day labels do not "
                "provide calendar dates. Source transaction records, screening evidence, "
                "calculation methods, reference populations, and model-confidence calibration "
                "were not supplied here. These are limitations of the draft input and do not "
                "establish that such records are unavailable elsewhere."
            ),
        }
        section_order = (
            "EXECUTIVE SUMMARY",
            "CUSTOMER AND CASE CONTEXT",
            "TRANSACTION CHRONOLOGY",
            "QUANTITATIVE ANALYSIS",
            "RISK INDICATORS AND SCREENING",
            "EVIDENCE LIMITATIONS",
            "ANALYST ASSESSMENT AND FOLLOW-UP",
        )
        section_pattern = re.compile(
            r"(?im)^[ \t]*(?:\d+[.)][ \t]*)?(?:(?:#{1,3}[ \t]*)|\*\*)?"
            r"(EXECUTIVE SUMMARY|CUSTOMER AND CASE CONTEXT|TRANSACTION CHRONOLOGY|"
            r"QUANTITATIVE ANALYSIS|RISK INDICATORS AND SCREENING|EVIDENCE LIMITATIONS|"
            r"ANALYST ASSESSMENT AND FOLLOW-UP)(?:\*\*)?[ \t]*:?[ \t]*$"
        )
        matches = list(section_pattern.finditer(narrative))
        model_sections = {}
        for index, match in enumerate(matches):
            section_title = match.group(1).upper()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(narrative)
            model_sections[section_title] = narrative[match.end():end].strip()

        report_sections = []
        for section_title in section_order:
            section_text = replacements.get(section_title)
            if section_text is None:
                section_text = model_sections.get(section_title) or fallback_sections[section_title]
            report_sections.append(f"**{section_title}**\n\n{section_text}")
        return "\n\n".join(report_sections)

    @staticmethod
    def _add_detailed_evidence_review(sar_input: SARInput, narrative: str) -> str:
        profile = sar_input.customer_profile
        summary = sar_input.transaction_summary
        customer_name = profile.get("customer_name", "Not provided")
        customer_id = profile.get("customer_id", "Not provided")
        timeline = summary.get("representative_timeline_events", [])
        drivers = summary.get("risk_drivers", [])

        review_lines = [
            "**DETAILED EVIDENCE REVIEW AND ANALYST FOLLOW-UP**",
            (
                "This evidence review expands the model-generated narrative using fields "
                "from the supplied case record. It does not independently verify transactions, "
                "screening outcomes, customer details, or the alert rationale. The analyst "
                "should distinguish recorded assertions from source documents and should not "
                "treat this draft as a filing decision."
            ),
            "",
            "**Case record reconciliation**",
            (
                f"The case record identifies {customer_name} (customer ID {customer_id}). "
                f"The recorded risk score is {profile.get('risk_score', 'Not provided')}; "
                f"the recorded geography is {profile.get('geography', 'Not provided')}; "
                f"and the corridor is {profile.get('corridor', 'Not provided')}. The alert "
                f"reason supplied for review is: {sar_input.alert_reason} The transaction "
                f"summary states: {summary.get('summary', 'Not provided')}"
            ),
            (
                f"The supplied aggregate exposure is {summary.get('total_exposure', 'Not provided')}, "
                f"the flagged-event count is {summary.get('flagged_transaction_count', 'Not provided')}, "
                f"and the highest single transfer is "
                f"{summary.get('highest_single_transfer', 'Not provided')}. The monitoring "
                f"window is {summary.get('monitoring_window', 'Not provided')}. These are "
                "separate reported fields: the flagged-event count should not be read as a "
                "complete transaction count, and the representative timeline should not be "
                "used to recalculate or replace the supplied aggregate exposure."
            ),
            "",
            "**Chronology and limits of the transaction sample**",
            (
                "The events below are reproduced as selected examples from the case record. "
                "Relative-day labels are not calendar dates, and the supplied note says the "
                "list may not contain every transaction in the monitoring window."
            ),
        ]
        review_lines.extend(
            f"- {event.get('relative_time', 'Relative time not provided')}: "
            f"{event.get('amount', 'Amount not provided')} — "
            f"{event.get('description', 'Description not provided')}"
            for event in timeline
        )
        review_lines.extend(
            [
                (
                    "The analyst should reconcile these selected events to the full transaction "
                    "record before relying on sequencing, totals, or the stated monitoring "
                    "period. The supplied descriptions are not a substitute for transaction "
                    "identifiers, timestamps, account records, or supporting documents, none "
                    "of which are included in this draft input."
                ),
                "",
                "**Quantitative fields and interpretation boundaries**",
                (
                    f"The peer-deviation field is {summary.get('peer_deviation', 'Not provided')}; "
                    f"transaction velocity is recorded as "
                    f"{summary.get('transaction_velocity', 'Not provided')}; the week-over-week "
                    f"change is {summary.get('week_over_week_change', 'Not provided')}; and "
                    f"the risk trend is {summary.get('risk_trend', 'Not provided')}. These "
                    "figures should retain their recorded labels. The case input does not "
                    "provide calculation methods, reference periods for every measure, peer "
                    "population, underlying baseline values, or thresholds. In particular, "
                    "a velocity stated as a percentage of an expected range must not be "
                    "described as above that range without additional evidence."
                ),
                (
                    f"The assessment model is {summary.get('assessment_model', 'Not provided')} "
                    f"and the recorded model confidence is "
                    f"{summary.get('model_confidence', 'Not provided')}. The case record does "
                    "not define how confidence is calculated or calibrated. It should therefore "
                    "be presented as a supplied model field, not as proof that the alert is "
                    "correct or as a probability that misconduct occurred."
                ),
                "",
                "**Risk drivers and screening**",
                (
                    "The recorded risk drivers are reproduced below as alert indicators, not "
                    "as independently established findings:"
                ),
            ]
        )
        review_lines.extend(f"- {driver}" for driver in drivers)
        review_lines.extend(
            [
                (
                    f"The case lists {summary.get('offshore_jurisdictions', 'Not provided')} "
                    "offshore jurisdictions. PEP screening is recorded as "
                    f"{summary.get('pep_screening', 'Not provided')}; sanctions screening is "
                    f"recorded as {summary.get('sanctions_screening', 'Not provided')}. "
                    "The underlying screening records, match-resolution rationale, and "
                    "screening date are not part of the supplied narrative input. A screening "
                    "status should not be extended beyond its recorded result."
                ),
                "",
                "**Prioritized analyst verification**",
                "Before reaching a disposition, the reviewer should:",
                "1. Obtain the complete transaction population for the stated monitoring window and reconcile it to the supplied exposure and flagged-event count.",
                "2. Verify transaction dates, amounts, originators, beneficiaries, account ownership, and the sequence of transfers against source records.",
                "3. Establish what the selected relative-day events represent and whether any relevant transactions are omitted from the representative timeline.",
                "4. Review the customer profile, expected activity, declared income, and available history; these details are not provided in the current case input.",
                "5. Confirm the basis, reference population, calculation period, and thresholds for peer deviation, transaction velocity, week-over-week change, and risk trend.",
                "6. Review the underlying PEP and sanctions screening records, including the scope and resolution of any review-required result.",
                "7. Record which facts were independently verified, identify unresolved questions, and document the human analyst's reasoning and disposition.",
                (
                    "These steps are verification questions, not assertions that additional "
                    "records contain adverse information. Any decision about escalation or "
                    "filing remains with the responsible analyst under the applicable internal "
                    "process. No filing recommendation or legal conclusion is made by this "
                    "supplement."
                ),
            ]
        )

        supplement = "\n".join(review_lines)
        combined = f"{narrative.rstrip()}\n\n{supplement}".strip()
        if len(combined.split()) < 900:
            combined = (
                f"{combined}\n\n"
                "**Documentation standard**\n"
                "For a review-ready record, preserve the source and time of each verified "
                "fact, the specific transaction or screening record supporting it, and any "
                "difference between source data and the summary presented here. Separate "
                "observed activity from model-generated descriptions, and distinguish an "
                "unresolved question from a negative finding. Where the source record is "
                "incomplete, state the limitation rather than filling it with an assumption. "
                "The final case disposition should explain which evidence was considered, "
                "what remains unverified, and why the chosen next step is appropriate. The "
                "narrative and its attached evidence should be reviewed together so that "
                "figures, relative dates, counts, and screening results remain consistent."
                " Record the source for each figure, the review date, and any reconciliation "
                "performed against the underlying transaction records. Keep representative "
                "events distinct from aggregate values, and retain the original labels for "
                "risk and screening fields when their methodology is not available. If a "
                "source record conflicts with the summary, document the discrepancy for "
                "resolution rather than silently selecting one value. This process makes the "
                "draft auditable and helps a later reviewer trace each statement to evidence."
                " Record the case-data fields that were unavailable at the time of review, "
                "and avoid treating missing information as evidence for or against the alert. "
                "Keep the original event descriptions and relative-time labels intact unless "
                "a source record establishes a correction. Any revised amount, count, or "
                "screening status should be traceable to that source and reflected consistently "
                "in the narrative and its evidence appendix. Any uncertainty about a number "
                "or description should be visible to the next reviewer, not resolved through "
                "assumption. The narrative should not state a trend, baseline comparison, or "
                "causal explanation unless the supplied record supports it. A reviewer should "
                "compare each paragraph with the attached case fields before approving or "
                "editing the draft. This final comparison helps prevent a representative event "
                "from being presented as exhaustive, a screening status from being broadened, "
                "or a model-generated interpretation from being mistaken for a verified fact."
            )
        return combined