from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Final, List

from trustgraph_legal.stopgate_types import JsonObject, JsonValue, RuleSource, RuleSourceSet, StopGateRule

RULES_PATH: Final = (
    Path(__file__).resolve().parents[1]
    / "resources"
    / "legal_rules"
    / "debt_collection_stopgate_v0.json"
)


class StopGateInputError(Exception):
    def __init__(self, case_path: Path, detail: str) -> None:
        self.case_path = case_path
        self.detail = detail
        super().__init__()

    def __str__(self) -> str:
        return "{}: {}".format(self.case_path, self.detail)


def load_rule_source(rules_path: Path = RULES_PATH) -> RuleSourceSet:
    raw = json.loads(rules_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise StopGateInputError(rules_path, "rule source root must be an object")
    sources = tuple(_source_from_json(item) for item in _object_list(raw.get("sources")))
    source_by_id = {source.source_id: source for source in sources}
    return RuleSourceSet(
        _required_str(raw, "rule_source_version"),
        _required_str(raw, "review_status"),
        _required_str(raw, "effective_date"),
        _required_str(raw, "curation_policy"),
        tuple(_rule_from_json(item, source_by_id) for item in _object_list(raw.get("rules"))),
    )


def _source_from_json(item: JsonObject) -> RuleSource:
    return RuleSource(
        _required_str(item, "source_id"),
        _required_str(item, "statute_ref"),
        _required_str(item, "effective_date"),
        _required_str(item, "review_status"),
        _required_str(item, "source_ref"),
    )


def _rule_from_json(item: JsonObject, source_by_id: Dict[str, RuleSource]) -> StopGateRule:
    return StopGateRule(
        _required_str(item, "rule_id"),
        _required_str(item, "stopgate_id"),
        _required_str(item, "reason_code"),
        _required_str(item, "decision"),
        _required_str(item, "condition"),
        _required_str(item, "blocked_reason"),
        _required_str(item, "recommended_action"),
        tuple(_string_list(item.get("required_preconditions"))),
        tuple(_string_list(item.get("missing_evidence"))),
        tuple(_string_list(item.get("risk_flags"))),
        tuple(source_by_id[source_id] for source_id in _string_list(item.get("source_ids"))),
        tuple(_string_list(item.get("statute_refs"))),
        _required_str(item, "effective_date"),
    )


def _object_list(value: JsonValue) -> List[JsonObject]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _string_list(value: JsonValue) -> List[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def _required_str(item: JsonObject, key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str):
        raise StopGateInputError(RULES_PATH, "missing string key {}".format(key))
    return value
