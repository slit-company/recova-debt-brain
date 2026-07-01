# Todo 6 Case Graph Contract Review

Member: B / case-graph-contract-review
Scope: read-only acceptance and risk review for Todo 6 hybrid case graph resolver
Review time: 2026-06-30

## Inputs Read

- Team guide: `.omo/teams/debt-collection-ontology-todo-6-20260630/guide.md`
- Plan Todo 6: `.omo/plans/debt-collection-ontology.md`
- Domain contract: `docs/product/debt-collection-ontology/domain-contract.md`
- Ontology: `resources/ontologies/recova-debt-collection.json`
- Fixtures: `tests/fixtures/legal-ocr/manifest.json` and `tests/fixtures/legal-ocr/snippets/*.md`
- Existing Todo 5 implementation: `trustgraph_legal/classifier.py`, `trustgraph_legal/fields.py`, `trustgraph_legal/registry.py`
- Existing tests: `tests/unit/legal_ontology/test_document_classifier.py`, `tests/unit/legal_ontology/test_field_extractors.py`, `tests/unit/legal_ontology/test_ingest.py`
- A worktree read-only status and file search

## Review State

This is a pre-implementation review. A worktree `team/debt-collection-ontology-todo-6-20260630/A` had no diff from `master` when inspected, and no `trustgraph_legal/case_graph.py` or `tests/unit/legal_ontology/test_case_graph_builder.py` existed yet.

Status snapshots captured before this report write:

- B worktree: `## team/debt-collection-ontology-todo-6-20260630/B`
- Main checkout: `## master...origin/master [ahead 15]` plus untracked `.omo/`
- A worktree: `## team/debt-collection-ontology-todo-6-20260630/A`

## Contract Baseline

Todo 6 must resolve extracted facts into case-level graph entities and edges for:

- `Case`, `CasePacket`, `Document`, `SourceSpan`
- `Person`, `Organization`, `Creditor`, `Debtor`, `ThirdPartyDebtor`, `Guarantor`, `Successor`
- `Claim`, `Amount`, `EnforcementTitle`, `CourtProcedure`
- `AttachmentTarget`, `Asset`, `LedgerEvent`, `RecoveryTransaction`, `Cost`, `RuleFinding`

The ontology IDs available in `recova-debt-collection@v0` are not a one-to-one PascalCase mirror. A should bind the graph JSON to ontology IDs explicitly:

- `CasePacket` -> `case-packet`; no separate ontology class named `Case` exists, so either omit a distinct Case node or make `Case` a documented projection/wrapper around `case-packet`.
- `Document` -> `legal-document`
- `SourceSpan` -> `source-span`
- `Person` -> `person-party`; `Organization` -> `organization-party`
- Role-specific concepts (`Creditor`, `Debtor`, `ThirdPartyDebtor`, `Guarantor`, `Successor`) should be packet-scoped `party-role` nodes with `role-id`, not permanent party classes.
- `Claim` -> `claim`; `Amount` -> `amount`; `EnforcementTitle` -> `enforcement-title`; `CourtProcedure` -> `court-procedure`
- `AttachmentTarget` -> `attachment-target`; `Asset` -> `asset`
- `LedgerEvent` should map to `ledger-entry`; `RecoveryTransaction` -> `recovery-transaction`; `Cost` -> `cost-entry`
- `RuleFinding` should map to `legal-check` or a `stopgate`/`legal-check` pair, depending on whether A emits placeholder rule findings before Todo 7.

Core ontology edges to require in the output:

- `case-packet` `has-document` `legal-document`
- `legal-document` `has-source-span` `source-span`
- `legal-document` `has-provenance` `document-provenance`
- `case-packet` `has-party` `party`
- `party` `has-party-role` `party-role`
- `party` `supported-by-identity` `identity-evidence` when identity evidence exists
- `case-packet` `has-claim` `claim`
- `claim` `has-amount` `amount`
- `case-packet` `has-enforcement-title` `enforcement-title`
- `case-packet` `has-court-procedure` `court-procedure`
- `case-packet` `has-attachment-target` `attachment-target`
- `attachment-target` `held-by-party` `party`
- `case-packet` `has-asset-evidence` `asset-evidence`
- `asset-evidence` `describes-asset` `asset`
- `case-packet` `has-ledger` `operational-ledger`
- `operational-ledger` `has-ledger-entry` `ledger-entry`
- `ledger-entry` `records-recovery` `recovery-transaction`
- `ledger-entry` `records-cost` `cost-entry`

## Required Evidence Keys

A must emit these exact evidence-key names somewhere stable in the case graph, preferably as `case_packet.evidence_keys` plus node-level mirrored references where relevant:

- `case_packet_id`
- `court_case_number`
- `claim_id`
- `enforcement_title_id`
- `party_identity_key`
- `document_hash`

Existing sources cover only part of this:

- Manifest provides `source_hash` for every fixture document. The graph should expose this as `document_hash` or define an explicit `source_hash` to `document_hash` mapping.
- Registry emits `case_packet_id` and `hybrid_evidence_keys`, but its key type for claim-like tokens is currently `claim_or_packet_token`, not `claim_id`.
- Field extraction emits `court_case_number`, `linked_title_case_number`, `assigned_claim_token`, `linked_claim_token`, `party_identity_key`, amount fields, role fields, and line-level provenance.
- No existing field extractor directly emits `enforcement_title_id`; A should derive a deterministic title id from title document evidence, title type, linked case number, and document id, while preserving the source fields.
- No existing field extractor directly emits `claim_id`; A should derive a deterministic claim id from `assigned_claim_token`, `linked_claim_token`, `court_case_number`, claim amount/title facts, or a documented unresolved placeholder with a review reason.

Acceptance should fail if the output only contains `claim_or_packet_token` or `source_hash` and never exposes `claim_id` / `document_hash` under the required names.

## Provenance Requirements

Every non-derived graph fact must include:

- `document_id`
- `source_ref`
- `source_span` or line/chunk pointer, using classifier `evidence_spans` or fields `chunk_id`, `line_start`, `line_end`
- `confidence`
- `extractor_version`
- enough context to identify the originating field or classifier signal

For derived ids and derived edges, A should label them as `derived` and cite all input facts used. Examples:

- `case_packet_id` derived from registry or graph evidence keys must cite its input key list and document hashes.
- `claim_id` derived from assigned/linked claim tokens or title facts must cite those field facts.
- `enforcement_title_id` derived from a payment order plus service/finality proof must cite both documents if both are used.
- `identity_uncertain` must cite the competing party facts that were not merged.

The CLI acceptance text says "document provenance on every non-derived fact"; the tests should assert this recursively across all graph nodes and edges, not just top-level documents.

## Identity And Merge Rules

No party, case, claim, or role merge may rely on display name or placeholder role text alone.

Required behavior:

- Parties with `party_identity_key` may be linked through `supported-by-identity`, but the identity fixture itself says identity facts support party resolution and are not enough for case merge alone.
- Similar debtor labels without identity evidence must remain separate party nodes.
- The graph must include an explicit reason such as `identity_uncertain`, with source refs for the ambiguous debtor facts.
- Name/role placeholders like `[DEBTOR_PERSON]`, `[CREDITOR_ORG]`, and `[ASSIGNEE_ORG]` must not be treated as stable identity keys.
- `case_packet_id` cannot be minted from name alone. Registry behavior already uses evidence keys or document hash; A should preserve or improve that behavior.

Required test before integration:

- Build a fixture with two similar debtor labels and no `party_identity_key`; assert two debtor party nodes remain, no shared party id is created, and an `identity_uncertain` review/risk reason appears.
- Build a fixture with identity evidence and verify any merge still keeps the supporting `party_identity_key`, document id, source ref, span/line, confidence, and extractor version.

## PII Safety

Existing classifier, field extraction, registry, manifest, and snippets are designed to be PII-safe:

- Classifier and fields set `pii_profile.raw_text_included` to false.
- Field values pass through redaction helpers for national-id, phone, and account-like shapes.
- Fixtures are synthetic minimized snippets with placeholders and no full raw OCR document body.
- Registry stores hashes and redacted path refs instead of raw document text.

A must preserve that boundary:

- Do not store raw OCR text in the graph JSON.
- Source spans may include redacted excerpts only. If a source span comes from fields, prefer `source_ref`, `chunk_id`, `line_start`, `line_end` over copying full line text.
- Do not emit raw identifiers, phone numbers, account numbers, full addresses, or full source documents in `.omo/evidence`.
- Graph output should include `pii_profile` or a redaction/provenance policy at document or graph summary level.

## CLI And JSON Shape

Required CLI:

```bash
python3 -m trustgraph_legal.case_graph --fixtures tests/fixtures/legal-ocr/manifest.json --out .omo/evidence/debt-collection-ontology/task-6-case-graph.json
```

Recommended JSON shape:

- `schema_version`: e.g. `trustgraph-legal-case-graph/v1`
- `ontology_version`
- `extractor_versions` or per-node/per-fact `extractor_version`
- `summary`: counts for case packets, documents, parties, claims, unresolved identities, provenance failures
- `case_packets`: array of packet objects
- `nodes`: typed graph nodes with ontology ids
- `edges`: typed graph edges with ontology ids
- `facts`: optional normalized fact projection if nodes/edges are lower-level
- `review_items` or `risk_flags`: include `identity_uncertain` and missing evidence states
- `pii_profile`: must state raw text is not included

Every node/edge/fact should be JSON serializable with stable ids. The tests should not assert brittle full snapshots only; they should assert required keys, ontology ids, provenance, and identity behavior.

## Tests A Must Pass Before Integration

Minimum required:

- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_case_graph_builder.py -q`
- `python3 -m trustgraph_legal.case_graph --fixtures tests/fixtures/legal-ocr/manifest.json --out .omo/evidence/debt-collection-ontology/task-6-case-graph.json`
- `/usr/bin/python3 -m py_compile trustgraph_legal/case_graph.py tests/unit/legal_ontology/test_case_graph_builder.py`
- `git diff --check HEAD~1 HEAD` after A commit
- Sensitive-pattern scan over A code, tests, and generated evidence

Test cases to require:

- Happy path builds at least one case packet with documents, parties, claim, amount, enforcement title, court procedure, attachment target, asset evidence, ledger events, recovery transaction, and cost.
- Required evidence-key test asserts exact keys `case_packet_id`, `court_case_number`, `claim_id`, `enforcement_title_id`, `party_identity_key`, and `document_hash`.
- Provenance test walks every non-derived fact and verifies `document_id`, `source_ref`, span/line/chunk, confidence, and extractor version.
- Ontology contract test verifies every emitted class/property id exists in `recova-debt-collection@v0`.
- Identity uncertainty test proves similar debtor names without identity evidence remain unresolved with `identity_uncertain`.
- PII test verifies graph/evidence JSON excludes raw sensitive identifier, phone, account, and full-location patterns and does not include raw source document text.
- CLI test drives the module entrypoint and verifies the output shape and summary counts.
- Negative test for missing field evidence should create a review item or risk flag rather than silently creating a high-confidence graph fact.

## Post-Implementation Risks To Check On A Branch

Because A had no implementation at review time, check these as soon as A has a diff:

- Does A import and reuse classifier/fields outputs, or does it duplicate extraction rules and drift from Todo 5?
- Does A use ontology IDs exactly, or introduce unconfigured IDs such as `Case`, `Creditor`, or `LedgerEvent` as ontology classes?
- Does A expose both `source_hash` and `document_hash`, or only the former?
- Does A map `claim_or_packet_token` to a real `claim_id` deliberately, or leak the registry's broader token name into the Todo 6 contract?
- Does A derive `enforcement_title_id` deterministically and cite source facts?
- Does A set fact provenance at fact granularity, not only document granularity?
- Does A keep role assertions packet-scoped rather than turning creditor/debtor into permanent identities?
- Does A mark derived facts and preserve input fact refs?
- Does A avoid full-line raw source copying in evidence JSON when a span pointer is enough?
- Does the failure QA actually create two ambiguous debtor candidates, rather than only asserting a static string exists?

## Integration Recommendation

Do not integrate Todo 6 until A's branch satisfies the exact evidence-key names, fact-level provenance walk, ontology-id validation, and identity uncertainty failure case. The rest of the implementation can be small and deterministic, but these four items are the contract core for later StopGate work.
