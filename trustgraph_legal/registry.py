from __future__ import annotations

import hashlib
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Iterable

from trustgraph_legal import __version__
from trustgraph_legal.pii import redact_text

JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]

ONTOLOGY_VERSION: Final = "recova-debt-collection@v0"
PROMPT_VERSION: Final = "legal-ontology-extraction@v0"
OCR_VERSION: Final = "MinerU@legal_ocr_20260630"
EXTRACTOR_VERSION: Final = f"trustgraph_legal.ingest@{__version__}"
SCHEMA_VERSION: Final = "trustgraph-legal-ingest-dry-run/v1"


@dataclass(frozen=True, slots=True)
class RegistryOptions:
    limit: int | None = None
    workspace: str = "default"
    collection: str = "recova-debt-collection"


@dataclass(frozen=True, slots=True)
class ArchiveEntry:
    name: str
    content: bytes


@dataclass(frozen=True, slots=True)
class EvidenceKey:
    key_type: str
    key_hash: str

    def to_json(self) -> dict[str, JsonValue]:
        return {"key_type": self.key_type, "key_hash": self.key_hash}


@dataclass(frozen=True, slots=True)
class RegistryRecord:
    document_id: str
    registry_status: str
    source_hash: str
    source_path: str
    source_path_ref: str
    source_size_bytes: int
    case_packet_id: str
    tags: tuple[str, ...]
    pii_counts: dict[str, int]
    evidence_keys: tuple[EvidenceKey, ...]
    duplicate_of_document_id: str | None = None

    def to_json(self, options: RegistryOptions) -> dict[str, JsonValue]:
        record: dict[str, JsonValue] = {
            "document_id": self.document_id,
            "registry_status": self.registry_status,
            "source_hash": self.source_hash,
            "source_path": self.source_path,
            "source_path_ref": self.source_path_ref,
            "source_size_bytes": self.source_size_bytes,
            "ocr_version": OCR_VERSION,
            "extractor_version": EXTRACTOR_VERSION,
            "ontology_version": ONTOLOGY_VERSION,
            "prompt_version": PROMPT_VERSION,
            "review_status": "pending_registry_review",
            "confidence": 1.0,
            "case_packet_id": self.case_packet_id,
            "hybrid_evidence_keys": [key.to_json() for key in self.evidence_keys],
            "provenance": {
                "source_ref": self.source_path_ref,
                "content_hash": self.source_hash,
                "trustgraph_interface": "service/text-load",
                "workspace": options.workspace,
                "collection": options.collection,
            },
            "tags": list(self.tags),
            "pii_profile": {
                "redacted": self.pii_counts,
                "raw_text_included": False,
            },
        }
        if self.duplicate_of_document_id is not None:
            record["duplicate_of_document_id"] = self.duplicate_of_document_id
        return record


@dataclass(frozen=True, slots=True)
class RegistryPayload:
    records: tuple[RegistryRecord, ...]
    options: RegistryOptions

    def to_json(self) -> dict[str, JsonValue]:
        duplicate_count = sum(
            1 for record in self.records if record.registry_status == "duplicate"
        )
        return {
            "schema_version": SCHEMA_VERSION,
            "dry_run": True,
            "summary": {
                "records": len(self.records),
                "insert_candidates": len(self.records) - duplicate_count,
                "duplicates": duplicate_count,
            },
            "records": [record.to_json(self.options) for record in self.records],
        }


class ArchiveOpenError(Exception):
    def __init__(self, archive_path: Path) -> None:
        self.archive_path = archive_path
        super().__init__()

    def __str__(self) -> str:
        return f"cannot open archive: {self.archive_path}"


_COURT_CASE: Final = re.compile(r"\b[12]\d{3}[가-힣]{1,6}\d{1,8}\b")
_CLAIM_TOKEN: Final = re.compile(r"\[(?:CLAIM|CASE_PACKET)_TOKEN\]")
_TITLE_MARKERS: Final = ("지급명령", "판결", "집행문", "확정증명")
_ATTACHMENT_MARKERS: Final = ("압류", "추심", "제3채무자")
_INSOLVENCY_MARKERS: Final = ("파산", "면책", "신용회복", "회생")
_ASSIGNMENT_MARKERS: Final = ("양도", "승계", "양수")
_ASSET_MARKERS: Final = ("부동산", "보험", "예금", "급여", "자산")


def collect_registry_payload(
    archive_path: Path, options: RegistryOptions
) -> RegistryPayload:
    seen_hashes: dict[str, str] = {}
    records: list[RegistryRecord] = []
    try:
        with zipfile.ZipFile(archive_path) as archive:
            for entry in _iter_markdown_entries(archive):
                if options.limit is not None and len(records) >= options.limit:
                    break
                record = _build_record(entry, seen_hashes)
                records.append(record)
    except zipfile.BadZipFile as exc:
        raise ArchiveOpenError(archive_path) from exc
    except FileNotFoundError as exc:
        raise ArchiveOpenError(archive_path) from exc
    return RegistryPayload(records=tuple(records), options=options)


def _iter_markdown_entries(archive: zipfile.ZipFile) -> Iterable[ArchiveEntry]:
    names = sorted(
        name
        for name in archive.namelist()
        if name.lower().endswith(".md") and not name.endswith("/")
    )
    for name in names:
        yield ArchiveEntry(name=name, content=archive.read(name))


def _build_record(entry: ArchiveEntry, seen_hashes: dict[str, str]) -> RegistryRecord:
    source_hash = _sha256_prefixed(entry.content)
    document_id = f"legal-doc-{source_hash.replace('sha256:', '', 1)[:16]}"
    duplicate_of = seen_hashes.get(source_hash)
    if duplicate_of is None:
        seen_hashes[source_hash] = document_id
    redacted_path = redact_text(entry.name)
    decoded = entry.content.decode("utf-8", errors="replace")
    redacted_text = redact_text(decoded)
    evidence_keys = _extract_evidence_keys(decoded, source_hash)
    return RegistryRecord(
        document_id=document_id,
        registry_status="duplicate" if duplicate_of is not None else "dry_run_insert_candidate",
        source_hash=source_hash,
        source_path=redacted_path.text,
        source_path_ref=_path_ref(entry.name),
        source_size_bytes=len(entry.content),
        case_packet_id=_case_packet_id(evidence_keys, source_hash),
        tags=tuple(_classify_tags(decoded)),
        pii_counts=_merge_counts(redacted_path.counts, redacted_text.counts),
        evidence_keys=evidence_keys,
        duplicate_of_document_id=duplicate_of,
    )


def _extract_evidence_keys(text: str, source_hash: str) -> tuple[EvidenceKey, ...]:
    keys: list[EvidenceKey] = []
    keys.extend(_hashed_keys("court_case_number", _COURT_CASE.findall(text)))
    keys.extend(_hashed_keys("claim_or_packet_token", _CLAIM_TOKEN.findall(text)))
    if not keys:
        keys.append(EvidenceKey(key_type="document_hash", key_hash=source_hash))
    return tuple(keys)


def _hashed_keys(key_type: str, values: Iterable[str]) -> Iterable[EvidenceKey]:
    unique_values = sorted(set(values))
    for value in unique_values:
        yield EvidenceKey(key_type=key_type, key_hash=_sha256_prefixed(value.encode()))


def _case_packet_id(keys: tuple[EvidenceKey, ...], source_hash: str) -> str:
    key_material = "|".join(f"{key.key_type}:{key.key_hash}" for key in keys)
    material = key_material if key_material else source_hash
    return f"casepkt-{hashlib.sha256(material.encode()).hexdigest()[:20]}"


def _classify_tags(text: str) -> list[str]:
    tags: list[str] = ["legal-ocr", "recova-debt-collection"]
    marker_groups = (
        ("attachment-collection", _ATTACHMENT_MARKERS),
        ("enforcement-title", _TITLE_MARKERS),
        ("insolvency-credit-recovery", _INSOLVENCY_MARKERS),
        ("assignment-succession", _ASSIGNMENT_MARKERS),
        ("asset-evidence", _ASSET_MARKERS),
    )
    for tag, markers in marker_groups:
        if any(marker in text for marker in markers):
            tags.append(tag)
    return tags


def _merge_counts(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    return {key: left.get(key, 0) + right.get(key, 0) for key in sorted(left | right)}


def _sha256_prefixed(content: bytes) -> str:
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def _path_ref(path: str) -> str:
    return f"zip-entry:{hashlib.sha256(path.encode()).hexdigest()[:20]}"
