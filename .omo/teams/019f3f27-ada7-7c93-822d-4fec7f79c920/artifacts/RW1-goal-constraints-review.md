# RW1 Goal and Constraint Review

ReviewClaim: RW1 FAIL

## Verdict

The implementation satisfies several safety and boundary constraints, but it does not satisfy the core goal at the actual claim-domain decision/MCP surface. The standalone workflow judgment unit surface can produce distinct practical stages, but the integrated `evaluate_claim_domain_decision` path collapses the eight semireal workflow scenarios to `evidence_completion` / `evidence_completion_loop`.

## Blocking Goal Gap

- Plan goal requires a first-class collection workflow judgment model that answers current stage, posture, next best action, premature actions, missing inputs, review/remediation loop, and reasons, integrated into claim-domain decision/MCP output.
- Plan goal also requires semireal scenario coverage proving practical workflow behavior for premature litigation, title acquisition, asset discovery, enforcement-ready, monitoring/low-yield, finance reconciliation, and insolvency/protected-asset hold.
- Actual decision-surface check:
  - `premature_litigation_review`: expected `title_acquisition` / `confirm_service_finality_execution_clause` / `legal_precondition_review_loop`; actual `evidence_completion` / `collect_missing_evidence` / `evidence_completion_loop`.
  - `title_acquisition_loop`: expected `title_acquisition` / `acquire_or_confirm_title` / `title_acquisition_loop`; actual `evidence_completion` / `collect_missing_evidence` / `evidence_completion_loop`.
  - `asset_discovery_loop`: expected `asset_discovery` / `enrich_asset_signals` / `asset_discovery_loop`; actual `evidence_completion` / `collect_missing_evidence` / `evidence_completion_loop`.
  - `enforcement_ready_review`: expected `enforcement_ready` / `prepare_advisory_packet` / `legal_precondition_review_loop`; actual `evidence_completion` / `collect_missing_evidence` / `evidence_completion_loop`.
  - `monitoring_low_yield`: expected `monitoring` / `monitor_retry` / `low_yield_monitoring_loop`; actual `evidence_completion` / `collect_missing_evidence` / `evidence_completion_loop`.
  - `finance_reconciliation_hold`: expected `evidence_completion` / `reconcile_finance` / `finance_reconciliation_loop`; actual `evidence_completion` / `collect_missing_evidence` / `evidence_completion_loop`.
  - `insolvency_protected_asset_hold`: expected `insolvency_protected_asset_review` / `insolvency_protected_asset_review` / `protected_asset_insolvency_hold`; actual `evidence_completion` / `collect_missing_evidence` / `evidence_completion_loop`.

Evidence:

- `.omo/plans/debt-brain-structural-depth-v1.md:21-29` states the core must-have goal and scenario proof requirement.
- `.omo/evidence/debt-brain-structural-depth-v1/task-7-scenario-coverage.json:12-66` records the eight scenario expectations.
- `.omo/teams/019f3f27-ada7-7c93-822d-4fec7f79c920/artifacts/final3-manual-qa-report.md:15-24` records that all eight actual local decision-surface scenarios returned `evidence_completion` / `evidence_completion_loop`.
- `trustgraph_legal/domain_workflow_integration.py:27-34` passes evidence and finance support surfaces into `evaluate_workflow_judgment`, but not the legal checkpoint surface.
- `trustgraph_legal/workflow_judgments.py:100-117` prioritizes evidence review/hold before finance, legal, route, asset, and readiness logic, explaining why broad evidence review collapses later practical workflow distinctions.
- `tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py:80-97` checks only that the workflow envelope exists and is advisory-safe; it does not assert scenario-specific workflow stage/action/loop expectations at the integrated decision/MCP surface.

## Goal Breakdown

- PARTIAL: Operator playbook exists and documents practical stages, actions, premature-action reasons, checkpoint inputs, and remediation loops.
- PARTIAL: Evidence, finance, and legal support modules exist and have standalone tests/evidence.
- FAIL: Legal checkpoints are not wired into the integrated claim-domain workflow output, so legal precondition and protected-asset scenarios do not influence the actual decision/MCP surface.
- FAIL: Semireal scenarios do not prove practical workflow behavior at the decision/MCP surface; 7 of 8 expected stage/action/loop outcomes mismatch and the remaining evidence-completion scenario only passes because it matches the collapsed default.
- PARTIAL: Domain decision/MCP output includes `workflow_judgment` and `operator_next_steps`, but it is envelope-compatible rather than behavior-complete.
- PASS: Docs and final evidence frame workflow judgment as the product center and legal/evidence/finance as support layers.

## Constraint Compliance

- PASS: No remote deployment or remote smoke was performed or claimed in the final evidence.
- PASS: Local MCP tool order/count remains 25 with the accepted first 21 and claim-domain tail.
- PASS: No public admin/write tools were observed in this wave's changed surface.
- PASS: No debtor contact, court filing, seizure, payment demand, or production ledger mutation was added by this wave.
- PASS: Deliverable-surface scans and spot checks found only negative/guardrail strings or synthetic rejection tests for raw fields; no raw PII/OCR/contact/filing/local-path output evidence was observed.
- PASS: Workflow outputs remain advisory-only and human-review-gated.
- PASS: Finance remains fixture/review support and does not emit authoritative balance authority in the checked surfaces.
- PASS: Legal/evidence/finance are documented as support layers rather than the product identity.

## Blocker

Fix Todo 6/7 integration so the real `evaluate_claim_domain_decision` and MCP decision path carries enough evidence/legal/finance support context to produce the eight required practical workflow outcomes, and add integrated assertions comparing each required scenario to its expected stage/action/posture/remediation loop.
