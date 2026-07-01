from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional, Sequence

from trustgraph_legal.classifier_manifest import classify_manifest
from trustgraph_legal.classifier_rules import RULES, classify_text
from trustgraph_legal.classifier_types import (
    FIXTURE_BUCKET_TO_DOCUMENT_TYPE,
    ONTOLOGY_VERSION,
    PROMPT_VERSION,
    SCHEMA_VERSION,
    CanonicalDocumentType,
    ClassificationPayload,
    ClassificationResult,
    ClassifierInputError,
    EvidenceSpan,
    FixtureBucket,
    JsonScalar,
    JsonValue,
    ManifestDocument,
    RedactionResult,
    ReviewStatus,
    RuleMatch,
    RuleSpec,
    SignalSpec,
)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -m trustgraph_legal.classifier",
        description="Classify PII-safe legal OCR markdown fixtures.",
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--evidence", required=True)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    manifest_path = Path(args.manifest)
    evidence_path = Path(args.evidence)
    payload = classify_manifest(manifest_path)
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        json.dumps(payload.to_json(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "records": len(payload.records),
                "unknown_doc_type": sum(
                    1
                    for record in payload.records
                    if record.document_type is CanonicalDocumentType.UNKNOWN
                ),
                "evidence": str(evidence_path),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


__all__ = [
    "FIXTURE_BUCKET_TO_DOCUMENT_TYPE",
    "ONTOLOGY_VERSION",
    "PROMPT_VERSION",
    "RULES",
    "SCHEMA_VERSION",
    "CanonicalDocumentType",
    "ClassificationPayload",
    "ClassificationResult",
    "ClassifierInputError",
    "EvidenceSpan",
    "FixtureBucket",
    "JsonScalar",
    "JsonValue",
    "ManifestDocument",
    "RedactionResult",
    "ReviewStatus",
    "RuleMatch",
    "RuleSpec",
    "SignalSpec",
    "build_parser",
    "classify_manifest",
    "classify_text",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
