from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from trustgraph_legal.registry import RegistryOptions, collect_registry_payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -m trustgraph_legal.ingest",
        description="Build PII-safe dry-run registry records for legal OCR markdown zips.",
    )
    parser.add_argument("--zip", required=True, dest="zip_path")
    parser.add_argument("--dry-run", required=True, action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--workspace", default="default")
    parser.add_argument("--collection", default="recova-debt-collection")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be greater than 0")
    options = RegistryOptions(
        limit=args.limit,
        workspace=args.workspace,
        collection=args.collection,
    )
    payload = collect_registry_payload(Path(args.zip_path), options)
    evidence_path = Path(args.evidence)
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        json.dumps(payload.to_json(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    summary = payload.to_json()["summary"]
    print(
        json.dumps(
            {
                "dry_run": True,
                "records": summary["records"],
                "insert_candidates": summary["insert_candidates"],
                "duplicates": summary["duplicates"],
                "evidence": str(evidence_path),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
