# RV67R Reverify Real Boundary

VerificationClaim: Todo 6/7 REOPEN FIX APPROVED

## Scope

Independent re-verification of the reopened Todo 6/7 blocker: the real `evaluate_claim_domain_decision` and MCP `evaluate_claim_domain_decision` surfaces must consume structured workflow support and return distinct semireal workflow outcomes instead of collapsing to `evidence_completion`.

No product, test, or evidence files were edited by this verifier. This artifact is the only file added.

## Code Inspection

- `trustgraph_legal/domain_decisions.py` now calls `build_domain_workflow_output(...)` and includes `workflow_judgment` plus `operator_next_steps` in the public decision output.
- `trustgraph_legal/domain_workflow_integration.py` consumes structured `evidence_checkpoint`, `finance_bridge`, and `legal_checkpoints` generically from the claim-domain payload, with fallback evidence/finance derivation where explicit support is absent.
- `tests/utils/claim_domain_pipeline_support.py` projects fixture `workflow_support` into those top-level structured fields before the domain/MCP boundary.
- Product code search found no `scenario_id`, `expected_workflow`, or `workflow_support` field dependency in `trustgraph_legal/domain_decisions.py`, `trustgraph_legal/domain_workflow_integration.py`, or `trustgraph_legal/workflow_judgments.py`. Generic remediation-loop strings do appear in product logic, but no scenario-id/test-label branching was found.
- `tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py` now asserts exact workflow stage/action/posture/remediation expectations at both domain and MCP surfaces.

## Commands and Results

- `uv run --with pytest --with pydantic --with typing-extensions python -m pytest tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py tests/unit/legal_ontology/test_workflow_judgments_v1.py -q`
  - Result: 9 passed, 1 existing pytest config warning for unknown `asyncio_mode`.
- `uv run --with pytest --with pydantic --with typing-extensions python -m pytest tests/unit/legal_ontology/test_domain_decision_engine_v1.py tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py -q`
  - Result: 8 passed, 1 existing pytest config warning for unknown `asyncio_mode`.
- `python3 -m compileall trustgraph_legal/domain_decisions.py trustgraph_legal/domain_workflow_integration.py trustgraph_legal/workflow_judgments.py tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py tests/unit/legal_ontology/test_workflow_judgments_v1.py tests/utils/claim_domain_pipeline_support.py tests/utils/workflow_scenario_expectations.py`
  - Result: passed.
- `uv run --with basedpyright --with pytest --with pydantic --with typing-extensions basedpyright trustgraph_legal/domain_decisions.py trustgraph_legal/domain_workflow_integration.py trustgraph_legal/workflow_judgments.py tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py tests/unit/legal_ontology/test_workflow_judgments_v1.py tests/utils/claim_domain_pipeline_support.py tests/utils/workflow_scenario_expectations.py`
  - Result: 0 errors, 0 warnings, 0 notes.
- `uv run --with ruff ruff check trustgraph_legal/domain_decisions.py trustgraph_legal/domain_workflow_integration.py trustgraph_legal/workflow_judgments.py tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py tests/unit/legal_ontology/test_workflow_judgments_v1.py tests/utils/claim_domain_pipeline_support.py tests/utils/workflow_scenario_expectations.py`
  - Result: All checks passed.
- JSON validation over `resources`, `tests/fixtures/claim-domain-v1`, and `.omo/evidence/debt-brain-structural-depth-v1`
  - Result: `JSON_VALIDATION_OK files=21`.
- MCP order smoke
  - Result: `MCP_ORDER_OK count=25 tail=list_claim_domain_routes,explain_collection_workflow_state,evaluate_claim_domain_decision,explain_claim_action_packet`.
- Scoped Todo 6/7 safety scan over evidence, fixtures, changed Todo 6/7 tests/utilities, and workflow/domain product files
  - Result: `SCOPED_NO_FINDINGS files=20`.
- Product scenario/test label scan
  - Result: `NO_PRODUCT_SCENARIO_ID_OR_TEST_EXPECTATION_FIELDS files=3`.

## Direct QA

Direct manual QA script drove all eight named semireal scenarios through both `evaluate_claim_domain_decision` and MCP `invoke_tool("evaluate_claim_domain_decision", ...)`, asserting exact stage, action, posture, remediation loop, advisory-only semantics, and no forbidden raw/contact/filing/balance fields.

Result:

`DIRECT_QA_APPROVED scenarios=8 surfaces=domain,mcp exact_stage_action_posture_loop=pass`

Scenario lines:

- `premature_litigation_review`: `title_acquisition` / `confirm_service_finality_execution_clause` / `resolve_title_service_finality_and_execution_clause_before_enforcement` / `legal_precondition_review_loop`
- `evidence_completion_loop`: `evidence_completion` / `collect_missing_evidence` / `complete_source_backed_fact_package_before_escalation` / `evidence_completion_loop`
- `title_acquisition_loop`: `title_acquisition` / `acquire_or_confirm_title` / `resolve_title_service_finality_and_execution_clause_before_enforcement` / `title_acquisition_loop`
- `asset_discovery_loop`: `asset_discovery` / `enrich_asset_signals` / `enrich_asset_targets_and_exemption_risk_before_route_selection` / `asset_discovery_loop`
- `enforcement_ready_review`: `enforcement_ready` / `prepare_advisory_packet` / `prepare_review_packet_only_after_route_and_guardrail_readiness` / `legal_precondition_review_loop`
- `monitoring_low_yield`: `monitoring` / `monitor_retry` / `hold_low_yield_or_blocked_case_with_review_trigger` / `low_yield_monitoring_loop`
- `finance_reconciliation_hold`: `evidence_completion` / `reconcile_finance` / `complete_source_backed_fact_package_before_escalation` / `finance_reconciliation_loop`
- `insolvency_protected_asset_hold`: `insolvency_protected_asset_review` / `insolvency_protected_asset_review` / `hold_or_redirect_before_enforcement_ready_judgment` / `protected_asset_insolvency_hold`

## Guardrails

- Advisory-only semantics: passed at domain and MCP workflow surfaces.
- No authoritative finance balance in domain/MCP decision payloads: passed direct QA and unit guardrails.
- No execution/contact/filing payloads in domain/MCP decision payloads: passed direct QA and unit/integration guardrails.
- MCP tool order/count: passed, count remains 25 with claim-domain tools appended after existing 21.

## Residual Risks

- The broad plan safety scan over all `docs/product/debt-collection-ontology` still reports environment-variable names in pre-existing MCP lab docs (`MCP_LAB_BEARER_TOKEN`, `SUPABASE_SERVICE_ROLE_KEY`). Those docs are not part of the Todo 6/7 reopen fix surface and were not changed by this verifier; the scoped Todo 6/7 safety scan passed.
- Legal checkpoints are consumed when the structured `legal_checkpoints` support surface is present. The fallback path still returns `None` rather than deriving legal checkpoints from StopGate resources automatically; this is acceptable for the reopened blocker because the claimed fix was structured support projection and both public boundaries now consume it.

## Blockers

None for Todo 6/7 reopen fix.
