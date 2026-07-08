# V8 Todo 8 Refresh Verification Report

Timestamp: 2026-07-08T15:03:50+0900

Thread: V8 verify-docs-readiness (`codex://threads/019f402e-efaf-7dc1-b884-7ea6e809f713`)
Target: Todo 8 refresh after Todo 6/7 real-boundary fix

## Verdict

VerificationClaim: Todo 8 REFRESH APPROVED

## Refreshed Contract Inspection

- Product doc now states the real domain/MCP boundary consumes structured workflow support through generic payload fields, not scenario names or test labels:
  - `docs/product/debt-collection-ontology/claim-domain-ontology-v1.md:48`
  - `docs/product/debt-collection-ontology/claim-domain-ontology-v1.md:150`
  - `docs/product/debt-collection-ontology/claim-domain-ontology-v1.md:273`
- Final summary states the refresh:
  - fixture `workflow_support` projects into `evidence_checkpoint`, `finance_bridge`, and `legal_checkpoints`;
  - `domain_workflow_integration` consumes those fields before deterministic fallbacks;
  - direct domain and MCP `evaluate_claim_domain_decision` assert exact stage/action/posture/remediation loop for all eight semireal scenarios;
  - no scenario-id or expected-label branching.
- Final validation encodes the same `real_boundary_contract` with `scenario_id_branching: false`, `expected_label_branching: false`, and `deterministic_fallbacks_preserved: true`.
- Working log records the real-boundary refresh and RV67R approval.
- Stale relaxed-policy scan passed over product doc, working log, final summary, and final validation:
  - `STALE_POLICY_SCAN_OK refreshed_real_boundary_docs=yes old_relaxed_policy_absent=yes`.

## Implementation Spot Check

- `trustgraph_legal/domain_workflow_integration.py` consumes payload `evidence_checkpoint`, `finance_bridge`, and `legal_checkpoints` before fallback logic.
- `trustgraph_legal` contains no `scenario_id`, `expected_workflow`, or `expected_label` branching.
- Test helper projection is generic: fixture `workflow_support` is copied into standard payload support fields in `tests/utils/claim_domain_pipeline_support.py`.
- Fixture inventory has eight `workflow_support` scenarios:
  - `premature_litigation_review`
  - `evidence_completion_loop`
  - `title_acquisition_loop`
  - `asset_discovery_loop`
  - `enforcement_ready_review`
  - `monitoring_low_yield`
  - `finance_reconciliation_hold`
  - `insolvency_protected_asset_hold`

## Commands Rerun

- Focused pytest:
  - `uv run --with pytest --with pydantic --with typing-extensions python -m pytest tests/unit/legal_ontology/test_operator_playbook_v1.py tests/unit/legal_ontology/test_workflow_judgments_v1.py tests/unit/legal_ontology/test_evidence_quality_v1.py tests/unit/legal_ontology/test_finance_claim_model_v1.py tests/unit/legal_ontology/test_domain_decision_engine_v1.py tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py -q`
  - Result: `28 passed`, one existing `asyncio_mode` warning.
- Regression pytest:
  - `uv run --with pytest --with pydantic --with typing-extensions python -m pytest tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py tests/unit/legal_ontology/test_stop_gates_domain_v1.py tests/unit/legal_ontology/test_route_decisions_v1.py tests/unit/legal_ontology/test_action_packets_v1.py -q`
  - Result: `18 passed`, one existing `asyncio_mode` warning.
- Reopened real-boundary pytest:
  - `uv run --with pytest --with pydantic --with typing-extensions python -m pytest tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py tests/unit/legal_ontology/test_workflow_judgments_v1.py -q`
  - Result: `9 passed`, one existing `asyncio_mode` warning.
- Domain/MCP boundary pytest:
  - `uv run --with pytest --with pydantic --with typing-extensions python -m pytest tests/unit/legal_ontology/test_domain_decision_engine_v1.py tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py -q`
  - Result: `8 passed`, one existing `asyncio_mode` warning.
- JSON validation:
  - Result: `JSON_VALIDATION_OK files=21`.
- Compile:
  - `python3 -m compileall trustgraph_legal tests/unit/legal_ontology tests/integration/legal_ontology`
  - Result: passed.
- Scoped structural-depth typecheck:
  - Result: `0 errors, 0 warnings, 0 notes`.
- Scoped real-boundary lint:
  - Result: `All checks passed!`.
- MCP order smoke:
  - Result: `MCP_ORDER_OK count=25 tail=list_claim_domain_routes,explain_collection_workflow_state,evaluate_claim_domain_decision,explain_claim_action_packet`.
- System Python pytest caveat:
  - `python3 -m pytest --version`
  - Result: `/Library/Developer/CommandLineTools/usr/bin/python3: No module named pytest`.
- Whitespace:
  - `git diff --check`
  - Result: passed.
- Deliverable safety scan:
  - Result: `NO_FINDINGS files=26`.
- Deployment/client-doc guard:
  - Result: `PLAN_COMPLIANCE_APPROVED no_client_deploy_docs no_remote_claims`.

## Manual QA

Direct real-boundary QA was rerun against all eight required semireal scenarios. For each scenario, the direct domain decision and MCP decision matched exact `current_stage`, first `next_best_action`, `posture`, and `remediation_loop`.

Result:

`DIRECT_QA_APPROVED scenarios=8 surfaces=domain,mcp exact_stage_action_posture_loop=pass ids=premature_litigation_review,evidence_completion_loop,title_acquisition_loop,asset_discovery_loop,enforcement_ready_review,monitoring_low_yield,finance_reconciliation_hold,insolvency_protected_asset_hold`

## Blockers

None.

## Residual Risks

- System `python3` still lacks pytest; uv-based pytest suites pass and remain the practical local validation path.
- Broad repository docs still contain older out-of-scope remote/auth examples; Todo 8 refreshed deliverables keep local-only readiness and do not modify client/deployment docs.
- Deterministic fallbacks are intentionally preserved and conservative if future adapters strip the structured support fields; current fixture adapter preserves them and boundary tests enforce exact outcomes.

## Decision

APPROVE Todo 8 refresh.
