from __future__ import annotations

import hashlib
import re
from typing import TypeAlias

from .domain_manual_inventory_terms import (
    ACTION_PACKET_TERMS,
    ARTICLE_RE,
    LAW_NAMES,
    SENSITIVE_PATTERNS,
)

JsonScalar: TypeAlias = None | bool | int | float | str
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]


def route_family_for(title: str) -> str:
    if any(term in title for term in ("은행", "예금", "금융", "증권", "가상자산")):
        return "financial_asset"
    if any(term in title for term in ("급여", "퇴직", "소득", "용역대금")):
        return "income"
    if any(term in title for term in ("부동산", "임대차", "보증금", "전세권")):
        return "real_estate_or_housing"
    if any(term in title for term in ("회생", "파산", "면책")):
        return "insolvency_review"
    if any(term in title for term in ("지급명령", "소송", "공정증서", "조정", "화해")):
        return "title_acquisition"
    return "collection_route"


def collect_term_candidates(term_map: dict[str, tuple[str, ...]], text: str, prefix: str) -> list[JsonObject]:
    candidates: list[JsonObject] = []
    for candidate_id, terms in term_map.items():
        hit_count = sum(text.count(term) for term in terms)
        if hit_count < 1:
            continue
        candidates.append(
            {
                "candidate_id": f"{prefix}:{candidate_id}",
                "name": candidate_id,
                "signal_count": hit_count,
            },
        )
    return candidates


def collect_legal_sources(text: str) -> list[JsonObject]:
    article_refs = sorted({normalize_article_ref(match.group(0)) for match in ARTICLE_RE.finditer(text)})
    candidates: list[JsonObject] = []
    for law_name in LAW_NAMES:
        hit_count = text.count(law_name)
        if hit_count < 1:
            continue
        article_values: list[JsonValue] = [article_ref for article_ref in article_refs[:20]]
        candidates.append(
            {
                "candidate_id": f"legal-source:{hashlib.sha1(law_name.encode('utf-8')).hexdigest()[:10]}",
                "law_name": law_name,
                "article_refs": article_values,
                "signal_count": hit_count,
                "review_status": "candidate_requires_legal_review",
            },
        )
    return candidates


def collect_action_packets(text: str) -> list[JsonObject]:
    packets = collect_term_candidates(ACTION_PACKET_TERMS, text, "action-packet")
    return [
        {
            **packet,
            "status": "draft_only",
            "human_review_required": True,
            "execution_forbidden": True,
        }
        for packet in packets
    ]


def count_sensitive_patterns(text: str) -> JsonObject:
    return {label: len(pattern.findall(text)) for label, pattern in SENSITIVE_PATTERNS.items()}


def normalize_article_ref(raw: str) -> str:
    return re.sub(r"\s+", "", raw)
