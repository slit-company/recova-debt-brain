from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias


JsonScalar: TypeAlias = None | bool | int | float | str
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]


@dataclass(frozen=True, slots=True)
class DomainSourceIssue:
    location: str
    message: str

    def format(self) -> str:
        return f"{self.location}: {self.message}"


@dataclass(frozen=True, slots=True)
class DomainSourceSummary:
    source_version: str
    source_count: int
    route_count: int
    route_source_ref_count: int
    stopgate_count: int
    stopgate_source_ref_count: int
    workflow_ref_count: int
    workflow_source_ref_count: int


def load_json(path: Path) -> JsonObject:
    with path.open(encoding="utf-8") as handle:
        raw: JsonValue = json.load(handle)

    if not isinstance(raw, dict):
        raise TypeError("resource root must be a JSON object")
    return raw


def text_value(entry: JsonObject, field: str) -> str:
    value = entry.get(field)
    if isinstance(value, str):
        return value
    return ""


def bool_value(entry: JsonObject, field: str) -> bool | None:
    value = entry.get(field)
    if isinstance(value, bool):
        return value
    return None


def object_list_value(entry: JsonObject, field: str, location: str) -> tuple[list[JsonObject], list[DomainSourceIssue]]:
    value = entry.get(field)
    if not isinstance(value, list):
        return [], [DomainSourceIssue(location=location, message=f"{field} must be a list")]

    items: list[JsonObject] = []
    issues: list[DomainSourceIssue] = []
    for index, item in enumerate(value):
        item_location = f"{location}.{field}[{index}]"
        if isinstance(item, dict):
            items.append(item)
        else:
            issues.append(DomainSourceIssue(location=item_location, message="entry must be an object"))
    return items, issues


def string_list_value(entry: JsonObject, field: str, location: str) -> tuple[list[str], list[DomainSourceIssue]]:
    value = entry.get(field)
    if not isinstance(value, list):
        return [], [DomainSourceIssue(location=location, message=f"{field} must be a string list")]

    strings: list[str] = []
    issues: list[DomainSourceIssue] = []
    for index, item in enumerate(value):
        item_location = f"{location}.{field}[{index}]"
        if isinstance(item, str) and item:
            strings.append(item)
        else:
            issues.append(DomainSourceIssue(location=item_location, message="entry must be a non-empty string"))
    return strings, issues


def validate_unique_ids(ids: Sequence[str], label: str) -> list[DomainSourceIssue]:
    issues: list[DomainSourceIssue] = []
    seen: set[str] = set()
    for identifier in ids:
        if identifier in seen:
            issues.append(DomainSourceIssue(location=label, message=f"duplicate id {identifier}"))
        seen.add(identifier)
    return issues


def validate_known_ids(
    usage_ids: Sequence[str],
    known_ids: set[str],
    location: str,
    label: str,
) -> list[DomainSourceIssue]:
    issues: list[DomainSourceIssue] = []
    for usage_id in usage_ids:
        if usage_id not in known_ids:
            issues.append(DomainSourceIssue(location=location, message=f"unknown {label} {usage_id}"))
    return issues
