# A Document Classifier Report

Member: A, document-classifier
Worktree: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debt-collection-ontology-todo-5-20260630/worktrees/A`
Branch: `team/debt-collection-ontology-todo-5-20260630/A`
Commits:

- `3ba6e641 feat(legal-extract): add document classifier`
- `dd4a55fa fix(legal-extract): support python 3.8 classifier syntax`

## Implemented

- Added `trustgraph_legal/classifier.py` deterministic v0 classifier.
- Added `tests/unit/legal_ontology/test_document_classifier.py`.
- Classifier output serializes canonical ontology/domain-boundary `document_type` values and preserves manifest compatibility separately as `fixture_document_type`.
- Low-signal text emits canonical `document_type: "unknown"`, `fixture_document_type: "unknown_doc_type"`, confidence below threshold, evidence span, and `review_status: "needs_review_unknown_doc_type"`.
- Follow-up compatibility commit replaced `StrEnum`, PEP 604 runtime aliases, and `dataclass(slots=True)` usage so the classifier syntax/import path works with the repo's Python `>=3.8` baseline.
- CLI entrypoint works:
  `python3 -m trustgraph_legal.classifier --manifest tests/fixtures/legal-ocr/manifest.json --evidence .omo/evidence/debt-collection-ontology/task-5-classifier.json`

## Fixture Bucket Mapping

| Fixture bucket | Canonical `document_type` |
| --- | --- |
| `attachment_collection_order` | `attachment-collection-order` |
| `judgment_payment_order` | `payment-order` |
| `service_finality_execution_clause` | `service-finality-proof` |
| `assignment_succession` | `assignment-succession` |
| `identity_evidence` | `identity-evidence` |
| `insolvency_credit_recovery` | `insolvency-credit-recovery` |
| `asset_evidence` | `asset-evidence` |
| `operational_ledger` | `ledger-recovery` |
| `amount_interest` | `amount-interest-calculation` |
| `unknown_doc_type` | `unknown` |

Unsupported domain-contract document types remain `unknown`/review until future fixtures and deterministic rules cover them.

## Evidence Summary

Happy QA evidence path:
`/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debt-collection-ontology-todo-5-20260630/worktrees/A/.omo/evidence/debt-collection-ontology/task-5-classifier.json`

Generated summary:

```json
{
  "records": 9,
  "classified": 9,
  "unknown_doc_type": 0
}
```

All nine fixture records include:

- `document_id`
- canonical `document_type`
- source manifest `fixture_document_type`
- numeric `confidence`
- `review_status`
- `reason_signals`
- non-empty `evidence_spans`
- `source_refs`
- version fields
- `pii_profile.raw_text_included: false`

## Verification

Initial A worktree status before edits:

```text
## team/debt-collection-ontology-todo-5-20260630/A
```

Focused tests:

```text
python3 -m pytest tests/unit/legal_ontology/test_document_classifier.py -q
6 passed in 0.10s
```

Happy QA:

```text
python3 -m trustgraph_legal.classifier --manifest tests/fixtures/legal-ocr/manifest.json --evidence .omo/evidence/debt-collection-ontology/task-5-classifier.json
{"evidence": ".omo/evidence/debt-collection-ontology/task-5-classifier.json", "records": 9, "unknown_doc_type": 0}
```

Failure QA:

```json
{
  "confidence": 0.0,
  "document_type": "unknown",
  "evidence_spans": 1,
  "exit_code": 0,
  "fixture_document_type": "unknown_doc_type",
  "review_status": "needs_review_unknown_doc_type"
}
```

PII scan:

```text
sensitive-pattern scan over classifier source, classifier tests, and generated evidence JSON
```

Result: no findings.

Compile:

```text
python3 -m py_compile trustgraph_legal/classifier.py tests/unit/legal_ontology/test_document_classifier.py
/usr/bin/python3 -m py_compile trustgraph_legal/classifier.py tests/unit/legal_ontology/test_document_classifier.py
```

Result: both passed. `/usr/bin/python3 --version` reported `Python 3.9.6`.

Baseline compatibility smoke:

```text
/usr/bin/python3 -m trustgraph_legal.classifier --manifest tests/fixtures/legal-ocr/manifest.json --evidence /tmp/task-5-classifier-py39.json
{"evidence": "/tmp/task-5-classifier-py39.json", "records": 9, "unknown_doc_type": 0}
```

Diff checks:

```text
git diff --cached --check
git diff --check HEAD~1 HEAD
```

Result: both passed for the initial classifier commit and the follow-up compatibility commit.

## Status Snapshots

A worktree status after commit:

```text
## team/debt-collection-ontology-todo-5-20260630/A
?? .omo/
```

Main checkout status after commit:

```text
## master...origin/master [ahead 10]
?? .omo/
```

The A worktree `.omo/` entry is generated QA evidence only; it was not staged or committed. The main checkout `.omo/` entry is team metadata/artifacts.

## Notes

- Reviewed C artifact: `artifacts/C-classifier-contract-review.md`.
- C's label dialect risk is addressed by the explicit `FIXTURE_BUCKET_TO_DOCUMENT_TYPE` mapping in `trustgraph_legal/classifier.py`.
- `classifier.py` carries a `SIZE_OK` marker because Todo 5 keeps the classifier API, CLI, JSON contract, and deterministic rule table in the single owned file.
- The earlier Python-version blocker is fixed in `dd4a55fa`; classifier imports no longer depend on `StrEnum`, PEP 604 runtime aliases, or neighboring legal modules that use newer dataclass options.
