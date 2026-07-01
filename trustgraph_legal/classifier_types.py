from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, unique
from typing import Dict, Final, List, Tuple, Union

from trustgraph_legal import __version__

JsonScalar = Union[str, int, float, bool, type(None)]
JsonValue = Union[JsonScalar, List["JsonValue"], Dict[str, "JsonValue"]]
SignalSpec = Tuple[str, str, float]
RuleSpec = Tuple["FixtureBucket", Tuple[SignalSpec, ...]]

SCHEMA_VERSION: Final = "trustgraph-legal-document-classifier/v1"
EXTRACTOR_VERSION: Final = f"trustgraph_legal.classifier@{__version__}"
ONTOLOGY_VERSION: Final = "recova-debt-collection@v0"
PROMPT_VERSION: Final = "legal-ontology-extraction@v0"
UNKNOWN_CONFIDENCE_CEILING: Final = 0.49
MIN_CLASSIFICATION_SCORE: Final = 4.0


@unique
class FixtureBucket(str, Enum):
    ATTACHMENT_COLLECTION_ORDER = "attachment_collection_order"
    JUDGMENT_PAYMENT_ORDER = "judgment_payment_order"
    SERVICE_FINALITY_EXECUTION_CLAUSE = "service_finality_execution_clause"
    ASSIGNMENT_SUCCESSION = "assignment_succession"
    IDENTITY_EVIDENCE = "identity_evidence"
    INSOLVENCY_CREDIT_RECOVERY = "insolvency_credit_recovery"
    ASSET_EVIDENCE = "asset_evidence"
    OPERATIONAL_LEDGER = "operational_ledger"
    AMOUNT_INTEREST = "amount_interest"
    UNKNOWN_DOC_TYPE = "unknown_doc_type"


@unique
class CanonicalDocumentType(str, Enum):
    ATTACHMENT_COLLECTION_ORDER = "attachment-collection-order"
    PAYMENT_ORDER = "payment-order"
    SERVICE_FINALITY_PROOF = "service-finality-proof"
    ASSIGNMENT_SUCCESSION = "assignment-succession"
    IDENTITY_EVIDENCE = "identity-evidence"
    INSOLVENCY_CREDIT_RECOVERY = "insolvency-credit-recovery"
    ASSET_EVIDENCE = "asset-evidence"
    LEDGER_RECOVERY = "ledger-recovery"
    AMOUNT_INTEREST_CALCULATION = "amount-interest-calculation"
    UNKNOWN = "unknown"


@unique
class ReviewStatus(str, Enum):
    CLASSIFIED = "classified"
    NEEDS_REVIEW_UNKNOWN_DOC_TYPE = "needs_review_unknown_doc_type"


FIXTURE_BUCKET_TO_DOCUMENT_TYPE: Final[Dict[FixtureBucket, CanonicalDocumentType]] = {
    FixtureBucket.ATTACHMENT_COLLECTION_ORDER: CanonicalDocumentType.ATTACHMENT_COLLECTION_ORDER,
    FixtureBucket.JUDGMENT_PAYMENT_ORDER: CanonicalDocumentType.PAYMENT_ORDER,
    FixtureBucket.SERVICE_FINALITY_EXECUTION_CLAUSE: CanonicalDocumentType.SERVICE_FINALITY_PROOF,
    FixtureBucket.ASSIGNMENT_SUCCESSION: CanonicalDocumentType.ASSIGNMENT_SUCCESSION,
    FixtureBucket.IDENTITY_EVIDENCE: CanonicalDocumentType.IDENTITY_EVIDENCE,
    FixtureBucket.INSOLVENCY_CREDIT_RECOVERY: CanonicalDocumentType.INSOLVENCY_CREDIT_RECOVERY,
    FixtureBucket.ASSET_EVIDENCE: CanonicalDocumentType.ASSET_EVIDENCE,
    FixtureBucket.OPERATIONAL_LEDGER: CanonicalDocumentType.LEDGER_RECOVERY,
    FixtureBucket.AMOUNT_INTEREST: CanonicalDocumentType.AMOUNT_INTEREST_CALCULATION,
    FixtureBucket.UNKNOWN_DOC_TYPE: CanonicalDocumentType.UNKNOWN,
}


@dataclass(frozen=True)
class EvidenceSpan:
    source_ref: str
    start: int
    end: int
    excerpt: str
    signal: str

    def to_json(self) -> Dict[str, JsonValue]:
        return {
            "source_ref": self.source_ref,
            "start": self.start,
            "end": self.end,
            "excerpt": self.excerpt,
            "signal": self.signal,
        }


@dataclass(frozen=True)
class ClassificationResult:
    document_id: str
    document_type: CanonicalDocumentType
    fixture_document_type: FixtureBucket
    confidence: float
    review_status: ReviewStatus
    evidence_spans: Tuple[EvidenceSpan, ...]
    reason_signals: Tuple[str, ...]
    pii_counts: Dict[str, int]

    def to_json(self) -> Dict[str, JsonValue]:
        return {
            "document_id": self.document_id,
            "document_type": self.document_type.value,
            "fixture_document_type": self.fixture_document_type.value,
            "confidence": self.confidence,
            "review_status": self.review_status.value,
            "reason_signals": list(self.reason_signals),
            "evidence_spans": [span.to_json() for span in self.evidence_spans],
            "source_refs": sorted({span.source_ref for span in self.evidence_spans}),
            "ocr_version": "MinerU@legal_ocr_20260630",
            "extractor_version": EXTRACTOR_VERSION,
            "ontology_version": ONTOLOGY_VERSION,
            "prompt_version": PROMPT_VERSION,
            "pii_profile": {
                "redacted": self.pii_counts,
                "raw_text_included": False,
            },
        }


@dataclass(frozen=True)
class ClassificationPayload:
    records: Tuple[ClassificationResult, ...]

    def to_json(self) -> Dict[str, JsonValue]:
        unknown_count = sum(
            1
            for record in self.records
            if record.document_type is CanonicalDocumentType.UNKNOWN
        )
        return {
            "schema_version": SCHEMA_VERSION,
            "summary": {
                "records": len(self.records),
                "classified": len(self.records) - unknown_count,
                "unknown_doc_type": unknown_count,
            },
            "records": [record.to_json() for record in self.records],
        }


@dataclass(frozen=True)
class RuleMatch:
    fixture_bucket: FixtureBucket
    score: float
    evidence_spans: Tuple[EvidenceSpan, ...]
    reason_signals: Tuple[str, ...]


@dataclass(frozen=True)
class ManifestDocument:
    document_id: str
    source_fixture_path: str


@dataclass(frozen=True)
class RedactionResult:
    text: str
    counts: Dict[str, int]


class ClassifierInputError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__()

    def __str__(self) -> str:
        return self.message
