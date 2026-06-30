from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Final, List, Optional, Sequence, Tuple, Union

from trustgraph_legal import __version__

JsonScalar = Optional[Union[str, int, float, bool]]
JsonValue = Union[JsonScalar, List["JsonValue"], Dict[str, "JsonValue"]]
Line = Tuple[int, str]
Rule = Tuple[str, Tuple[str, ...], str, float, str]
RuleRow = Tuple[str, str, Tuple[str, ...], str, float, str]

SCHEMA_VERSION: Final = "trustgraph-legal-field-extraction/v1"
EXTRACTOR_VERSION: Final = "trustgraph_legal.fields@{}".format(__version__)
_TEXT: Final = "text"
_AMOUNT: Final = "amount"
_INTEREST: Final = "interest"


@dataclass(frozen=True)
class DocumentInput:
    document_id: str
    document_type: str
    source_ref: str
    text: str


@dataclass(frozen=True)
class ExtractedField:
    document_id: str
    document_type: str
    name: str
    normalized_value: str
    confidence: float
    source_ref: str
    chunk_id: str
    line_start: int
    line_end: int
    reason: str

    def to_json(self) -> Dict[str, JsonValue]:
        return {
            "document_id": self.document_id,
            "document_type": self.document_type,
            "name": self.name,
            "normalized_value": self.normalized_value,
            "confidence": self.confidence,
            "source_ref": self.source_ref,
            "chunk_id": self.chunk_id,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class FieldExtractionResult:
    document_id: str
    document_type: str
    review_status: str
    confidence: float
    fields: Tuple[ExtractedField, ...]
    review_reason: Optional[str] = None

    def to_json(self) -> Dict[str, JsonValue]:
        payload: Dict[str, JsonValue] = {
            "document_id": self.document_id,
            "document_type": self.document_type,
            "review_status": self.review_status,
            "confidence": self.confidence,
            "extractor_version": EXTRACTOR_VERSION,
            "fields": [field.to_json() for field in self.fields],
            "pii_profile": {
                "raw_text_included": False,
                "redaction_status": "redacted-output",
            },
        }
        if self.review_reason is not None:
            payload["review_reason"] = self.review_reason
        return payload


@dataclass(frozen=True)
class FieldEvidencePayload:
    documents: Tuple[FieldExtractionResult, ...]

    @property
    def schema_version(self) -> str:
        return SCHEMA_VERSION

    def to_json(self) -> Dict[str, JsonValue]:
        return {
            "schema_version": self.schema_version,
            "documents": [document.to_json() for document in self.documents],
        }


class ManifestFormatError(Exception):
    def __init__(self, manifest_path: Path, detail: str) -> None:
        self.manifest_path = manifest_path
        self.detail = detail
        super().__init__()

    def __str__(self) -> str:
        return "{}: {}".format(self.manifest_path, self.detail)


_CANONICAL_TYPES: Final = ("attachment-collection-order", "payment-order", "service-finality-proof", "assignment-succession", "identity-evidence", "insolvency-credit-recovery", "asset-evidence", "ledger-recovery", "amount-interest-calculation", "unknown")
_TYPE_ALIASES: Dict[str, str] = {name: name for name in _CANONICAL_TYPES}
_TYPE_ALIASES.update(
    {
        "attachment_collection_order": "attachment-collection-order",
        "judgment_payment_order": "payment-order",
        "payment_order": "payment-order",
        "service_finality_execution_clause": "service-finality-proof",
        "assignment_succession": "assignment-succession",
        "identity_evidence": "identity-evidence",
        "insolvency_credit_recovery": "insolvency-credit-recovery",
        "asset_evidence": "asset-evidence",
        "operational_ledger": "ledger-recovery",
        "amount_interest": "amount-interest-calculation",
        "unknown_doc_type": "unknown",
    }
)
_AMOUNT_RE: Final = re.compile(r"\bKRW\s*([0-9][0-9,]*)\b", re.IGNORECASE)
_INTEREST_RE: Final = re.compile(
    r"\b([0-9]+(?:\.[0-9]+)?)\s*percent\s+per\s+year\b", re.IGNORECASE
)
_NATIONAL_ID_RE: Final = re.compile(r"\b\d{6}-\d{7}\b")
_PHONE_RE: Final = re.compile(r"\b(?:\+82[-.\s]?)?0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}\b")
_ACCOUNT_RE: Final = re.compile(
    r"(?i)\b(?:account|bank|계좌|은행|입금|송금)[^\n\r]{0,24}?"
    r"\d{2,6}[-.\s]\d{2,6}[-.\s]\d{2,8}\b"
)
_RULE_TEXT: Final = (
    "attachment-collection-order|court_identifier|Court|text|0.88|Court;attachment-collection-order|court_case_number|Case number|text|0.95|Case number;attachment-collection-order|creditor_role|Creditor|text|0.93|Creditor;attachment-collection-order|debtor_role|Debtor|text|0.93|Debtor;attachment-collection-order|third_party_debtor_role|Third-party debtor|text|0.92|Third-party debtor;attachment-collection-order|claim_amount|Claim amount|amount|0.94|Claim amount;attachment-collection-order|attachment_target|Attachment target|text|0.9|Attachment target;"
    "payment-order|court_identifier|Court|text|0.88|Court;payment-order|court_case_number|Case number|text|0.95|Case number;payment-order|creditor_role|Claimant|text|0.93|Claimant;payment-order|debtor_role|Respondent|text|0.93|Respondent;payment-order|principal_amount|Principal|amount|0.95|Principal;payment-order|interest_rate|Delayed damages|interest|0.9|Delayed damages;"
    "service-finality-proof|court_identifier|Court|text|0.88|Court;service-finality-proof|linked_title_case_number|Linked title|text|0.94|Linked title;service-finality-proof|served_party_role|Served party|text|0.92|Served party;service-finality-proof|service_result|Service result|text|0.94|Service result;service-finality-proof|finality_result|Finality result|text|0.94|Finality result;service-finality-proof|execution_clause_status|Execution clause|text|0.94|Execution clause;"
    "assignment-succession|assignor_role|Assignor|text|0.92|Assignor;assignment-succession|assignee_role|Assignee|text|0.92|Assignee;assignment-succession|debtor_role|Debtor|text|0.9|Debtor;assignment-succession|assigned_claim_token|Assigned claim|text|0.94|Assigned claim;assignment-succession|notice_status|Notice status|text|0.9|Notice status;assignment-succession|succession_authority|Succession authority|text|0.88|Succession authority;"
    "identity-evidence|identity_subject_role|Subject|text|0.88|Subject;identity-evidence|organization_role|Organization|text|0.88|Organization;identity-evidence|party_identity_key|normalized name token,birth date token|text|0.91|Identity token;identity-evidence|organization_status|registration status|text|0.9|Registration status;identity-evidence|representative_role|representative role|text|0.87|Representative role;"
    "insolvency-credit-recovery|insolvency_subject_role|Subject|text|0.88|Subject;insolvency-credit-recovery|procedure_type|Procedure type|text|0.92|Procedure type;insolvency-credit-recovery|procedure_status|Procedure state|text|0.92|Procedure state;insolvency-credit-recovery|authority_ref|Court or agency|text|0.88|Court or agency;insolvency-credit-recovery|linked_claim_token|Linked claim|text|0.92|Linked claim;"
    "asset-evidence|asset_subject_role|Subject|text|0.86|Subject;asset-evidence|asset_class|Asset type|text|0.9|Asset type;asset-evidence|asset_evidence_source|Evidence source|text|0.88|Evidence source;asset-evidence|priority_status|Priority note|text|0.86|Priority note;asset-evidence|attachment_suitability|Attachment suitability|text|0.86|Attachment suitability;"
    "amount-interest-calculation|principal_amount|Principal|amount|0.95|Principal;amount-interest-calculation|interest_rate|Interest basis|interest|0.92|Interest basis;amount-interest-calculation|calculation_start|Calculation start|text|0.9|Calculation start;amount-interest-calculation|calculation_end|Calculation end|text|0.9|Calculation end;amount-interest-calculation|claimed_total|Claimed total|amount|0.94|Claimed total"
)
_RULE_ROWS: Final = tuple(
    (parts[0], parts[1], tuple(parts[2].split(",")), parts[3], float(parts[4]), parts[5])
    for parts in (row.split("|") for row in _RULE_TEXT.split(";"))
)


def normalize_document_type(document_type: str) -> str:
    return _TYPE_ALIASES.get(document_type.strip().lower(), "unknown")


def extract_fields(document: DocumentInput) -> FieldExtractionResult:
    canonical_type = normalize_document_type(document.document_type)
    lines = tuple(enumerate(document.text.splitlines(), start=1))
    fields = _extract_rule_fields(document, canonical_type, lines)
    if canonical_type == "ledger-recovery":
        fields.extend(_extract_ledger(document, canonical_type, lines))
    if canonical_type == "asset-evidence":
        fields.extend(_extract_asset_review(document, canonical_type, lines))
    if not fields:
        return FieldExtractionResult(
            document.document_id, canonical_type, "needs_review", 0.0, (),
            "low_signal_no_supported_fields",
        )
    confidence = round(sum(field.confidence for field in fields) / len(fields), 2)
    return FieldExtractionResult(document.document_id, canonical_type, "accepted", confidence, tuple(fields))


def extract_manifest_fields(manifest_path: Path, repo_root: Optional[Path] = None) -> FieldEvidencePayload:
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("documents"), list):
        raise ManifestFormatError(manifest_path, "missing documents list")
    root = repo_root if repo_root is not None else manifest_path.parents[3]
    return FieldEvidencePayload(tuple(_extract_manifest_document(entry, root, manifest_path) for entry in raw["documents"]))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python3 -m trustgraph_legal.fields")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--repo-root", default=".")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    payload = extract_manifest_fields(Path(args.manifest), Path(args.repo_root))
    evidence_path = Path(args.evidence)
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(payload.to_json(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"documents": len(payload.documents), "evidence": str(evidence_path)}))
    return 0


def _extract_manifest_document(entry: JsonValue, repo_root: Path, manifest_path: Path) -> FieldExtractionResult:
    if not isinstance(entry, dict):
        raise ManifestFormatError(manifest_path, "document entry has invalid shape")
    document_id = entry.get("document_id")
    document_type = entry.get("document_type")
    fixture_path = entry.get("source_fixture_path")
    if not isinstance(document_id, str) or not isinstance(document_type, str) or not isinstance(fixture_path, str):
        raise ManifestFormatError(manifest_path, "document entry has invalid shape")
    path = repo_root / fixture_path
    return extract_fields(DocumentInput(document_id, document_type, "fixture:{}".format(fixture_path), path.read_text(encoding="utf-8")))


def _extract_rule_fields(document: DocumentInput, canonical_type: str, lines: Tuple[Line, ...]) -> List[ExtractedField]:
    fields: List[ExtractedField] = []
    for line in lines:
        for rule_doc_type, name, labels, mode, confidence, reason in _RULE_ROWS:
            if rule_doc_type != canonical_type:
                continue
            value = _labeled_value(line[1], labels)
            if value is not None:
                fields.append(_field(document, canonical_type, name, value, mode, confidence, line, reason))
    return fields


def _field(
    document: DocumentInput, canonical_type: str, name: str, value: str,
    mode: str, confidence: float, line: Line, reason: str,
) -> ExtractedField:
    return ExtractedField(
        document.document_id, canonical_type, name, _normalize_value(value, mode),
        confidence, document.source_ref, "line-{}".format(line[0]), line[0], line[0],
        "matched {} field".format(reason),
    )


def _labeled_value(line: str, labels: Tuple[str, ...]) -> Optional[str]:
    stripped = line.lstrip("- ").strip()
    for label in labels:
        prefix = "{}:".format(label)
        if stripped.lower().startswith(prefix.lower()):
            return stripped[len(prefix):].strip()
    return None


def _normalize_value(value: str, mode: str) -> str:
    if mode == _AMOUNT:
        match = _AMOUNT_RE.search(value)
        return _safe_text(value) if match is None else "KRW {}".format(match.group(1).replace(",", ""))
    if mode == _INTEREST:
        match = _INTEREST_RE.search(value)
        return _safe_text(value) if match is None else "{}% per_year".format(match.group(1))
    return _safe_text(value)


def _safe_text(value: str) -> str:
    redacted = _NATIONAL_ID_RE.sub("[NATIONAL_ID_REDACTED]", value.strip())
    redacted = _PHONE_RE.sub("[PHONE_REDACTED]", redacted)
    redacted = _ACCOUNT_RE.sub("[ACCOUNT_REDACTED]", redacted)
    return " ".join(redacted.split())


def _extract_ledger(document: DocumentInput, canonical_type: str, lines: Tuple[Line, ...]) -> List[ExtractedField]:
    fields: List[ExtractedField] = []
    for line in lines:
        segments = _ledger_segments(line[1])
        event = segments.get("event")
        amount = segments.get("amount")
        if event is not None:
            fields.append(_field(document, canonical_type, "ledger_event", event, _TEXT, 0.86, line, "Ledger event"))
        if amount is not None and event == "partial recovery":
            fields.append(_field(document, canonical_type, "recovery_amount", amount, _AMOUNT, 0.88, line, "Recovery amount"))
        if amount is not None and event == "filing cost":
            fields.append(_field(document, canonical_type, "cost_amount", amount, _AMOUNT, 0.87, line, "Cost amount"))
    return fields


def _ledger_segments(line: str) -> Dict[str, str]:
    if "event:" not in line:
        return {}
    pairs: Dict[str, str] = {}
    for part in line.lstrip("- ").split(";"):
        key, separator, value = part.partition(":")
        if separator:
            pairs[key.strip().lower()] = value.strip()
    return pairs


def _extract_asset_review(document: DocumentInput, canonical_type: str, lines: Tuple[Line, ...]) -> List[ExtractedField]:
    for line in lines:
        if "Exemption, priority, and ownership uncertainty" in line[1]:
            return [_field(document, canonical_type, "exemption_review_status", "explicit review required", _TEXT, 0.84, line, "Exemption review")]
    return []


if __name__ == "__main__":
    raise SystemExit(main())
