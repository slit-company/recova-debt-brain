from __future__ import annotations

import re
from datetime import date
from typing import Final

EVALUATION_DATE: Final = date(2026, 7, 6)
UNKNOWN_DOCUMENT_TYPES: Final = frozenset({"", "unknown", "unclassified", "needs_review"})
APPROVED_LEGAL_STATUSES: Final = frozenset({"approved", "approved-static-v0", "approved_static_v0", "retrieved"})
REVIEW_LEGAL_MARKERS: Final = ("draft", "review", "deprecated", "future")
NATIONAL_ID_RE: Final = re.compile(r"\b\d{6}-\d{7}\b")
PHONE_RE: Final = re.compile(r"\b(?:\+82[-.\s]?)?0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}\b")
ACCOUNT_RE: Final = re.compile(r"(?i)\b(?:account|bank|계좌|은행|입금|송금)[^\n\r]{0,24}?\d{2,6}[-.\s]\d{2,6}[-.\s]\d{2,8}\b")
ADDRESS_HINT_RE: Final = re.compile(r"[가-힣]{2,}(?:시|도)\s+[가-힣0-9\s.-]{2,}(?:로|길)\s*\d+(?:-\d+)?")


def safe_text(value: str) -> str:
    redacted = NATIONAL_ID_RE.sub("[NATIONAL_ID_REDACTED]", value)
    redacted = PHONE_RE.sub("[PHONE_REDACTED]", redacted)
    redacted = ACCOUNT_RE.sub("[ACCOUNT_REDACTED]", redacted)
    return ADDRESS_HINT_RE.sub("[ADDRESS_REDACTED]", redacted)


def missing_text(value: str) -> bool:
    return not value.strip() or value.strip().lower() in {"missing", "none", "null"}


def unknown_document_type(document_type: str) -> bool:
    return document_type.strip().lower().replace("-", "_") in UNKNOWN_DOCUMENT_TYPES


def legal_source_reason_codes(source_ref: str) -> tuple[str, ...]:
    attrs = dict(segment.split("=", 1) for segment in source_ref.split("|")[1:] if "=" in segment)
    retrieval_status = attrs.get("retrieval_status", "")
    if missing_text(retrieval_status) or retrieval_status.lower() in {"unretrieved", "missing"}:
        return ("legal_source_unretrieved",)
    reasons: list[str] = []
    if _status_requires_review(retrieval_status) or _status_requires_review(attrs.get("review_status", "")):
        reasons.append("legal_source_review_status")
    if _future_effective_date(attrs.get("effective_date", "")):
        reasons.append("legal_source_future_effective_date")
    return tuple(dict.fromkeys(reasons))


def _status_requires_review(status: str) -> bool:
    normalized = status.replace("_", "-").lower()
    return normalized not in APPROVED_LEGAL_STATUSES and any(marker in normalized for marker in REVIEW_LEGAL_MARKERS)


def _future_effective_date(value: str) -> bool:
    if missing_text(value):
        return False
    try:
        return date.fromisoformat(value) > EVALUATION_DATE
    except ValueError:
        return True
