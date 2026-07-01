from __future__ import annotations

import re
from enum import Enum
from typing import Final, List, Tuple

from trustgraph_legal.classifier_types import (
    FIXTURE_BUCKET_TO_DOCUMENT_TYPE,
    MIN_CLASSIFICATION_SCORE,
    UNKNOWN_CONFIDENCE_CEILING,
    CanonicalDocumentType,
    ClassificationResult,
    EvidenceSpan,
    FixtureBucket,
    RedactionResult,
    ReviewStatus,
    RuleMatch,
    RuleSpec,
)

_NATIONAL_ID: Final = re.compile(r"\b\d{6}-\d{7}\b")
_PHONE: Final = re.compile(
    r"\b(?:\+82[-.\s]?)?0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}\b"
)
_ACCOUNT: Final = re.compile(
    r"(?i)\b(?:account|bank|계좌|은행|입금|송금)[^\n\r]{0,24}?"
    r"\d{2,6}[-.\s]\d{2,6}[-.\s]\d{2,8}\b"
)
_ADDRESS_HINT: Final = re.compile(
    r"[가-힣]{2,}(?:시|도)\s+[가-힣0-9\s.-]{2,}(?:로|길)\s*\d+(?:-\d+)?"
)

RULES: Final[Tuple[RuleSpec, ...]] = (
    (
        FixtureBucket.ATTACHMENT_COLLECTION_ORDER,
        (
            ("채권압류 및 추심명령", "attachment_collection_order_marker", 4.0),
            ("Third-party debtor", "third_party_debtor_present", 2.0),
            ("The court orders attachment", "court_attachment_order_language", 2.0),
            ("may collect from the third-party debtor", "collection_authority_language", 1.5),
            ("Attachment target", "attachment_target_present", 1.0),
        ),
    ),
    (
        FixtureBucket.JUDGMENT_PAYMENT_ORDER,
        (
            ("지급명령 / 판결 정본", "judgment_payment_order_marker", 4.0),
            ("Delayed damages", "delayed_damages_present", 1.5),
            ("Decision summary", "decision_summary_present", 1.5),
            ("principal, accrued interest", "title_amount_language", 1.5),
            ("Objection and appeal status", "appeal_status_language", 1.0),
        ),
    ),
    (
        FixtureBucket.SERVICE_FINALITY_EXECUTION_CLAUSE,
        (
            ("송달증명 / 확정증명 / 집행문", "service_finality_execution_marker", 4.0),
            ("Service result", "service_result_present", 1.5),
            ("Finality result", "finality_result_present", 1.5),
            ("Execution clause", "execution_clause_present", 1.5),
            ("execution authority", "execution_authority_language", 1.0),
        ),
    ),
    (
        FixtureBucket.ASSIGNMENT_SUCCESSION,
        (
            ("채권양도 통지 / 승계집행문", "assignment_succession_marker", 4.0),
            ("Assignor", "assignor_present", 1.5),
            ("Assignee", "assignee_present", 1.5),
            ("Notice status", "notice_status_present", 1.5),
            ("Succession authority", "succession_authority_present", 1.5),
        ),
    ),
    (
        FixtureBucket.IDENTITY_EVIDENCE,
        (
            ("신원 확인 자료 / 법인등기 요약", "identity_evidence_marker", 4.0),
            ("Identity key evidence", "identity_key_evidence_present", 2.0),
            ("normalized name token", "name_token_present", 1.0),
            ("registration status", "registry_status_present", 1.0),
            ("representative role", "representative_role_present", 1.0),
        ),
    ),
    (
        FixtureBucket.INSOLVENCY_CREDIT_RECOVERY,
        (
            ("파산 / 면책 / 신용회복", "insolvency_credit_recovery_marker", 4.0),
            ("personal rehabilitation", "rehabilitation_present", 1.5),
            ("Procedure state", "procedure_state_present", 1.5),
            ("Discharge, rehabilitation", "discharge_rehabilitation_language", 1.5),
            ("Debt collection action must pause", "collection_pause_language", 1.0),
        ),
    ),
    (
        FixtureBucket.ASSET_EVIDENCE,
        (
            ("자산 증빙 / 압류대상 후보", "asset_evidence_marker", 4.0),
            ("Asset type", "asset_type_present", 1.5),
            ("Priority note", "priority_note_present", 1.5),
            ("Attachment suitability", "attachment_suitability_present", 1.5),
            ("Asset evidence suggests", "asset_evidence_language", 1.0),
        ),
    ),
    (
        FixtureBucket.OPERATIONAL_LEDGER,
        (
            ("채권보전 및 회수현황", "operational_ledger_marker", 4.0),
            ("Ledger rows", "ledger_rows_present", 2.0),
            ("partial recovery", "partial_recovery_present", 1.5),
            ("filing cost", "filing_cost_present", 1.0),
            ("operational facts", "operational_fact_language", 1.0),
        ),
    ),
    (
        FixtureBucket.AMOUNT_INTEREST,
        (
            ("원리금 계산서 / 지연손해금 산정", "amount_interest_marker", 4.0),
            ("Interest basis", "interest_basis_present", 1.5),
            ("Calculation start", "calculation_period_present", 1.5),
            ("Claimed total", "claimed_total_present", 1.5),
            ("principal, interest basis", "amount_interest_language", 1.0),
        ),
    ),
)


def classify_text(document_id: str, source_ref: str, text: str) -> ClassificationResult:
    redaction = _redact_text(text)
    best_match = max((_match_rule(rule, source_ref, text) for rule in RULES), key=_rank)
    if best_match.score < MIN_CLASSIFICATION_SCORE:
        preview = _unknown_span(source_ref, redaction.text)
        return ClassificationResult(
            document_id=document_id,
            document_type=CanonicalDocumentType.UNKNOWN,
            fixture_document_type=FixtureBucket.UNKNOWN_DOC_TYPE,
            confidence=round(min(best_match.score / 10, UNKNOWN_CONFIDENCE_CEILING), 2),
            review_status=ReviewStatus.NEEDS_REVIEW_UNKNOWN_DOC_TYPE,
            evidence_spans=(preview,),
            reason_signals=("insufficient_document_type_signals",),
            pii_counts=redaction.counts,
        )
    return ClassificationResult(
        document_id=document_id,
        document_type=FIXTURE_BUCKET_TO_DOCUMENT_TYPE[best_match.fixture_bucket],
        fixture_document_type=best_match.fixture_bucket,
        confidence=_confidence(best_match.score),
        review_status=ReviewStatus.CLASSIFIED,
        evidence_spans=best_match.evidence_spans,
        reason_signals=best_match.reason_signals,
        pii_counts=redaction.counts,
    )


def _rank(rule_match: RuleMatch) -> Tuple[float, int]:
    return (rule_match.score, -list(FixtureBucket).index(rule_match.fixture_bucket))


def _match_rule(rule: RuleSpec, source_ref: str, text: str) -> RuleMatch:
    fixture_bucket, signal_specs = rule
    folded_text = text.casefold()
    spans: List[EvidenceSpan] = []
    signals: List[str] = []
    score = 0.0
    for needle, reason, weight in signal_specs:
        start = folded_text.find(needle.casefold())
        if start >= 0:
            end = start + len(needle)
            spans.append(
                EvidenceSpan(
                    source_ref=source_ref,
                    start=start,
                    end=end,
                    excerpt=_redacted_excerpt(text, start, end),
                    signal=reason,
                )
            )
            signals.append(reason)
            score += weight
    return RuleMatch(
        fixture_bucket=fixture_bucket,
        score=score,
        evidence_spans=tuple(spans),
        reason_signals=tuple(signals),
    )


def _confidence(score: float) -> float:
    return round(min(0.97, 0.62 + (score / 20)), 2)


def _unknown_span(source_ref: str, redacted_text: str) -> EvidenceSpan:
    end = min(len(redacted_text), 160)
    return EvidenceSpan(
        source_ref=source_ref,
        start=0,
        end=end,
        excerpt=redacted_text[:end],
        signal="low_signal_preview",
    )


def _redacted_excerpt(text: str, start: int, end: int) -> str:
    window_start = max(0, start - 80)
    window_end = min(len(text), end + 160)
    return _redact_text(text[window_start:window_end].strip()).text


def _redact_text(text: str) -> RedactionResult:
    redacted, national_count = _NATIONAL_ID.subn("[NATIONAL_ID_REDACTED]", text)
    redacted, phone_count = _PHONE.subn("[PHONE_REDACTED]", redacted)
    redacted, account_count = _ACCOUNT.subn("[ACCOUNT_REDACTED]", redacted)
    redacted, address_count = _ADDRESS_HINT.subn("[ADDRESS_REDACTED]", redacted)
    return RedactionResult(
        text=redacted,
        counts={
            "national_id": national_count,
            "phone": phone_count,
            "account": account_count,
            "address": address_count,
        },
    )
