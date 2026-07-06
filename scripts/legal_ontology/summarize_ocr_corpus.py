#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
# --- How to run ---
# /opt/homebrew/bin/python3 scripts/legal_ontology/summarize_ocr_corpus.py \
#   --ocr-root /Users/cosmos/dev/ocr/MinerU/work/legal_ocr_20260630 \
#   --out .omo/evidence/debtor-context-graph-v0/task-3-real-ocr-assembly-summary.json
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, TextIO, TypeAlias

JsonScalar: TypeAlias = None | bool | int | float | str
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]

SCHEMA_VERSION: Final = "legal-ocr-corpus-summary/v1"
DEFAULT_MARKDOWN_DIR: Final = "markdown_flat"
MANIFEST_NAME: Final = "manifest.tsv"
FINANCIAL_TERMS: Final = ("계좌", "은행", "입금", "송금")
SIGNAL_TERMS: Final[dict[str, tuple[str, ...]]] = {
    "payment_order": ("지급명령", "판결", "payment order", "enforceable title"),
    "service_finality": ("송달", "확정", "집행문", "service", "finality"),
    "attachment": ("압류", "추심명령", "attachment", "collection order"),
    "insolvency": ("파산", "면책", "회생", "rehabilitation"),
    "assignment": ("채권양도", "승계", "assignment", "succession"),
    "asset_evidence": ("부동산", "보험", "재산", "asset"),
    "ledger": ("회수", "비용", "ledger", "recovery"),
}
SENSITIVE_PATTERNS: Final[dict[str, re.Pattern[str]]] = {
    "resident_registration": re.compile(r"\b\d{6}-\d{7}\b"),
    "phone": re.compile(r"(?:\+82[-.\s]?)?0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}"),
    "financial_identifier": re.compile("(?:" + "|".join(FINANCIAL_TERMS) + r").{0,24}\d"),
    "long_digit_sequence": re.compile(r"\b\d{10,16}\b"),
}


class CorpusSummaryError(RuntimeError):
    pass


class UsageError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ProbeArgs:
    ocr_root: Path
    out: Path
    limit: int | None


@dataclass(frozen=True, slots=True)
class PageStats:
    char_count: int
    line_count: int
    signal_hits: dict[str, int]
    sensitive_hits: dict[str, int]

    @classmethod
    def from_text(cls, text: str) -> PageStats:
        lowered = text.lower()
        return cls(
            char_count=len(text),
            line_count=len(text.splitlines()),
            signal_hits={
                signal: sum(lowered.count(term.lower()) for term in terms)
                for signal, terms in SIGNAL_TERMS.items()
            },
            sensitive_hits={
                label: len(pattern.findall(text))
                for label, pattern in SENSITIVE_PATTERNS.items()
            },
        )


def summarize_ocr_root(ocr_root: Path, limit: int | None = None) -> JsonObject:
    markdown_paths, source_kind = discover_markdown_paths(ocr_root)
    selected_paths = markdown_paths[:limit] if limit is not None else markdown_paths
    if not selected_paths:
        raise CorpusSummaryError("no markdown pages found")

    page_stats = [PageStats.from_text(path.read_text(encoding="utf-8", errors="replace")) for path in selected_paths]
    char_counts = [stats.char_count for stats in page_stats]
    line_counts = [stats.line_count for stats in page_stats]
    manifest_path = ocr_root / MANIFEST_NAME
    fingerprint = hash_page_stats(page_stats)

    return {
        "schema_version": SCHEMA_VERSION,
        "summary_kind": "aggregate_only",
        "pii_profile": {
            "raw_text_included": False,
            "matched_text_included": False,
            "source_paths_included": False,
        },
        "corpus": {
            "root_label": ocr_root.name,
            "markdown_source": source_kind,
            "manifest_present": manifest_path.exists(),
            "manifest_rows": count_manifest_rows(manifest_path),
            "limit": limit,
            "sample_limited": limit is not None and len(markdown_paths) > len(selected_paths),
        },
        "summary": {
            "pages": len(selected_paths),
            "available_pages": len(markdown_paths),
            "total_chars": sum(char_counts),
            "total_lines": sum(line_counts),
            "empty_pages": sum(1 for char_count in char_counts if char_count == 0),
            "min_chars": min(char_counts),
            "max_chars": max(char_counts),
            "average_chars": round(sum(char_counts) / len(char_counts), 2),
            "corpus_fingerprint": fingerprint,
        },
        "signal_page_counts": count_signal_pages(page_stats),
        "signal_hit_counts": sum_hit_counts(page_stats, SIGNAL_TERMS),
        "possible_sensitive_pattern_counts": sum_hit_counts(page_stats, SENSITIVE_PATTERNS),
    }


def discover_markdown_paths(ocr_root: Path) -> tuple[list[Path], str]:
    if not ocr_root.exists():
        raise CorpusSummaryError(f"ocr root does not exist: {ocr_root}")
    if not ocr_root.is_dir():
        raise CorpusSummaryError(f"ocr root is not a directory: {ocr_root}")

    flat_paths = sorted((ocr_root / DEFAULT_MARKDOWN_DIR).glob("*.md"))
    if flat_paths:
        return flat_paths, DEFAULT_MARKDOWN_DIR

    manifest_paths = manifest_markdown_paths(ocr_root / MANIFEST_NAME)
    if manifest_paths:
        return manifest_paths, MANIFEST_NAME

    recursive_paths = sorted(ocr_root.rglob("*.md"))
    return recursive_paths, "recursive-md"


def manifest_markdown_paths(manifest_path: Path) -> list[Path]:
    if not manifest_path.exists():
        return []

    with manifest_path.open(encoding="utf-8", newline="") as handle:
        rows = csv.DictReader(handle, delimiter="\t")
        paths = [
            Path(markdown_path)
            for row in rows
            for markdown_path in [row.get("markdown", "")]
            if markdown_path and Path(markdown_path).exists()
        ]
    return sorted(dict.fromkeys(paths))


def count_manifest_rows(manifest_path: Path) -> int:
    if not manifest_path.exists():
        return 0

    with manifest_path.open(encoding="utf-8", newline="") as handle:
        rows = csv.DictReader(handle, delimiter="\t")
        return sum(1 for _row in rows)


def hash_page_stats(page_stats: Sequence[PageStats]) -> str:
    digest = hashlib.sha256()
    for stats in page_stats:
        digest.update(f"{stats.char_count}:{stats.line_count}\n".encode("utf-8"))
    return f"sha256:{digest.hexdigest()}"


def count_signal_pages(page_stats: Sequence[PageStats]) -> JsonObject:
    return {
        signal: sum(1 for stats in page_stats if stats.signal_hits[signal] > 0)
        for signal in SIGNAL_TERMS
    }


def sum_hit_counts(page_stats: Sequence[PageStats], labels: Mapping[str, object]) -> JsonObject:
    return {
        label: sum(_hits_for(stats, label) for stats in page_stats)
        for label in labels
    }


def _hits_for(stats: PageStats, label: str) -> int:
    if label in stats.signal_hits:
        return stats.signal_hits[label]
    return stats.sensitive_hits[label]


def write_json(path: Path, payload: JsonObject) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def page_count_from_payload(payload: JsonObject) -> int:
    summary = payload["summary"]
    if not isinstance(summary, dict):
        raise CorpusSummaryError("internal summary missing object")
    pages = summary.get("pages")
    if isinstance(pages, bool) or not isinstance(pages, int):
        raise CorpusSummaryError("internal summary missing page count")
    return pages


def parse_args(argv: Sequence[str]) -> ProbeArgs:
    ocr_root: Path | None = None
    out: Path | None = None
    limit: int | None = None
    index = 0
    while index < len(argv):
        option = argv[index]
        if option == "--ocr-root":
            ocr_root, index = read_path_arg(argv, index)
        elif option == "--out":
            out, index = read_path_arg(argv, index)
        elif option == "--limit":
            limit, index = read_limit_arg(argv, index)
        else:
            raise UsageError(f"unknown argument {option}")

    if ocr_root is None or out is None:
        raise UsageError("usage: summarize_ocr_corpus.py --ocr-root <path> --out <path> [--limit <n>]")
    return ProbeArgs(ocr_root=ocr_root, out=out, limit=limit)


def read_path_arg(argv: Sequence[str], index: int) -> tuple[Path, int]:
    value, next_index = read_arg_value(argv, index)
    return Path(value), next_index


def read_limit_arg(argv: Sequence[str], index: int) -> tuple[int, int]:
    value, next_index = read_arg_value(argv, index)
    try:
        limit = int(value)
    except ValueError as error:
        raise UsageError("--limit must be an integer") from error
    return limit, next_index


def read_arg_value(argv: Sequence[str], index: int) -> tuple[str, int]:
    value_index = index + 1
    if value_index >= len(argv):
        raise UsageError(f"{argv[index]} requires a value")
    return argv[value_index], value_index + 1


def main(argv: Sequence[str], stderr: TextIO = sys.stderr) -> int:
    try:
        args = parse_args(argv)
    except UsageError as error:
        print(f"ERROR {error}", file=stderr)
        return 2

    if args.limit is not None and args.limit < 1:
        print("ERROR --limit must be greater than zero", file=stderr)
        return 2

    try:
        payload = summarize_ocr_root(args.ocr_root, args.limit)
        write_json(args.out, payload)
        page_count = page_count_from_payload(payload)
    except (CorpusSummaryError, OSError, UnicodeError, csv.Error) as error:
        print(f"ERROR {error}", file=stderr)
        return 1

    print(f"PASS aggregate OCR summary pages={page_count} out={args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
