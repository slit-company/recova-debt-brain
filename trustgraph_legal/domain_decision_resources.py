from __future__ import annotations

import json
import typing
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

from typing_extensions import TypeAlias, override

from trustgraph_legal.route_decisions import RouteDecisionTable, SourceReviewStatus, load_decision_table

if TYPE_CHECKING:
    JsonValue: TypeAlias = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]

    def _loads_json(_raw_text: str) -> JsonValue: ...
else:
    JsonValue: TypeAlias = typing.Union[None, bool, int, float, str, list["JsonValue"], dict[str, "JsonValue"]]

    def _loads_json(_raw_text: str) -> JsonValue:
        return json.loads(_raw_text)
JsonObject: TypeAlias = dict[str, JsonValue]
REPO_ROOT: Final = Path(__file__).resolve().parents[1]
DECISIONS_PATH: Final = REPO_ROOT / "resources" / "decision_tables" / "debt_collection_route_decisions_v1.json"
SOURCES_PATH: Final = REPO_ROOT / "resources" / "legal_rules" / "debt_collection_domain_sources_v1.json"
ACTION_PACKETS_PATH: Final = REPO_ROOT / "resources" / "action_packets" / "debt_collection_action_packets_v1.json"
WORKFLOW_PATH: Final = REPO_ROOT / "resources" / "workflows" / "debt_collection_workflow_v1.json"
FINANCE_PATH: Final = REPO_ROOT / "resources" / "finance" / "claim_finance_model_v1.json"
STOPGATE_PATH: Final = REPO_ROOT / "resources" / "legal_rules" / "debt_collection_stopgate_domain_v1.json"


@dataclass(frozen=True)
class DomainDecisionError(Exception):
    location: str
    reason_code: str
    message: str

    @override
    def __str__(self) -> str:
        return "{}: {}".format(self.reason_code, self.message)


@dataclass(frozen=True, slots=True)
class DomainDecisionResourceRequest:
    decisions_path: Path
    sources_path: Path
    action_packets_path: Path
    finance_path: Path
    stopgate_path: Path
    expected_domain_source_version: str | None


@dataclass(frozen=True, slots=True)
class ResourceBundle:
    decision_table: RouteDecisionTable
    source_reviews: tuple[SourceReviewStatus, ...]
    action_packets_by_type: dict[str, JsonObject]
    versions: JsonObject


def load_domain_decision_resources(request: DomainDecisionResourceRequest) -> ResourceBundle:
    table = load_decision_table(request.decisions_path)
    sources = load_json_object(request.sources_path)
    actions = load_json_object(request.action_packets_path)
    finance = load_json_object(request.finance_path)
    stopgate = load_json_object(request.stopgate_path)
    source_version = text(sources.get("rule_source_version"))
    finance_version = text(finance.get("model_version"))
    _require_source_version(source_version, text(table.root.get("domain_source_version")), request.expected_domain_source_version)
    if finance_version != text(table.root.get("finance_model_version")):
        raise DomainDecisionError("resources/finance/claim_finance_model_v1.json", "stale_finance_model_version", "finance model version does not match the decision table")
    return ResourceBundle(
        table,
        tuple(
            SourceReviewStatus(
                source_id=text(source.get("source_id")),
                review_status=text(source.get("review_status")),
            )
            for source in json_objects(sources.get("sources"))
            if text(source.get("source_id"))
        ),
        {text(schema.get("packet_type")): schema for schema in json_objects(actions.get("packet_schemas")) if text(schema.get("packet_type"))},
        {
            "decision_table_version": text(table.root.get("decision_table_version")),
            "domain_source_version": source_version,
            "workflow_version": text(table.root.get("workflow_version")),
            "finance_model_version": finance_version,
            "action_packet_version": text(actions.get("action_packet_version")),
            "stopgate_rule_source_version": text(stopgate.get("rule_source_version")),
        },
    )


def load_json_object(path: Path) -> JsonObject:
    raw = _loads_json(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise DomainDecisionError(path.name, "invalid_json_resource", "resource root must be an object")
    return raw


def json_object(value: JsonValue) -> JsonObject:
    return value if isinstance(value, dict) else {}


def json_objects(value: JsonValue) -> tuple[JsonObject, ...]:
    return tuple(item for item in value if isinstance(item, dict)) if isinstance(value, list) else ()


def strings(value: JsonValue) -> tuple[str, ...]:
    return tuple(item for item in value if isinstance(item, str) and item) if isinstance(value, list) else ()


def text(value: JsonValue) -> str:
    return value if isinstance(value, str) else ""


def _require_source_version(actual: str, expected: str, requested: str | None) -> None:
    if actual != expected or (requested is not None and actual != requested):
        raise DomainDecisionError(
            "resources/legal_rules/debt_collection_domain_sources_v1.json",
            "stale_legal_source_version",
            "domain legal-source version does not match the decision table",
        )
