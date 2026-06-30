from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class RedactionResult:
    text: str
    counts: dict[str, int]

    @property
    def total(self) -> int:
        return sum(self.counts.values())


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


def redact_text(text: str) -> RedactionResult:
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
