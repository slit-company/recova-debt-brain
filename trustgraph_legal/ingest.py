from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, Sequence

from trustgraph_legal.registry import (
    JsonValue,
    RegistryOptions,
    RegistryRecord,
    collect_registry_payload,
)

TEXT_LOAD_SCHEMA_VERSION = "trustgraph-legal-ingest-text-load/v1"


class TextLoadFlow(Protocol):
    def load_text(
        self,
        text: bytes,
        id: str,
        metadata: Any = None,
        charset: str = "utf-8",
        collection: str | None = None,
    ) -> Any:
        ...


@dataclass(frozen=True)
class RegistryMetadata:
    record: RegistryRecord
    options: RegistryOptions

    def emit(self, emit: Any) -> None:
        subject = "urn:trustgraph:legal-document:{}".format(self.record.document_id)
        triples = (
            ("source_hash", self.record.source_hash),
            ("source_ref", self.record.source_path_ref),
            ("case_packet_id", self.record.case_packet_id),
            ("ontology_version", self.record.to_json(self.options)["ontology_version"]),
            ("prompt_version", self.record.to_json(self.options)["prompt_version"]),
            ("workspace", self.options.workspace),
            ("collection", self.options.collection),
        )
        for predicate, value in triples:
            emit(
                {
                    "s": subject,
                    "p": "recova-debt-collection:{}".format(predicate),
                    "o": str(value),
                }
            )


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


def load_registry_records_to_trustgraph(
    archive_path: Path,
    options: RegistryOptions,
    flow: TextLoadFlow,
) -> dict[str, JsonValue]:
    payload = collect_registry_payload(archive_path, options)
    content_by_hash = _content_by_hash(archive_path, options.limit)
    loaded: list[dict[str, JsonValue]] = []
    skipped_duplicates = 0

    for record in payload.records:
        if record.registry_status == "duplicate":
            skipped_duplicates += 1
            continue
        content = content_by_hash.get(record.source_hash)
        if content is None:
            continue
        flow.load_text(
            text=content,
            id=record.document_id,
            metadata=RegistryMetadata(record, options),
            charset="utf-8",
            collection=options.collection,
        )
        loaded.append(
            {
                "document_id": record.document_id,
                "source_hash": record.source_hash,
                "source_ref": record.source_path_ref,
                "case_packet_id": record.case_packet_id,
                "trustgraph_interface": "service/text-load",
                "raw_text_included": False,
            }
        )

    return {
        "schema_version": TEXT_LOAD_SCHEMA_VERSION,
        "dry_run": False,
        "summary": {
            "records": len(payload.records),
            "load_text_calls": len(loaded),
            "duplicates_skipped": skipped_duplicates,
        },
        "records": loaded,
    }


def _content_by_hash(archive_path: Path, limit: int | None) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    with zipfile.ZipFile(archive_path) as archive:
        names = sorted(
            name
            for name in archive.namelist()
            if name.lower().endswith(".md") and not name.endswith("/")
        )
        for name in names:
            if limit is not None and len(result) >= limit:
                break
            content = archive.read(name)
            source_hash = "sha256:{}".format(hashlib.sha256(content).hexdigest())
            result.setdefault(source_hash, content)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
