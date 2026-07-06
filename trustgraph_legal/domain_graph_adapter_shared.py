from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass

from trustgraph_legal.debtor_context_types import (
    DebtorGraphPayload,
    JsonObject,
    JsonValue,
    PLACEHOLDER_SOURCE_REFS,
)

GraphInput = DebtorGraphPayload | JsonObject


@dataclass(frozen=True, slots=True)
class DomainGraphAdapterError(Exception):
    location: str
    reason_code: str
    detail: str


def graph_json(graph: GraphInput) -> JsonObject:
    if isinstance(graph, DebtorGraphPayload):
        return graph.to_json()
    return graph


def json_object(value: JsonValue) -> JsonObject:
    return value if isinstance(value, dict) else {}


def json_objects(value: JsonValue) -> tuple[JsonObject, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, dict))


def strings(value: JsonValue) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str) and item)


def required_text(entry: JsonObject, field: str, location: str) -> str:
    value = text(entry.get(field))
    if value:
        return value
    raise DomainGraphAdapterError(location, "missing_{}".format(field), "{} is required".format(field))


def text(value: JsonValue) -> str:
    return value if isinstance(value, str) else ""


def int_value(value: JsonValue) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def number_value(value: JsonValue) -> JsonValue:
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def source_refs(fact: JsonObject) -> tuple[str, ...]:
    refs = strings(fact.get("source_refs"))
    if refs:
        return refs
    source_ref = text(fact.get("source_ref"))
    return (source_ref,) if source_ref else ()


def required_source_refs(fact: JsonObject, location: str) -> tuple[str, ...]:
    refs = source_refs(fact)
    if not refs:
        raise DomainGraphAdapterError(location, "missing_source_ref", "fact source_refs are required")
    for source_ref in refs:
        if placeholder_source_ref(source_ref):
            raise DomainGraphAdapterError(location, "placeholder_source_ref", "fact source_ref is a placeholder")
    return refs


def placeholder_source_ref(source_ref: str) -> bool:
    normalized = source_ref.strip().lower()
    return (
        normalized in PLACEHOLDER_SOURCE_REFS
        or normalized.startswith("placeholder:")
        or normalized.startswith("todo:")
        or normalized.startswith("[")
    )


def unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def digest(text_value: str) -> str:
    return hashlib.sha256(text_value.encode("utf-8")).hexdigest()[:16]


def pii_profile() -> JsonObject:
    return {"raw_text_included": False, "source_text_included": False}
