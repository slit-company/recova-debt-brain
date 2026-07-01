from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, Final, List

from trustgraph_legal.governance_models import JsonValue
from trustgraph_legal.pii import redact_text

JsonObject = Dict[str, JsonValue]
SCHEMA_VERSION: Final = "trustgraph-legal-mcp-tool-response/v1"


@dataclass(frozen=True)
class EnvelopeRequest:
    tool_name: str
    group: str
    scope: str
    result: JsonValue
    warnings: List[str]
    source_refs: List[JsonValue]


def build_envelope(request: EnvelopeRequest) -> JsonObject:
    profile = pii_profile(request.result)
    return {
        "schema_version": SCHEMA_VERSION,
        "tool_name": request.tool_name,
        "group": request.group,
        "scope": request.scope,
        "pii_profile": profile,
        "redaction": {
            "status": "redacted",
            "default": "redacted",
            "raw_text_included": False,
            "source_text_included": False,
            "counts": profile.get("redacted", {}),
        },
        "source_refs": request.source_refs,
        "warnings": request.warnings,
        "result": request.result,
    }


def redact_json(value: JsonValue) -> JsonValue:
    if isinstance(value, str):
        return redact_text(value).text
    if isinstance(value, list):
        return [redact_json(item) for item in value]
    if isinstance(value, dict):
        return {key: redact_json(item) for key, item in value.items()}
    return value


def pii_profile(value: JsonValue) -> JsonObject:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True)
    redaction = redact_text(encoded)
    return {"raw_text_included": False, "source_text_included": False, "redacted": redaction.counts}


def source_refs(value: JsonValue) -> List[JsonValue]:
    refs: Dict[str, str] = {}
    _collect_source_refs(value, refs)
    return [refs[key] for key in sorted(refs)]


def _collect_source_refs(value: JsonValue, refs: Dict[str, str]) -> None:
    if isinstance(value, list):
        for item in value:
            _collect_source_refs(item, refs)
    if isinstance(value, dict):
        source_ref = value.get("source_ref")
        if isinstance(source_ref, str):
            _add_source_ref(refs, source_ref)
        nested = value.get("source_refs")
        if isinstance(nested, list):
            for item in nested:
                _add_source_ref(refs, _source_ref_pointer(item))
        for item in value.values():
            _collect_source_refs(item, refs)


def _add_source_ref(refs: Dict[str, str], value: str) -> None:
    if value:
        safe_ref = redact_text(value).text
        refs[safe_ref] = safe_ref


def _source_ref_pointer(value: JsonValue) -> str:
    if isinstance(value, str):
        return value
    if not isinstance(value, dict):
        return ""
    parts: list[str] = []
    for key in ("source_ref", "ref", "id", "document_id", "chunk_id", "line_range"):
        item = value.get(key)
        if isinstance(item, str) and item:
            parts.append("{}={}".format(key, item))
    return "|".join(parts)
