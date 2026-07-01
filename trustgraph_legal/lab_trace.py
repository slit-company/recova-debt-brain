from __future__ import annotations

import json
import os
import re
import time
import urllib.request
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from trustgraph_legal.governance_models import JsonValue
from trustgraph_legal.mcp_domain import invoke_tool
from trustgraph_legal.mcp_envelope import redact_json

JsonObject = Dict[str, JsonValue]
JsonAnyObject = Dict[str, Any]
JsonRows = List[JsonAnyObject]
DEFAULT_OWNER_EMAIL = "dev@slit.company"
_BLOCKED_DB_TERMS = re.compile(
    r"(?i)(resident[_ -]?id|national[_ -]?id|rrn|"
    r"authorization:[\s]*bearer|service_role|"
    r"supabase_service_role_key|cloudflare_api_token)"
)


@dataclass(frozen=True)
class TraceInvocation:
    tool_name: str
    arguments: JsonAnyObject
    envelope: JsonAnyObject
    latency_ms: int
    lab_owner_email: str = DEFAULT_OWNER_EMAIL


@dataclass(frozen=True)
class SupabaseConfig:
    url: str
    service_role_key: str


def invoke_with_trace(
    tool_name: str,
    arguments: Optional[JsonAnyObject] = None,
    repo_root: Optional[Path] = None,
) -> TraceInvocation:
    args = {} if arguments is None else arguments
    started = time.monotonic()
    envelope = invoke_tool(tool_name, args, repo_root)
    elapsed = max(0, round((time.monotonic() - started) * 1000))
    return TraceInvocation(tool_name, args, envelope, elapsed)


def tool_trace_row(invocation: TraceInvocation) -> JsonAnyObject:
    envelope = invocation.envelope
    result = _object(envelope.get("result"))
    redacted_arguments = db_safe_json(invocation.arguments)
    redacted_result = db_safe_json(result)
    return {
        "lab_owner_email": invocation.lab_owner_email,
        "tool_name": str(envelope.get("tool_name") or invocation.tool_name),
        "group_name": str(envelope.get("group") or "read"),
        "scope": str(envelope.get("scope") or "read:tools"),
        "status": _status(envelope, result),
        "arguments_hash_sha256": _hash_json(invocation.arguments),
        "envelope_hash_sha256": _hash_json(envelope),
        "redacted_arguments": redacted_arguments,
        "redacted_result": redacted_result,
        "source_refs": _list(envelope.get("source_refs")),
        "warnings": [str(item) for item in _list(envelope.get("warnings"))],
        "latency_ms": invocation.latency_ms,
    }


def rows_for_fixture_manifest(
    manifest_path: Path,
    repo_root: Optional[Path] = None,
) -> JsonRows:
    calls = (
        ("list_debt_collection_tools", {}),
        ("check_case_stop_gates", {"manifest_path": str(manifest_path)}),
        ("recommend_next_action", {"manifest_path": str(manifest_path)}),
    )
    return [
        tool_trace_row(invoke_with_trace(name, args, repo_root))
        for name, args in calls
    ]


def rows_for_payload(payload: JsonAnyObject, repo_root: Optional[Path] = None) -> JsonRows:
    tool_name = str(payload.get("tool_name") or "check_case_stop_gates")
    arguments = payload.get("arguments")
    args = arguments if isinstance(arguments, dict) else {}
    return [tool_trace_row(invoke_with_trace(tool_name, args, repo_root))]


def fake_supabase_payload(rows: JsonRows) -> JsonAnyObject:
    return {
        "mode": "fake_supabase",
        "row_count": len(rows),
        "raw_text_included": False,
        "records": rows,
        "summary": {
            "tool_names": sorted({str(row["tool_name"]) for row in rows}),
            "statuses": sorted({str(row["status"]) for row in rows}),
            "source_ref_count": sum(len(_list(row.get("source_refs"))) for row in rows),
        },
    }


def write_rows_to_supabase(rows: JsonRows, config: SupabaseConfig) -> JsonAnyObject:
    if not rows:
        return {"status": "skipped", "row_count": 0}
    endpoint = "{}/rest/v1/tool_traces".format(config.url.rstrip("/"))
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(rows, ensure_ascii=False).encode("utf-8"),
        headers={
            "apikey": config.service_role_key,
            "authorization": "Bearer {}".format(config.service_role_key),
            "content-type": "application/json",
            "prefer": "return=representation",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read().decode("utf-8")
    inserted = json.loads(body) if body else []
    return {
        "status": "recorded",
        "row_count": len(inserted) if isinstance(inserted, list) else len(rows),
    }


def supabase_config_from_env() -> SupabaseConfig:
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        missing = [
            name
            for name, value in (
                ("SUPABASE_URL", url),
                ("SUPABASE_SERVICE_ROLE_KEY", key),
            )
            if not value
        ]
        raise RuntimeError("missing env: {}".format(", ".join(missing)))
    return SupabaseConfig(url, key)


def ensure_no_raw_text(payload: JsonAnyObject, forbidden: Iterable[str]) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    found = [item for item in forbidden if item and item in encoded]
    if found:
        raise RuntimeError("redaction failed for {} item(s)".format(len(found)))


def db_safe_json(value: Any) -> Any:
    return _scrub_blocked_db_terms(redact_json(value))


def _status(envelope: JsonAnyObject, result: JsonAnyObject) -> str:
    status = str(result.get("status") or "")
    warnings = [str(item) for item in _list(envelope.get("warnings"))]
    if status == "unknown_tool" or "unknown_tool" in warnings:
        return "unknown_tool"
    if status in {"rejected", "blocked"}:
        return "rejected"
    if status == "error" or "error" in warnings:
        return "error"
    return "ok"


def _hash_json(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _object(value: Any) -> JsonAnyObject:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _scrub_blocked_db_terms(value: Any) -> Any:
    if isinstance(value, str):
        return _BLOCKED_DB_TERMS.sub("[SENSITIVE_LABEL_REDACTED]", value)
    if isinstance(value, list):
        return [_scrub_blocked_db_terms(item) for item in value]
    if isinstance(value, dict):
        return {key: _scrub_blocked_db_terms(item) for key, item in value.items()}
    return value
