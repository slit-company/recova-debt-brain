#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
# --- How to run ---
# /opt/homebrew/bin/python3 scripts/legal_ontology/domain_manual_inventory.py \
#   --manual "<manual.md>" \
#   --out .omo/evidence/debt-collection-domain-ontology-v1/task-1-manual-inventory.json
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, TextIO, TypeAlias

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    __package__ = "scripts.legal_ontology"

from .domain_manual_inventory_collectors import (
    collect_action_packets,
    collect_legal_sources,
    collect_term_candidates,
    count_sensitive_patterns,
    route_family_for,
)
from .domain_manual_inventory_terms import (
    FACT_HANDLE_TERMS,
    FINANCE_TERMS,
    RISK_TERMS,
    SCORING_TERMS,
    WORKFLOW_TERMS,
)

JsonScalar: TypeAlias = None | bool | int | float | str
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]

SCHEMA_VERSION: Final = "domain-manual-inventory/v2"
SUMMARY_KIND: Final = "manual_candidate_inventory"
HEADING_RE: Final = re.compile(r"^(?P<marks>#{1,6})\s+(?P<title>.+?)\s*$")
NUMBERED_HEADING_RE: Final = re.compile(r"^(?P<number>\d+(?:\.\d+)*)\.?\s*(?P<title>.+)$")
ROUTE_SECTION_RANGE: Final = range(4, 22)


@dataclass(frozen=True, slots=True)
class InventoryArgs:
    manual: Path
    out: Path


@dataclass(frozen=True, slots=True)
class Heading:
    heading_id: str
    level: int
    number: str
    title: str
    parent_number: str


class ManualInventoryError(RuntimeError):
    detail: str

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class UsageError(RuntimeError):
    detail: str

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


def inventory_manual(manual_path: Path) -> JsonObject:
    if not manual_path.exists():
        raise ManualInventoryError("manual path does not exist")
    if not manual_path.is_file():
        raise ManualInventoryError("manual path is not a file")

    text = manual_path.read_text(encoding="utf-8", errors="replace")
    headings = parse_headings(text)
    if not headings:
        raise ManualInventoryError("manual has no markdown headings")

    route_candidates = collect_route_candidates(headings)
    workflow_candidates = collect_term_candidates(WORKFLOW_TERMS, text, "workflow")
    fact_handles = collect_term_candidates(FACT_HANDLE_TERMS, text, "fact")
    risk_blocker_candidates = collect_term_candidates(RISK_TERMS, text, "risk")
    legal_source_candidates = collect_legal_sources(text)
    finance_candidates = collect_term_candidates(FINANCE_TERMS, text, "finance")
    scoring_fields = collect_term_candidates(SCORING_TERMS, text, "score")
    action_packet_candidates = collect_action_packets(text)

    counts: JsonObject = {
        "headings": len(headings),
        "route_candidates": len(route_candidates),
        "workflow_candidates": len(workflow_candidates),
        "fact_handles": len(fact_handles),
        "risk_blocker_candidates": len(risk_blocker_candidates),
        "legal_source_candidates": len(legal_source_candidates),
        "finance_candidates": len(finance_candidates),
        "scoring_fields": len(scoring_fields),
        "action_packet_candidates": len(action_packet_candidates),
    }
    source: JsonObject = {
        "manual_kind": "debt_collection_practical_manual_v2",
        "structure_fingerprint": structure_fingerprint(headings),
        "source_paths_included": False,
    }
    pii_profile: JsonObject = {
        "raw_text_included": False,
        "source_text_included": False,
        "matched_text_included": False,
        "source_paths_included": False,
        "sensitive_counts_only": True,
        "possible_sensitive_pattern_counts": count_sensitive_patterns(text),
    }
    non_execution_semantics: JsonObject = {
        "inventory_only": True,
        "direct_execution_allowed": False,
        "human_review_required": True,
    }
    payload: JsonObject = {
        "schema_version": SCHEMA_VERSION,
        "summary_kind": SUMMARY_KIND,
        "source": source,
        "pii_profile": pii_profile,
        "counts": counts,
        "headings": json_object_list([heading_to_json(heading) for heading in headings]),
        "route_candidates": json_object_list(route_candidates),
        "workflow_candidates": json_object_list(workflow_candidates),
        "fact_handles": json_object_list(fact_handles),
        "risk_blocker_candidates": json_object_list(risk_blocker_candidates),
        "legal_source_candidates": json_object_list(legal_source_candidates),
        "finance_candidates": json_object_list(finance_candidates),
        "scoring_fields": json_object_list(scoring_fields),
        "action_packet_candidates": json_object_list(action_packet_candidates),
        "non_execution_semantics": non_execution_semantics,
    }
    return payload


def parse_headings(text: str) -> list[Heading]:
    headings: list[Heading] = []
    parent_number = ""
    for line in text.splitlines():
        match = HEADING_RE.match(line)
        if match is None:
            continue
        title = match.group("title").strip()
        number, clean_title = split_heading_number(title)
        level = len(match.group("marks"))
        if level == 2 and number:
            parent_number = number
        heading_number = number if number else f"unumbered-{len(headings) + 1}"
        headings.append(
            Heading(
                heading_id=f"heading:{heading_number.replace('.', '-')}",
                level=level,
                number=heading_number,
                title=clean_title,
                parent_number=parent_number,
            ),
        )
    return headings


def split_heading_number(title: str) -> tuple[str, str]:
    match = NUMBERED_HEADING_RE.match(title)
    if match is None:
        return "", title
    return match.group("number"), match.group("title").strip()


def collect_route_candidates(headings: Sequence[Heading]) -> list[JsonObject]:
    routes: list[JsonObject] = []
    for heading in headings:
        if heading.level < 3 or not is_route_heading(heading):
            continue
        routes.append(
            {
                "candidate_id": f"route:{heading.number.replace('.', '-')}",
                "name": heading.title,
                "source_heading_id": heading.heading_id,
                "route_family": route_family_for(heading.title),
                "advisory_only": True,
                "direct_execution_allowed": False,
            },
        )
    return routes


def json_object_list(values: Sequence[JsonObject]) -> list[JsonValue]:
    return [value for value in values]


def is_route_heading(heading: Heading) -> bool:
    major = major_section(heading.parent_number)
    return major in ROUTE_SECTION_RANGE or any(term in heading.title for term in ("압류", "루트", "지급명령", "변제"))


def major_section(number: str) -> int:
    first = number.split(".", maxsplit=1)[0]
    if not first.isdecimal():
        return 0
    return int(first)


def heading_to_json(heading: Heading) -> JsonObject:
    return {
        "heading_id": heading.heading_id,
        "level": heading.level,
        "number": heading.number,
        "title": heading.title,
        "parent_number": heading.parent_number,
    }


def structure_fingerprint(headings: Sequence[Heading]) -> str:
    digest = hashlib.sha256()
    for heading in headings:
        digest.update(f"{heading.level}:{heading.number}:{heading.title}\n".encode("utf-8"))
    alpha_digest = "".join(chr(ord("a") + int(char)) if char.isdigit() else char for char in digest.hexdigest())
    return f"sha256-alpha:{alpha_digest}"


def write_json(path: Path, payload: JsonObject) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args(argv: Sequence[str]) -> InventoryArgs:
    manual: Path | None = None
    out: Path | None = None
    index = 0
    while index < len(argv):
        option = argv[index]
        match option:
            case "--manual":
                manual, index = read_path_arg(argv, index)
            case "--out":
                out, index = read_path_arg(argv, index)
            case _:
                raise UsageError(f"unknown argument {option}")
    if manual is None or out is None:
        raise UsageError("usage: domain_manual_inventory.py --manual <path> --out <path>")
    return InventoryArgs(manual=manual, out=out)


def read_path_arg(argv: Sequence[str], index: int) -> tuple[Path, int]:
    value_index = index + 1
    if value_index >= len(argv):
        raise UsageError(f"{argv[index]} requires a value")
    return Path(argv[value_index]), value_index + 1


def route_count_from_payload(payload: JsonObject) -> int:
    counts = payload["counts"]
    if not isinstance(counts, dict):
        raise ManualInventoryError("internal counts missing object")
    route_count = counts.get("route_candidates")
    if isinstance(route_count, bool) or not isinstance(route_count, int):
        raise ManualInventoryError("internal route count missing")
    return route_count


def main(argv: Sequence[str], stderr: TextIO = sys.stderr) -> int:
    try:
        args = parse_args(argv)
    except UsageError as error:
        print(f"ERROR {error}", file=stderr)
        return 2

    try:
        payload = inventory_manual(args.manual)
        write_json(args.out, payload)
        route_count = route_count_from_payload(payload)
    except (ManualInventoryError, OSError, UnicodeError) as error:
        print(f"ERROR {error}", file=stderr)
        return 1

    print(f"PASS manual inventory route_candidates={route_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
