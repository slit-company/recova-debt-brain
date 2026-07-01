# B Field Extractors Report

Member: B, field-extractors
Thread: `019f176d-e954-7970-87e7-0e3b1e474c0d` (`codex://threads/019f176d-e954-7970-87e7-0e3b1e474c0d`)
Worktree: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debt-collection-ontology-todo-5-20260630/worktrees/B`
Branch: `team/debt-collection-ontology-todo-5-20260630/B`
Commit: `806c43b0 feat(legal-extract): add field extractors`

## Delivered

- Added `trustgraph_legal/fields.py`.
- Added `tests/unit/legal_ontology/test_field_extractors.py`.
- Generated uncommitted QA evidence at `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debt-collection-ontology-todo-5-20260630/worktrees/B/.omo/evidence/debt-collection-ontology/task-5-fields.json`.

## Contract Notes

- Fixture snake_case document labels normalize before extraction branching.
- Output document types use canonical v0 labels:
  - `attachment_collection_order` -> `attachment-collection-order`
  - `judgment_payment_order` -> `payment-order`
  - `service_finality_execution_clause` -> `service-finality-proof`
  - `assignment_succession` -> `assignment-succession`
  - `identity_evidence` -> `identity-evidence`
  - `insolvency_credit_recovery` -> `insolvency-credit-recovery`
  - `asset_evidence` -> `asset-evidence`
  - `operational_ledger` -> `ledger-recovery`
  - `amount_interest` -> `amount-interest-calculation`
  - `unknown_doc_type` -> `unknown`
- Every accepted field includes `document_id`, canonical `document_type`, field name, normalized value, confidence, `source_ref`, `chunk_id`, line range, and non-PII reason.
- Low-signal input returns `review_status=needs_review`, `confidence=0.0`, canonical `document_type=unknown`, and no accepted fields.
- The implementation is Python 3.8-parser-compatible. `/opt/homebrew/bin/python3` is Python 3.14.5; `/usr/bin/python3` is Python 3.9.6. The earlier `match` parser error was removed by replacing Python 3.10+ syntax.

## QA Evidence

- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_field_extractors.py -q`: 4 passed.
- `python3 -m pytest tests/unit/legal_ontology/test_field_extractors.py -q`: 4 passed.
- `/opt/homebrew/bin/python3 -m trustgraph_legal.fields --manifest tests/fixtures/legal-ocr/manifest.json --repo-root . --evidence .omo/evidence/debt-collection-ontology/task-5-fields.json`: wrote 9-document evidence JSON.
- `python3 -m json.tool .omo/evidence/debt-collection-ontology/task-5-fields.json`: passed.
- Evidence summary: 9 documents, 52 fields, canonical types `attachment-collection-order`, `payment-order`, `service-finality-proof`, `identity-evidence`, `insolvency-credit-recovery`, `assignment-succession`, `ledger-recovery`, `asset-evidence`, `amount-interest-calculation`.
- `/opt/homebrew/bin/python3` low-signal inline QA: returned `document_type=unknown`, `review_status=needs_review`, `confidence=0.0`, no fields.
- `/usr/bin/python3 -m py_compile trustgraph_legal/fields.py tests/unit/legal_ontology/test_field_extractors.py`: passed.
- `/usr/bin/python3` import smoke: returned `unknown needs_review 0`.
- `python3 -m py_compile trustgraph_legal/fields.py tests/unit/legal_ontology/test_field_extractors.py`: passed.
- Required sensitive-pattern scan over code, tests, and generated evidence: no findings.
- `git diff --cached --check`: passed before commit.
- `git diff --check HEAD~1 HEAD`: passed after commit.

## Isolation Evidence

B worktree status before commit, after unstaging generated evidence:

```text
## team/debt-collection-ontology-todo-5-20260630/B
A  tests/unit/legal_ontology/test_field_extractors.py
A  trustgraph_legal/fields.py
?? .omo/
```

B worktree status after commit:

```text
## team/debt-collection-ontology-todo-5-20260630/B
?? .omo/
```

Main checkout status:

```text
## master...origin/master [ahead 10]
?? .omo/
```

## Commit Contents

```text
806c43b0 (HEAD -> team/debt-collection-ontology-todo-5-20260630/B) feat(legal-extract): add field extractors
 tests/unit/legal_ontology/test_field_extractors.py | 147 ++++++++++
 trustgraph_legal/fields.py                         | 298 +++++++++++++++++++++
 2 files changed, 445 insertions(+)
```

Generated `.omo/` evidence was deliberately not staged or committed per leader correction.
