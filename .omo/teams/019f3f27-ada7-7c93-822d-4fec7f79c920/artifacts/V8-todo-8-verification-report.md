# V8 Todo 8 Verification Report

Timestamp: 2026-07-08T14:28:01+0900

Thread: V8 verify-docs-readiness (`codex://threads/019f402e-efaf-7dc1-b884-7ea6e809f713`)
Target: Todo 8 docs/evidence/local readiness DoneClaim from H (`codex://threads/019f4027-c5fb-7bc3-9c8e-3ea51d075ca7`)

## Verdict

VerificationClaim: Todo 8 APPROVED

## Manual QA Confirmation

- Product doc centers collection workflow judgment rather than legal-doc automation:
  - `docs/product/debt-collection-ontology/claim-domain-ontology-v1.md:36` introduces "Collection Workflow Judgment Brain".
  - `docs/product/debt-collection-ontology/claim-domain-ontology-v1.md:38` says workflow judgment is the center of the product surface.
  - `docs/product/debt-collection-ontology/claim-domain-ontology-v1.md:57` keeps product identity as collection workflow intelligence.
- Support-layer relationship is explicit:
  - `docs/product/debt-collection-ontology/claim-domain-ontology-v1.md:48` states legal, evidence, finance, and StopGate are support layers.
  - `docs/product/debt-collection-ontology/claim-domain-ontology-v1.md:52-55` defines legal checkpoints, evidence quality, finance bridge, and operator playbook support/forbidden roles.
  - `.omo/evidence/debt-brain-structural-depth-v1/final-summary.md:9` repeats the support-layer boundary.
- Non-execution/deployment boundaries are explicit:
  - `docs/product/debt-collection-ontology/claim-domain-ontology-v1.md:13` forbids filing, debtor contact, payment demands, ledger mutation, seizure, and authoritative balances.
  - `docs/product/debt-collection-ontology/claim-domain-ontology-v1.md:180-200` keeps action packets review-only and forbids executable/contact/filing/payment fields.
  - `docs/product/debt-collection-ontology/claim-domain-ontology-v1.md:315` and `:321` state no remote deploy/smoke/client setup changes and local readiness only.
  - `.omo/evidence/debt-brain-structural-depth-v1/final-summary.md:38` states no remote deploy/smoke/client docs/admin/write/contact/filing/seizure/payment/ledger/balance claim.
- Manual scenario QA rerun passed:
  - `MANUAL_QA_APPROVED scenarios=8 ids=premature_litigation_review,evidence_completion_loop,title_acquisition_loop,asset_discovery_loop,enforcement_ready_review,monitoring_low_yield,finance_reconciliation_hold,insolvency_protected_asset_hold`.

## Commands Rerun

- `uv run --with pytest --with pydantic --with typing-extensions python -m pytest tests/unit/legal_ontology/test_operator_playbook_v1.py tests/unit/legal_ontology/test_workflow_judgments_v1.py tests/unit/legal_ontology/test_evidence_quality_v1.py tests/unit/legal_ontology/test_finance_claim_model_v1.py tests/unit/legal_ontology/test_domain_decision_engine_v1.py tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py -q`
  - Result: `28 passed`, one existing `asyncio_mode` pytest config warning.
- `uv run --with pytest --with pydantic --with typing-extensions python -m pytest tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py tests/unit/legal_ontology/test_stop_gates_domain_v1.py tests/unit/legal_ontology/test_route_decisions_v1.py tests/unit/legal_ontology/test_action_packets_v1.py -q`
  - Result: `18 passed`, one existing `asyncio_mode` pytest config warning.
- `python3 -m pytest --version`
  - Result: failed with `No module named pytest`, confirming the documented system-Python caveat.
- `python3 -m compileall trustgraph_legal tests/unit/legal_ontology tests/integration/legal_ontology`
  - Result: passed.
- `git diff --check`
  - Result: passed.
- JSON validation over resources, claim-domain fixtures, and structural-depth evidence.
  - Result: `JSON_VALIDATION_OK files=21`.
- `uv run --with pydantic --with typing-extensions python` MCP order smoke.
  - Result: `MCP_ORDER_OK count=25 tail=list_claim_domain_routes,explain_collection_workflow_state,evaluate_claim_domain_decision,explain_claim_action_packet`.
- Narrow structural-depth basedpyright:
  - Command covered `trustgraph_legal/workflow_judgments.py`, `domain_workflow_integration.py`, `evidence_quality.py`, `finance_review_bridge.py`, `legal_workflow_checkpoints.py`, `domain_decisions.py`, and structural-depth unit/integration tests.
  - Result: `0 errors, 0 warnings, 0 notes`.
- Broader typecheck including older MCP facade files:
  - Result: `0 errors, 17 warnings, 0 notes`; warnings are in older `mcp_domain.py` deprecated typing and `mcp_claim_domain_handlers.py` `Any` typing. Treated as documented broad-scope caveat, not a Todo 8 blocker.
- Deliverable safety scan over structural-depth evidence, product ontology doc, resources, and claim-domain fixture files.
  - Result: `NO_FINDINGS files=31`.
- Scope fidelity text check.
  - Result: `SCOPE_FIDELITY_APPROVED workflow_first support_layers_ok local_only_ok`.
- Changed-path/deployment-doc check.
  - Result: `PLAN_COMPLIANCE_APPROVED no_client_deploy_docs no_public_admin_write_claims`.

## Caveats

- System `python3` does not have pytest installed; uv-based equivalents passed and are acceptable for this repository's current local checks.
- A broad all-docs scan is noisy because older docs/API/spec material and older working-log notes contain remote MCP/auth/env examples. Those are outside Todo 8 and not edited by the claimed docs-readiness work.
- A broader basedpyright run that includes older MCP facade files reports warnings outside the narrowed structural-depth changed-file scope. The structural-depth scoped typecheck is clean.
- Remote MCP deployment and remote live smoke remain explicitly deferred; Todo 8 only proves local deploy-readiness.

## Risks

- The final readiness claim depends on preserving the explicit local-only/deferred-deployment wording; future productization work should not reuse this evidence as proof of remote deployment.
- Older broad docs still mention remote/auth examples, so future public/client documentation work should do a separate deployment-doc review.

## Decision

APPROVE Todo 8.
