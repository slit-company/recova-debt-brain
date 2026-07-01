# C Classifier Contract Review

Member: C, classifier-contract-review
Worktree: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debt-collection-ontology-todo-5-20260630/worktrees/C`
Scope: read-only acceptance and risk review for Todo 5. No production files edited.

## Sources Reviewed

- `/Users/cosmos/dev/ontology/trustgraph/.omo/plans/debt-collection-ontology.md`, Todo 5.
- `docs/product/debt-collection-ontology/domain-contract.md`.
- `tests/fixtures/legal-ocr/manifest.json`.
- `tests/fixtures/legal-ocr/snippets/*.md`.
- `trustgraph_legal/ingest.py`, `trustgraph_legal/registry.py`, `trustgraph_legal/pii.py`.
- Existing tests under `tests/unit/legal_ontology/`.
- A/B branch state read-only.

## Executive Findings

1. Highest acceptance risk: label dialect mismatch. The domain contract uses hyphenated canonical document type IDs such as `attachment-collection-order` and `amount-interest-calculation`; the fixture manifest uses snake_case labels such as `attachment_collection_order`; A's draft test expects snake_case plus `unknown_doc_type`. A/B should settle this explicitly before final commit. My recommendation is to emit one canonical `document_type` contract value and, if needed, keep manifest compatibility in a separate `source_category` or `fixture_label` field.
2. Todo 5 must prove more than fixture label matching. It requires confidence, review state, source-backed evidence spans, unknown-document behavior, normalized extracted fields, and PII-safe evidence JSON.
3. The nine fixture snippets cover the current synthetic subset, not the full domain-contract document type list. Acceptance should state that v0 implements the Todo 5 buckets over the current manifest and routes unsupported contract types to review instead of pretending full domain coverage.
4. `trustgraph_legal/registry.py` already emits registry metadata, PII counts, provenance, tags, and hybrid evidence keys, but it does not produce Todo 5 `document_type`, classifier evidence spans, or normalized extracted fields. Todo 5 should layer on this cleanly without weakening registry redaction.
5. A/B committed pass/fail review is still pending because no A or B branch currently has committed Todo 5 diffs.

## Todo 5 Acceptance Checklist

### Classification Labels

- Every manifest document produces exactly one primary `document_type`.
- The output schema defines the label dialect. Prefer domain-contract IDs, or document an explicit compatibility mapping if fixture snake_case labels remain.
- Covered v0 fixture buckets:
  - attachment/collection order.
  - payment order or judgment.
  - service, finality, and execution clause.
  - assignment and succession.
  - identity evidence.
  - insolvency, discharge, or credit recovery.
  - asset evidence and attachment target or priority.
  - operational ledger.
  - amount and interest calculation.
- Unsupported or ambiguous contract types, including application-only attachment documents or legal rule sources, must not be forced into a nearest bucket. They should produce an unknown/review path.

### Confidence

- Each classification and each extracted material field has a numeric confidence score.
- Each material assertion also has a confidence level or review reason, because the domain contract says confidence is not a float alone.
- Thresholds are deterministic and documented. Example acceptance shape: high-confidence fixture labels above the classification threshold; low-signal unknown below the threshold.
- LLM-assisted behavior, if present, must be deterministic in tests: fixed fixture inputs, no live network dependency, stable output order, and stable version fields.

### Review Status

- Classified fixture documents receive an explicit success status such as `classified`.
- Low-confidence or ambiguous classifications receive a review status that makes the governance path machine-readable.
- Unknown classifications map to the domain queue concept `unknown-document-type`, even if the local result field is named `unknown_doc_type`.
- Missing critical fields should not be hidden by a successful document classification. They should produce field-level review status or low-confidence extraction records.

### Evidence and Source Spans

- Every document classification includes non-empty evidence signals and source spans.
- Every extracted material field includes one or more source spans or an explicit reviewed/derived-rule source.
- A source span should include at minimum: `source_ref` or fixture path, line or character offsets, redacted snippet text, and the signal or field it supports.
- Source spans must survive JSON serialization and CLI evidence output.
- Source spans that contain sensitive shapes must be redacted before they leave the extractor.

### Unknown Document Failure Behavior

- A low-signal markdown sample must not receive a confident nearest-neighbor label.
- The result should include:
  - unknown document type marker.
  - confidence below the classification threshold.
  - review status for unknown document type.
  - reason signal such as insufficient document type evidence.
  - at least one safe source span or source reference showing what was reviewed.
- Unknown output should be queue-ready for later governance work, but Todo 5 does not need to implement the full queue mutation if that belongs to Todo 8.

### Field Normalization

- Amounts normalize into numeric value plus currency, not only raw strings.
- Interest rates normalize consistently, with basis and period fields preserved when present.
- Date-like values preserve redacted placeholders safely and should not invent exact dates.
- Party and role fields preserve role context: creditor, debtor, third-party debtor, assignor, assignee, court, authority, asset holder.
- Case, claim, title, and identity references use hashed or placeholder-safe keys. Name-only merge evidence is not acceptable.
- Asset fields keep asset class, holder/owner context, priority/exemption uncertainty, and review flags separate.
- Ledger fields keep event type, amount, status, and row source separate from legal authority facts.
- Missing optional fields should be represented as absent or field-level unknown, not fabricated.

### PII Safety

- Evidence JSON must not include raw OCR text or unredacted sensitive identifiers.
- `pii_profile.raw_text_included` should remain false in classifier and extractor outputs.
- Report, evidence, logs, and fixtures should pass a sensitive-pattern scan.
- Source span text must pass through redaction before serialization.
- Existing registry redaction covers common sensitive shapes; Todo 5 should not bypass it by embedding raw snippets.

### Deterministic v0 Boundary

- The v0 classifier should be deterministic over the fixture manifest.
- Output order should be stable, ideally manifest order or sorted source path order.
- Version fields should include extractor, ontology, prompt, OCR, and schema versions where relevant.
- The classifier/extractor must avoid final legal conclusions. It only emits typed facts, evidence, confidence, and review states.

### Combined Test and Integration Expectations

- Required focused command: `pytest tests/unit/legal_ontology/test_document_classifier.py tests/unit/legal_ontology/test_field_extractors.py -q`.
- Classifier manifest run should write the Todo 5 evidence JSON path and validate as JSON.
- Field extraction tests should consume classifier-compatible document records or fixture files and assert normalized fields plus source spans.
- Combined behavior should prove at least one fixture can flow from classification into field extraction without losing `document_id`, `source_hash`, `source_path_ref`, `case_packet_id` or source refs.
- Failure tests should cover low-signal unknown classification and low-confidence or missing critical field extraction.
- PII scan should run against generated evidence JSON and the report artifacts.

## Risks and Gaps for A/B

1. Label mapping is currently underspecified across plan, domain contract, manifest, and A draft test. This can cause green tests that still violate the contract.
2. The domain contract includes document types not represented by current snippets. Tests should not imply full coverage beyond the Todo 5 fixture subset.
3. Confidence needs both score and reason/level. A score alone is not enough for downstream StopGate and governance behavior.
4. Evidence spans need clear semantics. "Evidence present" is too weak unless tests assert source reference, offset or line location, and redacted snippet text.
5. Field extraction must not infer legal facts from document type alone. Material facts need their own spans or explicit unknown/review status.
6. Unknown classification should not be named only for a local test. It must map cleanly to the domain `unknown-document-type` review path.
7. Existing registry JSON uses `review_status: pending_registry_review` and `confidence: 1.0` for registry metadata. Todo 5 classifier confidence should not be conflated with registry confidence.
8. PII risk is mostly evidence output, not fixture content. Serializing full source text into spans would violate the domain contract even if tests pass.
9. A/B should avoid changing manifest fixtures to make tests easy. The fixture manifest is acceptance input, not implementation-owned data for this todo.
10. B currently has no visible field-extractor branch diff. If B lands late, integration risk is schema mismatch between classifier records and field extraction inputs.

## A/B Read-Only Branch Notes

### Branch A: `team/debt-collection-ontology-todo-5-20260630/A`

- No committed diff from `master` at review time.
- Worktree status shows one untracked draft file:
  - `tests/unit/legal_ontology/test_document_classifier.py`
- Draft test strengths:
  - Covers manifest classification, confidence, review status, evidence spans, PII-safe JSON, low-signal unknown behavior, and module CLI.
  - Includes a subprocess module entrypoint check.
- Draft test gaps or risks:
  - Expects manifest snake_case labels, not domain-contract hyphenated IDs.
  - Imports `trustgraph_legal.classifier`, which is not present in the visible A worktree file list yet.
  - Does not assert source span location semantics beyond non-empty spans.
  - Does not prove integration with field extraction.
- Pass/fail note: no committed implementation to evaluate yet. The draft test would require a classifier module before it can pass.

### Branch B: `team/debt-collection-ontology-todo-5-20260630/B`

- No committed diff from `master` at review time.
- Worktree status is clean.
- No visible `trustgraph_legal/fields.py` or `tests/unit/legal_ontology/test_field_extractors.py` yet.
- Pass/fail note: field extraction implementation and tests are pending from this review perspective.

## Required Status Snapshot

### C worktree `git status --short`

```text

```

Interpretation: clean before report artifact write.

### Main checkout `git status --short`

```text
?? .omo/
```

Interpretation: the team metadata/artifacts directory is untracked in the main checkout.

### A worktree `git status --short`

```text
?? tests/unit/legal_ontology/test_document_classifier.py
```

### B worktree `git status --short`

```text

```

## C Verification Completed

- Artifact existence check passed for `artifacts/C-classifier-contract-review.md`.
- Sensitive-pattern scan over this report returned no findings.
- Fresh C worktree status after report write remained clean.
- Fresh main checkout status after report write still showed `?? .omo/`.

## Recommended Final Verification Once A/B Commit

1. Run `pytest tests/unit/legal_ontology/test_document_classifier.py tests/unit/legal_ontology/test_field_extractors.py -q`.
2. Run classifier evidence generation over `tests/fixtures/legal-ocr/manifest.json` and validate the output with `python3 -m json.tool`.
3. Run a low-signal unknown markdown through the classifier and assert review status, low confidence, reason signal, and safe source reference.
4. Run field extraction over all nine snippets and assert normalized amounts, rates, roles, status fields, asset/priority flags, ledger rows, and source spans.
5. Scan generated evidence and this report for sensitive patterns before handoff.
6. Inspect A/B diffs against `master` after commits appear and verify the committed code matches this checklist, not only the draft test shape.
