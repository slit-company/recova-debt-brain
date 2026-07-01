# Todo 6 A Case Graph Builder Report

Member: A / case-graph-builder
Worktree: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debt-collection-ontology-todo-6-20260630/worktrees/A`
Branch: `team/debt-collection-ontology-todo-6-20260630/A`

## Implementation

- Added deterministic `trustgraph_legal.case_graph` module and CLI.
- Added focused tests in `tests/unit/legal_ontology/test_case_graph_builder.py`.
- Reused Todo 5 `trustgraph_legal.classifier` and `trustgraph_legal.fields` outputs; no LLM, API, or network calls.
- Primary v0 ontology anchor is `CasePacket` mapped to configured class `case-packet`.
- `Case` appears only as `case_projection` metadata with `derived: true` and `ontology_class: null`; no new `case` ontology class is emitted.
- Role-specific concepts such as creditor, debtor, third-party debtor, assignor, and assignee are packet-scoped `party-role` nodes. `has-party` edges target configured `person-party` or `organization-party` nodes.
- Emitted graph uses configured v0 ontology IDs for nodes and predicates, including `ledger-entry` for LedgerEvent and `cost-entry` for Cost.

## Evidence Keys

The graph emits the exact Todo 6 evidence keys:

- `case_packet_id`: deterministic id from court cases, derived `claim_id`, derived `enforcement_title_id`, and document hashes.
- `court_case_number`: extracted from `court_case_number` and `linked_title_case_number` fields.
- `claim_id`: deterministic id from safe claim/title facts such as assigned/linked claim token, claim amount, principal amount, and court case number, with derivation metadata.
- `enforcement_title_id`: deterministic id from title case, linked title, and execution clause facts, with derivation metadata.
- `party_identity_key`: extracted from the identity fixture when present; otherwise low-confidence/missing identity evidence is explicit.
- `document_hash`: manifest `source_hash` mapped to Todo 6 `document_hash`.

`claim_or_packet_token` is not used as a substitute for `claim_id`.

## Provenance And Safety

- Every non-derived emitted node and edge carries fact-level provenance: `document_id`, `source_ref`, `chunk_id`, `line_start`, `line_end`, `confidence`, `extractor_version`, `source_module`.
- Source pointers prefer field spans and line/chunk metadata; full fixture text is not copied into graph output.
- Similar debtor placeholders without identity evidence remain separate `party-role` nodes and create `identity_uncertain` plus `name_only_without_identity_evidence` review findings.
- Negative or risky fixture facts such as `procedure_status` and `exemption_review_status` become review/legal-check findings rather than high-confidence action facts.
- Graph output sets `pii_profile.raw_text_included=false` and `source_text_included=false`.

## Verification

- Initial A worktree status was clean on `team/debt-collection-ontology-todo-6-20260630/A`.
- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_case_graph_builder.py -q`: passed, 4 tests.
- `python3 -m trustgraph_legal.case_graph --fixtures tests/fixtures/legal-ocr/manifest.json --out .omo/evidence/debt-collection-ontology/task-6-case-graph.json`: passed.
- JSON validation summary: schema `trustgraph-legal-case-graph/v1`, 1 case packet, 9 documents, 116 entities, 117 edges, 2 review items.
- Failure QA is covered by `test_similar_debtors_without_identity_evidence_remain_unresolved`.
- Ontology ID QA is covered by `test_emitted_ontology_ids_are_configured_v0_classes_and_properties`.
- `/usr/bin/python3 -m py_compile trustgraph_legal/case_graph.py tests/unit/legal_ontology/test_case_graph_builder.py`: passed.
- `/usr/bin/python3` import smoke for `trustgraph_legal.case_graph` and the test module: passed.
- Sensitive-pattern scan over owned code, tests, and generated evidence: no findings.
- Pure LOC: `trustgraph_legal/case_graph.py` 249; `tests/unit/legal_ontology/test_case_graph_builder.py` 201.
- `git diff --cached --check` before commit: passed.
- Commit: `48fc3e9a feat(legal-graph): resolve extracted facts into case graphs`.
- `git diff --check HEAD~1 HEAD` after commit: passed.

## Git Status

A worktree status before report write:

```text
## team/debt-collection-ontology-todo-6-20260630/A
?? .omo/
?? tests/unit/legal_ontology/test_case_graph_builder.py
?? trustgraph_legal/case_graph.py
```

Main checkout status:

```text
## master...origin/master [ahead 15]
?? .omo/
```

Generated `.omo/` evidence and this report are intentionally uncommitted and must not be staged in the member commit.

Final A worktree status after commit:

```text
## team/debt-collection-ontology-todo-6-20260630/A
?? .omo/
```
