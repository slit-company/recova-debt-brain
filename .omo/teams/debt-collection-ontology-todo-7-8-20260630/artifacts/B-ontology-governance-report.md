# B Ontology Governance Report

Member: B `ontology-governance`
Branch: `team/debt-collection-ontology-todo-7-8-20260630/B`

## Implementation

- Added service-side governance workflow modules:
  - `trustgraph_legal/governance.py`
  - `trustgraph_legal/governance_models.py`
  - `trustgraph_legal/governance_records.py`
  - `trustgraph_legal/governance_sources.py`
- Added focused tests:
  - `tests/unit/legal_ontology/test_ontology_governance.py`
- Governance processing emits:
  - ontology candidates for unknown document types and low-confidence fields
  - review queue items for unknown document type, low-confidence extraction, and ontology candidates
  - reprocess plans for each candidate
  - serializable promotion rejection or next-version approval decisions

## Boundary Decision

Todo 8 governance records are service-side records, not ontology graph nodes.
The production ontology JSON remains read-only in this implementation. Candidate
document types, review items, promotion decisions, and reprocess plans are
serialized as governance service records with source refs, risk flags, and
approval metadata requirements.

If a future change promotes these concepts into ontology-backed graph nodes, it
must update `resources/ontologies/recova-debt-collection.json` and the ontology
validator tests in the same change. This B slice intentionally avoids that and
keeps production ontology promotion as an explicit next-version decision.

## Contract Gap Handling

Member C flagged domain-contract document types that are not covered by the
current 9 classifier buckets. This implementation does not silently treat them
as production-supported. It emits explicit `ontology-candidate` review items and
reprocess plans for:

- `attachment-collection-application`
- `judgment-or-decision`
- `attachment-target-priority`
- `legal-rule-source`

Each uses reason
`domain_contract_type_not_production_supported_in_v0_classifier`, risk flag
`classifier-coverage-gap`, and changed version
`ontology_version=proposed:<document-type>`.

## Promotion Safety

Promotion requires all approval and regression metadata:

- `approved_by`
- `approved_at`
- `approval_evidence_ref`
- `regression_run_id`
- `fixture_set_id`
- `changed_versions`
- `regression_result`
- `unresolved_risk_summary`

Promotion without metadata is rejected as
`missing_required_approval_metadata`. Rejections remain serializable for audit
and include missing fields, candidate id, production ontology hash, and
`production_ontology_modified=false`.

## Evidence

- Happy QA evidence:
  `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debt-collection-ontology-todo-7-8-20260630/artifacts/B-governance-happy.json`
  - candidates: 6
  - review items: 6
  - reprocess plans: 6
  - production ontology modified: false
  - unsupported contract types represented: all four listed above
- Failure QA evidence:
  `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debt-collection-ontology-todo-7-8-20260630/artifacts/B-governance-failure.json`
  - status: rejected
  - reason: `missing_required_approval_metadata`
  - production ontology modified: false

## Verification

- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_ontology_governance.py -q`
  - result: 5 passed
- `/usr/bin/python3 -m py_compile trustgraph_legal/governance.py trustgraph_legal/governance_models.py trustgraph_legal/governance_records.py trustgraph_legal/governance_sources.py tests/unit/legal_ontology/test_ontology_governance.py`
  - result: passed
- Happy QA: unknown fixture through `python3 -m trustgraph_legal.governance`
  - result: candidate JSON and governance evidence captured
- Failure QA: promotion without approval metadata
  - result: rejected with serialized audit fields
- Sensitive scan over changed code, tests, and B evidence artifacts:
  - result: passed for resident-id, phone, and account-like patterns

## Notes

- CLI stdout prints counts, candidate ids, review item ids, source refs, and
  evidence path only.
- Governance evidence includes redacted excerpts from classifier output but no
  raw OCR text or raw source text.
- `.omo/` evidence artifacts are intentionally not staged for commit.
