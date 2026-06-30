from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Final, List, Optional, Sequence, Tuple, Union

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from trustgraph_legal.mcp_domain import invoke_tool, list_tools

JsonScalar = Optional[Union[str, int, float, bool]]
JsonValue = Union[JsonScalar, List["JsonValue"], Dict[str, "JsonValue"]]
JsonObject = Dict[str, JsonValue]

SCHEMA_VERSION: Final = "trustgraph-legal-packet-evaluation/v1"
RESPONSE_SCHEMA_VERSION: Final = "trustgraph-legal-mcp-tool-response/v1"
CONTRACT_SCHEMA_VERSION: Final = "trustgraph-legal-mcp-tool-contract/v1"
SENSITIVE_PATTERNS: Final[Tuple[re.Pattern[str], ...]] = (
    re.compile(r"\b\d{6}-\d{7}\b"),
    re.compile(r"\b(?:\+82[-.\s]?)?0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}\b"),
    re.compile(
        r"(?i)\b(?:account|bank|계좌|은행|입금|송금)[^\n\r]{0,24}?"
        r"\d{2,6}[-.\s]\d{2,6}[-.\s]\d{2,8}\b"
    ),
)
REQUIRED_ENVELOPE_KEYS: Final = {
    "schema_version",
    "tool_name",
    "group",
    "scope",
    "pii_profile",
    "redaction",
    "source_refs",
    "warnings",
    "result",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 scripts/legal_ontology/evaluate_packet.py"
    )
    parser.add_argument("--fixtures", required=True)
    parser.add_argument("--out", required=True)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = Path.cwd().resolve()
    fixtures = _repo_path(args.fixtures, repo_root)
    output = _repo_path(args.out, repo_root)
    payload = evaluate_packet(fixtures, repo_root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload["summary"], ensure_ascii=False, sort_keys=True))
    return 0 if payload["summary"]["status"] == "passed" else 1


def evaluate_packet(fixtures: Path, repo_root: Path) -> JsonObject:
    tools = list_tools()
    tool_summary = _validate_tool_contracts(tools)
    case_graph = invoke_tool(
        "get_case_graph",
        {"manifest_path": str(fixtures.relative_to(repo_root))},
        repo_root,
    )
    graph_payload = _result_object(case_graph)
    stopgates = invoke_tool(
        "check_case_stop_gates",
        {"case_graph": graph_payload},
        repo_root,
    )
    recommendation = invoke_tool(
        "recommend_next_action",
        {"case_graph": graph_payload},
        repo_root,
    )
    execution_probe = invoke_tool(
        "execute_direct_collection_filing",
        {"case_graph": graph_payload},
        repo_root,
    )
    responses = [case_graph, stopgates, recommendation, execution_probe]
    checks = _validate_responses(responses)
    status = "passed" if tool_summary["tool_count"] == 16 and not checks else "failed"
    return {
        "schema_version": SCHEMA_VERSION,
        "fixtures": str(fixtures.relative_to(repo_root)),
        "summary": {
            "status": status,
            "tool_count": tool_summary["tool_count"],
            "evaluated_tools": [str(item["tool_name"]) for item in responses],
            "decision": _result_object(stopgates).get("decision"),
            "recommendation": _result_object(recommendation).get("recommended_next_action"),
            "failure_probe": _result_object(execution_probe).get("status"),
            "issues": checks,
        },
        "tool_contracts": tool_summary,
        "responses": {
            "get_case_graph": case_graph,
            "check_case_stop_gates": stopgates,
            "recommend_next_action": recommendation,
            "direct_execution_probe": execution_probe,
        },
    }


def _validate_tool_contracts(tools: List[JsonObject]) -> JsonObject:
    groups = sorted({str(tool.get("group", "")) for tool in tools})
    schema_versions = sorted({str(tool.get("schema_version", "")) for tool in tools})
    names = [str(tool.get("tool_name", "")) for tool in tools]
    return {
        "tool_count": len(tools),
        "tool_names": names,
        "groups": groups,
        "schema_versions": schema_versions,
        "all_contracts_versioned": schema_versions == [CONTRACT_SCHEMA_VERSION],
    }


def _validate_responses(responses: List[JsonObject]) -> List[JsonObject]:
    issues: List[JsonObject] = []
    for response in responses:
        missing = sorted(REQUIRED_ENVELOPE_KEYS - set(response))
        if missing:
            issues.append({"tool_name": response.get("tool_name"), "issue": "missing_envelope_keys", "keys": missing})
        if response.get("schema_version") != RESPONSE_SCHEMA_VERSION:
            issues.append({"tool_name": response.get("tool_name"), "issue": "wrong_schema_version"})
        pii_profile = response.get("pii_profile")
        if not isinstance(pii_profile, dict) or pii_profile.get("raw_text_included") is not False:
            issues.append({"tool_name": response.get("tool_name"), "issue": "raw_text_profile_not_false"})
        source_refs = response.get("source_refs")
        if not isinstance(source_refs, list):
            issues.append({"tool_name": response.get("tool_name"), "issue": "source_refs_not_list"})
        encoded = json.dumps(response, ensure_ascii=False, sort_keys=True)
        for pattern in SENSITIVE_PATTERNS:
            if pattern.search(encoded) is not None:
                issues.append({"tool_name": response.get("tool_name"), "issue": "sensitive_pattern_detected"})
                break
    recommendation = _response_by_tool(responses, "recommend_next_action")
    if _result_object(recommendation).get("no_direct_filing_contact_or_collection") is not True:
        issues.append({"tool_name": "recommend_next_action", "issue": "execution_boundary_missing"})
    direct_probe = _response_by_tool(responses, "execute_direct_collection_filing")
    if _result_object(direct_probe).get("status") != "unknown_tool":
        issues.append({"tool_name": "execute_direct_collection_filing", "issue": "direct_execution_not_blocked"})
    return issues


def _response_by_tool(responses: List[JsonObject], tool_name: str) -> JsonObject:
    for response in responses:
        if response.get("tool_name") == tool_name:
            return response
    return {}


def _result_object(response: JsonObject) -> JsonObject:
    result = response.get("result")
    return result if isinstance(result, dict) else {}


def _repo_path(value: str, repo_root: Path) -> Path:
    path = Path(value)
    candidate = path if path.is_absolute() else repo_root / path
    resolved = candidate.resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError:
        raise SystemExit("path outside repo_root: {}".format(value))
    return resolved


if __name__ == "__main__":
    raise SystemExit(main())
