# RW3 Code Quality / Architecture Review

ReviewClaim: RW3 FAIL

Scope: verifier-only review of structural-depth implementation files for maintainability, deterministic structured parsing, narrow public contracts, type safety, abstraction fit, and test alignment. No product files edited.

## Blocking Findings

1. Public decision/MCP path does not consume legal workflow checkpoints.

- Evidence: `trustgraph_legal/domain_decisions.py:103` constructs `DomainWorkflowRequest(request.claim_domain_payload, route_decision_json, request.finance_review_codes, review_items)` with no legal checkpoint surface.
- Evidence: `trustgraph_legal/domain_workflow_integration.py:27` builds `WorkflowJudgmentRequest` with `claim_domain_payload`, `route_decisions`, `evidence_checkpoint`, and `finance_bridge` only.
- Evidence: `trustgraph_legal/workflow_judgments.py:32` and `trustgraph_legal/workflow_judgments.py:120` support `legal_checkpoints` and route legal gates when present.
- Evidence: `trustgraph_legal/legal_workflow_checkpoints.py:67` provides the adapter, but `rg "evaluate_legal_workflow_checkpoints|legal_checkpoints"` shows it is only used by unit tests/helpers, not the product decision/MCP path.
- Why this blocks: the architecture exposes a legal checkpoint contract but the public surface cannot exercise it. This leaves Todo 5 as a parallel island and makes the workflow judgment engine's legal branch reachable only through handcrafted unit requests, not through `evaluate_claim_domain_decision` or the MCP handler.

2. Scenario tests are not aligned with the real public surface.

- Evidence: `tests/unit/legal_ontology/test_workflow_judgments_v1.py:178` asserts exact semireal workflow expectations by building direct `WorkflowJudgmentRequest`s via `tests/unit/legal_ontology/workflow_scenario_requests.py:16`.
- Evidence: `tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py:93` and `tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py:124` assert only that a workflow envelope exists and has nonempty stage/action, not that the domain/MCP surface returns the scenario's expected workflow stage/action/posture/remediation loop.
- Evidence: running the real domain entrypoint on legal-oriented fixtures produced:
  - `title_acquisition_loop expected title_acquisition actual evidence_completion action collect_missing_evidence`
  - `premature_litigation_review expected title_acquisition actual evidence_completion action collect_missing_evidence`
  - `insolvency_protected_asset_hold expected insolvency_protected_asset_review actual evidence_completion action collect_missing_evidence`
- Why this blocks: the unit tests prove the standalone engine can classify legal stages when legal surfaces are manually injected, but they do not prove the integrated decision/MCP contract does so. This is exactly the kind of test/contract drift this lane is meant to catch.

## Non-Blocking Notes

- Scoped compile, focused pytest, and scoped basedpyright passed.
- New implementation modules stay under the 250 pure-LOC ceiling individually.
- The code avoids `Any`, `cast`, `type: ignore`, `eval`, `exec`, broad exception handling, LLM/web calls, wall-clock logic, and unsafe raw text/balance output in the inspected structural-depth modules.
- `trustgraph_legal/domain_workflow_integration.py` duplicates a small finance bridge shape instead of reusing `FinanceWorkflowBridge`; this is tolerable for now but increases contract drift risk because two mappings must remain consistent.

## Verification

- `uv run --with pytest --with pydantic --with typing-extensions python -m pytest tests/unit/legal_ontology/test_workflow_judgments_v1.py tests/unit/legal_ontology/test_evidence_quality_v1.py tests/unit/legal_ontology/test_finance_workflow_bridge_v1.py tests/unit/legal_ontology/test_legal_workflow_checkpoints_v1.py tests/unit/legal_ontology/test_domain_decision_engine_v1.py tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py -q` -> 25 passed, 1 existing pytest config warning.
- `python3 -m compileall trustgraph_legal/workflow_judgments.py trustgraph_legal/evidence_quality.py trustgraph_legal/finance_review_bridge.py trustgraph_legal/legal_workflow_checkpoints.py trustgraph_legal/domain_workflow_integration.py trustgraph_legal/domain_decisions.py` -> passed.
- `uv run --with basedpyright --with pytest --with pydantic --with typing-extensions basedpyright trustgraph_legal/workflow_judgments.py trustgraph_legal/evidence_quality.py trustgraph_legal/finance_review_bridge.py trustgraph_legal/legal_workflow_checkpoints.py trustgraph_legal/domain_workflow_integration.py trustgraph_legal/domain_decisions.py tests/unit/legal_ontology/test_workflow_judgments_v1.py tests/unit/legal_ontology/test_evidence_quality_v1.py tests/unit/legal_ontology/test_finance_workflow_bridge_v1.py tests/unit/legal_ontology/test_legal_workflow_checkpoints_v1.py tests/unit/legal_ontology/test_domain_decision_engine_v1.py tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py` -> 0 errors, 0 warnings, 0 notes.
- Manual domain-surface scenario comparison -> legal-oriented expected stages are not produced through `evaluate_claim_domain_decision`.

## Blocker To Clear

Wire a deterministic legal checkpoint surface into the public decision/MCP workflow path, or deliberately change the public contract/tests so scenario expectations are asserted only for supported inputs. Then add integrated assertions that the real domain and MCP decision surfaces return the expected workflow stage/action/posture/remediation loop for the eight semireal scenarios.
