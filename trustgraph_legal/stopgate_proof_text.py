from __future__ import annotations

from typing import Final, Iterable, Tuple

NEGATED_PROOF_WORDS: Final[Tuple[str, ...]] = (
    "absent",
    "denied",
    "missing",
    "no",
    "not",
    "pending",
    "uncertain",
    "unproven",
    "without",
)


def has_positive_proof_text(value: str, tokens: Iterable[str]) -> bool:
    normalized = value.lower().replace("_", " ").replace("-", " ")
    words = frozenset(normalized.split())
    if words & frozenset(NEGATED_PROOF_WORDS):
        return False
    return bool(words & frozenset(token.lower() for token in tokens))
