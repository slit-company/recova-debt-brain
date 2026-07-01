# C Contracts Review - Todo 7/8

Status: pre-implementation contract review for current Todo 7/8 team branches.
Reviewer: member C, contracts-review.
Date: 2026-06-30.

## Scope Read

- Plan source: `/Users/cosmos/dev/ontology/trustgraph/.omo/plans/debt-collection-ontology.md`, Todo 7 and Todo 8.
- Contract source: `docs/product/debt-collection-ontology/domain-contract.md`.
- Ontology source: `resources/ontologies/recova-debt-collection.json`.
- Baseline code reviewed: `trustgraph_legal/case_graph.py`, `trustgraph_legal/classifier.py`, `trustgraph_legal/fields.py`, plus `trustgraph_legal/pii.py` and `trustgraph_legal/registry.py` for PII/provenance context.
- Existing tests reviewed: `tests/unit/legal_ontology/test_case_graph_builder.py`, `test_document_classifier.py`, `test_field_extractors.py`, `test_ingest.py`, and `test_validate_ontology.py`.
- Current-session A/B branch status: branches `team/debt-collection-ontology-todo-7-8-20260630/A` and `/B` exist, both have no diff from `master`, and their worktree status is clean. No Todo 7/8 implementation was available to review at artifact time.

## Executive Risk Summary

Todo 7 and Todo 8 are blocked from integration until A and B provide the missing implementation and tests. The current baseline has good Todo 1-6 foundations for redacted fixture ingestion, deterministic document classification, field extraction, and case graph provenance, but it does not yet implement the StopGate engine, curated rule-source artifacts, ontology candidate queues, version promotion, or case reprocessing workflow.

Highest-risk integration points:

- StopGate output must be a deterministic domain decision, not a recommendation summary. It must return only `가능`, `불가능`, or `보류`.
- Production checks may use only approved curated rules with rule id, version, effective date, source ref, statute ref, status, and review lineage.
- Governance must not auto-promote ontology or rule changes from one document, one LLM assertion, or one unreviewed queue item.
- PII redaction must extend beyond classifier/fields output into StopGate evidence, review notes, rule-source notes, regression evidence, and any CLI/log output.
- Existing document-type coverage is narrower than the domain contract. The baseline classifier/fields cover 9 canonical outputs and do not cover `attachment-collection-application`, `judgment-or-decision`, `attachment-target-priority`, or `legal-rule-source` as first-class classified document types.

## Acceptance Gates For A - Todo 7 StopGate Engine

A must satisfy all checks below before leader integration.

1. Deterministic StopGate coverage

- Implement a public module/CLI contract matching the plan: `python3 -m trustgraph_legal.check --case <case-graph-json>`.
- Add `tests/unit/legal_ontology/test_stop_gates.py`.
- Include red/green fixture coverage for the plan-required cases: `discharge_proceeding_detected`, `missing_execution_clause`, `limitation_risk`, `exempt_claim_targeted`, `assignment_chain_broken`, `amount_mismatch`, and `identity_uncertain`.
- Include an invalid-provenance failure where a material blocking fact without source span returns `invalid_fact_without_provenance` or an equivalent stable error/risk flag.
- No LLM-only legal conclusions, live law crawling, client memory, or prompt-only rule memory may clear or block a StopGate.

2. StopGate result JSON contract

Every StopGate or recommendation-like check must return at least:

```json
{
  "case_packet_id": "case-packet-redacted",
  "decision": "보류",
  "recommended_action": "collect_more_evidence",
  "required_preconditions": [],
  "blocked_reasons": [],
  "missing_evidence": [],
  "risk_flags": [],
  "source_refs": [],
  "rule_refs": [],
  "confidence": "medium",
  "review_queue_items": []
}
```

Contract rules:

- `decision` enum is exactly `가능`, `불가능`, or `보류`.
- `recommended_action` is non-executing and may not imply filing, contacting, collecting, paying, transferring, or updating external business systems.
- `blocked_reasons`, `missing_evidence`, and `risk_flags` use stable machine labels, not prose-only text.
- `source_refs` use redacted document/chunk/span pointers and must never include raw source text by default.
- `rule_refs` include `rule_id`, `version`, `effective_date`, `source_ref`, `statute_ref` when available, and `status`.
- `review_queue_items` reference governance queue ids or returned item ids when the check creates review work.

3. Rule-source governance

- Store curated rule sources as versioned artifacts or structured data, not inline ad hoc constants without review metadata.
- Required rule fields: `rule_id`, `rule_group`, `statute_ref`, `source_ref`, `effective_date`, `jurisdiction`, `condition`, `decision`, `risk_flags`, `required_evidence`, `source_url` when available, `version`, `status`, `reviewed_by`, `reviewed_at`, `supersedes`, and `notes`.
- Allowed statuses: `draft`, `reviewed`, `approved`, `deprecated`, `superseded`.
- Production StopGate evaluation must ignore or hold on `draft`, `reviewed`, `deprecated`, and `superseded` rules unless the explicit behavior is `보류` with `rule-source-unapproved`.
- Promotion to `approved` must require regression evidence and approval metadata; a newer draft must not shadow the currently approved rule.

4. Provenance and critical fact handling

- StopGate input facts must cite document, chunk/span or reviewed derived-rule refs.
- Derived facts must cite input fact refs and the rule version used.
- Low-confidence, conflict, missing, stale, or unknown critical facts must return `보류` and create or reference governance review items.
- `identity_uncertain` and name-only merge findings from the case graph must hold affected actions.
- If graph facts and approved rules conflict with client-agent memory, the result must expose the conflict and return `보류` unless an approved rule clearly blocks the action.

## Acceptance Gates For B - Todo 8 Governance Workflow

B must satisfy all checks below before leader integration.

1. Queue and state coverage

- Add `tests/unit/legal_ontology/test_ontology_governance.py`.
- Implement queue contracts for `unknown-document-type`, `low-confidence-extraction`, `fact-conflict`, `identity-merge-review`, `rule-risk-review`, `ontology-candidate`, `version-promotion`, and `case-reprocess`.
- A low-confidence unknown fixture must create an ontology candidate, review item, and reprocess plan without mutating `resources/ontologies/recova-debt-collection.json`.
- Promotion without required approval metadata must be rejected.

2. Review item schema

Every review item should include:

- `review_item_id`
- `queue_id`
- `case_packet_id`
- `document_id`
- `fact_id`
- `candidate_value`
- `current_value`
- `reason`
- `risk_flags`
- `source_refs`
- `redaction_status`
- `status`
- `created_at`
- `updated_at`
- `assigned_to`
- `resolution`
- `resolution_reason`
- `approved_by`
- `approval_evidence_ref`

Allowed statuses are `open`, `in-review`, `needs-evidence`, `approved`, `rejected`, `superseded`, and `closed`.

3. Promotion and reprocessing boundaries

- Governance may transition review state but must not mutate raw source documents.
- Ontology/rule promotion must require approval metadata plus regression evidence.
- Candidate review must preserve rejected candidates and reasons for auditability.
- Case reprocessing must be planned when any material version changes: ontology, extractor, prompt, rule source, redaction policy, or registry schema.
- A reprocess plan must record `regression_run_id`, `fixture_set_id`, changed versions, pass/fail result, unresolved risk summary, and approval metadata before production promotion.
- No auto-promotion from a single unreviewed document, low-confidence extraction, or LLM-only assertion.

4. Ontology model alignment

The current ontology has 36 classes, 41 object properties, and 44 datatype properties. It includes `stopgate`, `rule-source`, `rule-version`, and `review-item`, but does not include explicit `ontology-candidate` or `reprocess-job` classes. B can still implement these as service-side queue records, but it must document that boundary. If B emits ontology-backed graph nodes for these concepts, it must add configured classes/properties and validator tests.

## Schema And Label Contracts

Document types:

- Domain contract lists 14 document type ids, including `attachment-collection-application`, `judgment-or-decision`, `attachment-target-priority`, and `legal-rule-source`.
- Current baseline classifier canonical enum covers 10 values including `unknown`, but only 9 positive canonical outputs: `attachment-collection-order`, `payment-order`, `service-finality-proof`, `assignment-succession`, `identity-evidence`, `insolvency-credit-recovery`, `asset-evidence`, `ledger-recovery`, and `amount-interest-calculation`.
- Integration requirement: A/B must not silently treat missing domain types as covered. Either extend classifier/fields/governance contracts or document a v0 exclusion and route the missing type to `unknown-document-type` review.

Labels and ids:

- Ontology ids remain kebab-case.
- Baseline tests already assert emitted graph ontology classes and predicates are configured in `recova-debt-collection.json`.
- Todo 7/8 outputs must keep stable machine labels for stopgate ids, risk flags, queue ids, rule statuses, and review statuses.
- Existing snake_case fixture labels may remain compatibility input, but public domain outputs should use domain-contract kebab-case ids unless an existing schema explicitly says otherwise.

Confidence:

- Do not collapse confidence to a float only. Contract requires level, score when available, reason, and provenance.
- StopGate checks may not upgrade confidence by LLM assertion alone.
- `low`, `conflict`, and `unknown` critical facts must hold affected legal-risk recommendations.

Case identity:

- `case_packet_id` remains canonical.
- Hybrid evidence keys must preserve `court_case_number`, `claim_id`, `enforcement_title_id`, `party_identity_key`, and `document_hash`.
- Name-only party or packet merge must remain blocked. Current baseline has coverage for similar debtors without identity evidence; Todo 7/8 must preserve and consume that finding.

## PII And Provenance Risks

Baseline PII handling:

- `trustgraph_legal.pii.redact_text` covers national id shape, phone, account, and Korean address-like hints.
- Classifier and fields outputs set `raw_text_included` false and have tests for sensitive-shape redaction.
- Registry dry-run records redact path/text counts and use `source_path_ref` hashes.

Todo 7/8 added risks:

- Rule-source notes can accidentally quote raw law/client context or OCR snippets; curated rules should cite `source_ref` and statute refs, not copy sensitive case text.
- Governance review notes are high leakage risk because they collect ambiguous facts; they must store redacted context and require raw source access through approved storage only.
- StopGate `source_refs` must not include excerpts unless those excerpts are redacted and explicitly marked with `redaction_status`.
- Regression/evidence files under `.omo/evidence` and team artifacts must be scanned for raw sensitive patterns before handoff.
- Logs and CLI stdout should print counts, ids, and file refs only, not raw OCR spans.
- `reviewed_by`, `assigned_to`, and approval metadata may themselves be personal data; prefer service identities or configured reviewer ids in committed fixtures.

Recommended sensitive-pattern scan before integration:

```sh
rg -n "resident|주민등록번호|[0-9]{6}-[0-9]{7}|010[-. ][0-9]{3,4}[-. ][0-9]{4}|계좌|은행|입금|송금" \
  trustgraph_legal tests/unit/legal_ontology tests/fixtures/legal-ocr resources/ontologies docs/product/debt-collection-ontology .omo/evidence
```

Expected result: only intentional redaction tests or policy text, no raw identifiers.

## Cross-Contract Boundary Review

Non-execution boundary:

- Todo 7 StopGate outputs can recommend preconditions and next evidence collection, but must not execute or imply completed execution.
- Todo 8 governance tools can change review states and promotion state, but must not mutate raw documents or external business systems.
- Future MCP Todo 9 must preserve tool-group scope: `read` cannot write, `graph` cannot clear StopGates, `stopgate` cannot execute, `governance` cannot mutate raw docs, and `admin` requires privileged scope/audit logging.

Rule versus governance boundary:

- A owns rule evaluation and deterministic decisions.
- B owns review state, candidate handling, promotion, and reprocess planning.
- A may create or reference review queue items when a StopGate holds, but B should own state transitions and approval enforcement.

Ontology versus service records:

- If governance records are not ontology graph nodes, their schema must still be stable and versioned.
- If governance emits graph nodes, classes/properties must be added to `resources/ontologies/recova-debt-collection.json` and validated.

Baseline implementation gap to watch:

- Current case graph uses `"missing"` placeholder provenance from `_first_provenance` when no matching source field exists. Todo 7 must treat such placeholder provenance as invalid or missing evidence for legal-risk decisions.
- Current classifier maps `judgment_payment_order` to `payment-order`; if the domain needs `judgment-or-decision`, B should create a candidate or A should hold on insufficient title specificity.
- Current `pii_profile` fields are minimal compared to the domain contract. Todo 7/8 should add or require `contains_sensitive_person_data`, `contains_financial_identifier`, `contains_contact_or_location`, `redaction_status`, `hashing_policy`, `raw_source_access_policy`, and `last_redaction_check_at` where outputs cross governance or MCP boundaries.

## Post-Implementation Review Checklist

Run after A and B deliver implementation branches:

- `pytest tests/unit/legal_ontology/test_stop_gates.py -q`
- `pytest tests/unit/legal_ontology/test_ontology_governance.py -q`
- `pytest tests/unit/legal_ontology/test_case_graph_builder.py tests/unit/legal_ontology/test_document_classifier.py tests/unit/legal_ontology/test_field_extractors.py -q`
- `python3 -m trustgraph_legal.check --case .omo/evidence/debt-collection-ontology/task-6-case-graph.json`
- Governance happy path: low-confidence unknown fixture creates ontology candidate, review item, and case reprocess plan without production ontology mutation.
- Governance failure path: promotion without `approved_by` and `approval_evidence_ref` is rejected.
- Rule failure path: a draft or superseded rule returns `보류` with `rule-source-unapproved`.
- Provenance failure path: remove source span from a blocking fact and verify the engine returns invalid/missing provenance, not `가능`.
- PII scan over implementation, tests, fixtures, docs, evidence, and this team artifact.
- Verify A/B do not change unrelated TrustGraph core behavior or add Hermes-specific/runtime-specific assumptions.

## Integration Decision

Current decision: do not integrate Todo 7/8 yet. A and B are pre-implementation in the current team worktrees. Integration can proceed only after the StopGate engine and governance workflow exist, focused tests pass, sensitive-pattern scans are clean, and the leader reviews the post-implementation checklist above.
