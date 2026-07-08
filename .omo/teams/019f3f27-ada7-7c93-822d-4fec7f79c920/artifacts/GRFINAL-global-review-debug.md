# GRFINAL Global Review + Debugging Gate

GlobalReviewDebuggingClaim: APPROVED

Timestamp: 2026-07-08T15:31+09:00

Scope: final verifier/debugging audit after the RW1/RW3 blocker, Todo 6/7 real-boundary reopen fix, Todo 8 refresh, and F1-F4 refresh approvals. No product code, docs, tests, or evidence files were edited by this verifier. This artifact is the only file added.

## Read-First Inputs

- `.omo/teams/019f3f27-ada7-7c93-822d-4fec7f79c920/guide.md`
- `.omo/teams/019f3f27-ada7-7c93-822d-4fec7f79c920/team.json`
- `.omo/plans/debt-brain-structural-depth-v1.md`
- `.omo/start-work/ledger.jsonl` recent entries
- `.omo/teams/019f3f27-ada7-7c93-822d-4fec7f79c920/artifacts/RW1-goal-constraints-review.md`
- `.omo/teams/019f3f27-ada7-7c93-822d-4fec7f79c920/artifacts/RW3-code-quality-review.md`
- `.omo/teams/019f3f27-ada7-7c93-822d-4fec7f79c920/artifacts/RV67R-reverify-real-boundary.md`
- `.omo/teams/019f3f27-ada7-7c93-822d-4fec7f79c920/artifacts/V8-todo-8-refresh-verification-report.md`
- `.omo/teams/019f3f27-ada7-7c93-822d-4fec7f79c920/artifacts/FINAL1-refresh-plan-compliance-report.md`
- `.omo/teams/019f3f27-ada7-7c93-822d-4fec7f79c920/artifacts/final2-refresh-code-quality.md`
- `.omo/teams/019f3f27-ada7-7c93-822d-4fec7f79c920/artifacts/final3-refresh-manual-qa-report.md`
- `.omo/teams/019f3f27-ada7-7c93-822d-4fec7f79c920/artifacts/final4-scope-fidelity-refresh-report.md`

## Plan Status

`PLAN_CHECKBOXES_OK top_level=8 final=4`

All top-level todos 1-8 and final checks F1-F4 are checked in `.omo/plans/debt-brain-structural-depth-v1.md`.

## Prior Blocker Verdict

RW1/RW3 blocker is fixed.

The previous failure was that standalone workflow unit tests could produce distinct stages, but the real `evaluate_claim_domain_decision` and MCP boundary collapsed the eight semireal scenarios to `evidence_completion` / `evidence_completion_loop`.

Current direct domain and MCP runtime QA now returns exact expected `current_stage`, first action, `posture`, and `remediation_loop` for all eight semireal scenarios:

- `premature_litigation_review`: `title_acquisition` / `confirm_service_finality_execution_clause` / `resolve_title_service_finality_and_execution_clause_before_enforcement` / `legal_precondition_review_loop`
- `evidence_completion_loop`: `evidence_completion` / `collect_missing_evidence` / `complete_source_backed_fact_package_before_escalation` / `evidence_completion_loop`
- `title_acquisition_loop`: `title_acquisition` / `acquire_or_confirm_title` / `resolve_title_service_finality_and_execution_clause_before_enforcement` / `title_acquisition_loop`
- `asset_discovery_loop`: `asset_discovery` / `enrich_asset_signals` / `enrich_asset_targets_and_exemption_risk_before_route_selection` / `asset_discovery_loop`
- `enforcement_ready_review`: `enforcement_ready` / `prepare_advisory_packet` / `prepare_review_packet_only_after_route_and_guardrail_readiness` / `legal_precondition_review_loop`
- `monitoring_low_yield`: `monitoring` / `monitor_retry` / `hold_low_yield_or_blocked_case_with_review_trigger` / `low_yield_monitoring_loop`
- `finance_reconciliation_hold`: `evidence_completion` / `reconcile_finance` / `complete_source_backed_fact_package_before_escalation` / `finance_reconciliation_loop`
- `insolvency_protected_asset_hold`: `insolvency_protected_asset_review` / `insolvency_protected_asset_review` / `hold_or_redirect_before_enforcement_ready_judgment` / `protected_asset_insolvency_hold`

Runtime result:

`GRFINAL_DIRECT_MCP_QA_APPROVED scenarios=8 exact_stage_action_posture_loop=pass unsafe_fields=absent direct_mcp_equal=true`

## Implementation Boundary Review

- `trustgraph_legal/domain_decisions.py` calls `build_domain_workflow_output(...)` and returns additive `workflow_judgment` and `operator_next_steps`.
- `trustgraph_legal/domain_workflow_integration.py` reads the generic support fields `evidence_checkpoint`, `finance_bridge`, and `legal_checkpoints` from `claim_domain_payload`, before deterministic fallback logic.
- `trustgraph_legal/workflow_judgments.py` consumes evidence, finance, and legal support surfaces, strips unsafe raw/authority fields from review items, and keeps `advisory_only_human_review_required`.
- `tests/utils/claim_domain_pipeline_support.py` projects fixture `workflow_support` into the same standard payload fields; product code does not consume `workflow_support` directly.
- Product scan over `trustgraph_legal` and `scripts/legal_ontology` found no product branching on `scenario_id`, `expected_workflow`, `expected_label`, or `workflow_support`. Hits were generic workflow strings in product logic or fixture/test helper fields outside the product path.

## Debugging Hypotheses

### H1: If `workflow_support` projection is stripped, scenarios collapse back to evidence_completion.

Confirmed, with safe behavior.

Probe removed `evidence_checkpoint`, `finance_bridge`, and `legal_checkpoints` from each adapted scenario payload before calling `evaluate_claim_domain_decision`. Seven of eight scenarios collapsed to the conservative evidence-completion fallback; the evidence-completion scenario remained exact. All stripped-support outputs retained advisory-only human-review semantics and human-review actions.

Result:

`GRFINAL_H1_STRIPPED_SUPPORT_FALLBACK scenarios=8 unsafe=0`

Documentation check:

- `docs/product/debt-collection-ontology/claim-domain-ontology-v1.md` states the boundary must preserve `evidence_checkpoint`, `finance_bridge`, and `legal_checkpoints`; if absent, deterministic fallback logic remains conservative and review-safe.
- `.omo/evidence/debt-brain-structural-depth-v1/final-summary.md` states `domain_workflow_integration` consumes generic structured fields before deterministic fallbacks.
- `.omo/evidence/debt-brain-structural-depth-v1/final-validation.json` records `deterministic_fallbacks_preserved: true`.

### H2: Product code branches on scenario IDs or expected labels.

Refuted.

Command:

`rg -n "scenario_id|expected_workflow|expected_label|workflow_support|premature_litigation_review|title_acquisition_loop|asset_discovery_loop|enforcement_ready_review|monitoring_low_yield|finance_reconciliation_hold|insolvency_protected_asset_hold" trustgraph_legal scripts/legal_ontology --glob '*.py'`

Result: no scenario-id/expected-label branch in product modules. Only generic workflow stage/remediation strings were found in product logic.

### H3: MCP handler diverges from direct domain decision.

Refuted.

Runtime QA drove all eight scenarios through both direct `evaluate_claim_domain_decision(...)` and local MCP `invoke_tool("evaluate_claim_domain_decision", ...)`. For each scenario, direct and MCP `workflow_judgment` matched exactly, including stage/action/posture/remediation loop.

Result:

`GRFINAL_DIRECT_MCP_QA_APPROVED scenarios=8 exact_stage_action_posture_loop=pass unsafe_fields=absent direct_mcp_equal=true`

### H4: Structured support surfaces introduce unsafe raw/PII/authority fields.

Refuted for the scoped structural-depth surface and live outputs.

Runtime QA recursively rejected forbidden output keys: `raw_text`, `source_text`, `body`, `excerpt`, `source_path`, `debtor_contact_payload`, `filing_destination`, `court_destination`, `court_destination_payload`, `remaining_balance`, and `collectable_balance_authority`.

Scoped static safety result:

`SCOPED_STRUCTURAL_DEPTH_NO_FINDINGS files=18`

## Commands and Results

- Required artifact presence:
  - `REQUIRED_ARTIFACTS_PRESENT count=8`
- Plan checkbox check:
  - `PLAN_CHECKBOXES_OK top_level=8 final=4`
- Focused structural-depth pytest:
  - `uv run --with pytest --with pytest-asyncio --with pytest-mock --with pytest-cov --with pydantic --with typing-extensions --with pyyaml python -m pytest tests/unit/legal_ontology/test_operator_playbook_v1.py tests/unit/legal_ontology/test_workflow_judgments_v1.py tests/unit/legal_ontology/test_evidence_quality_v1.py tests/unit/legal_ontology/test_finance_claim_model_v1.py tests/unit/legal_ontology/test_domain_decision_engine_v1.py tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py -q`
  - Result: `28 passed in 3.01s`
- Regression pytest:
  - `uv run --with pytest --with pytest-asyncio --with pytest-mock --with pytest-cov --with pydantic --with typing-extensions --with pyyaml python -m pytest tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py tests/unit/legal_ontology/test_stop_gates_domain_v1.py tests/unit/legal_ontology/test_route_decisions_v1.py tests/unit/legal_ontology/test_action_packets_v1.py -q`
  - Result: `18 passed in 0.35s`
- Reopened boundary/domain/MCP pytest:
  - `uv run --with pytest --with pytest-asyncio --with pytest-mock --with pytest-cov --with pydantic --with typing-extensions --with pyyaml python -m pytest tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py tests/unit/legal_ontology/test_workflow_judgments_v1.py tests/unit/legal_ontology/test_domain_decision_engine_v1.py tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py -q`
  - Result: `17 passed in 2.70s`
- Direct/MCP eight-scenario QA:
  - Result: `GRFINAL_DIRECT_MCP_QA_APPROVED scenarios=8 exact_stage_action_posture_loop=pass unsafe_fields=absent direct_mcp_equal=true`
- Stripped-support fallback probe:
  - Result: `GRFINAL_H1_STRIPPED_SUPPORT_FALLBACK scenarios=8 unsafe=0`
- JSON validation:
  - Result: `JSON_VALIDATION_OK files=21`
- MCP tool-order smoke:
  - Result: `MCP_ORDER_OK count=25 tail=list_claim_domain_routes,explain_collection_workflow_state,evaluate_claim_domain_decision,explain_claim_action_packet`
- Compile:
  - `python3 -m compileall trustgraph_legal tests/unit/legal_ontology tests/integration/legal_ontology`
  - Result: passed
- Scoped structural-depth typecheck:
  - `uv run --with basedpyright --with pytest --with pydantic --with typing-extensions basedpyright trustgraph_legal/domain_decisions.py trustgraph_legal/domain_workflow_integration.py trustgraph_legal/workflow_judgments.py tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py tests/unit/legal_ontology/test_workflow_judgments_v1.py tests/utils/claim_domain_pipeline_support.py tests/utils/workflow_scenario_expectations.py`
  - Result: `0 errors, 0 warnings, 0 notes`
- Extra MCP handler type probe:
  - Same typecheck with `trustgraph_legal/mcp_claim_domain_handlers.py` included
  - Result: `0 errors, 1 warning` at `mcp_claim_domain_handlers.py:202` (`reportAny` on local variable `raw`)
- Scoped lint:
  - `uv run --with ruff ruff check trustgraph_legal/domain_decisions.py trustgraph_legal/domain_workflow_integration.py trustgraph_legal/workflow_judgments.py trustgraph_legal/mcp_claim_domain_handlers.py tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py tests/unit/legal_ontology/test_workflow_judgments_v1.py tests/utils/claim_domain_pipeline_support.py tests/utils/workflow_scenario_expectations.py`
  - Result: `All checks passed!`
- Scoped safety scan:
  - Result: `SCOPED_STRUCTURAL_DEPTH_NO_FINDINGS files=18`
- Whitespace:
  - `git diff --check`
  - Result: passed

## Guardrails

- Product center remains workflow judgment: current stage, posture, next operational action, missing inputs, review/remediation loop, and source-backed reasons.
- Legal, evidence, finance, StopGate, and operator playbook remain support layers.
- Workflow output remains advisory-only and human-review-gated.
- No remote MCP deployment, remote smoke, admin/write tool, debtor contact, filing, seizure, payment demand, production ledger mutation, or authoritative balance output was observed or claimed in the checked structural-depth surfaces.
- MCP local tool order remains 25 with the expected claim-domain tail.

## Caveats and Residual Risks

- Post-GRFINAL caveat hardening supersedes the top-level-only support-field caveat: `domain_workflow_integration` now preserves exact semireal workflow behavior when `evidence_checkpoint`, `finance_bridge`, and `legal_checkpoints` are present either at the adapter payload top level or nested under `workflow_support`. If all structured support is stripped, the real boundary still falls back conservatively to evidence completion and remains advisory-only.
- A broad safety scan over all product docs and `trustgraph_legal` still finds pre-existing remote/auth environment-token names in older MCP lab docs and `trustgraph_legal/lab_trace.py`. The scoped structural-depth surfaces and live outputs are clean.
- Post-GRFINAL caveat hardening also removed the extra strict `mcp_claim_domain_handlers.py` type warning by using the typed JSON loader boundary; the handler-inclusive scoped basedpyright probe is now clean.
- System `/usr/bin/python3` is Python 3.9.6 and lacks this repo's pytest/test-helper compatibility; runtime tests were run through the repo's `uv` flow with explicit dependencies.
- The shared worktree was already dirty with team-wave changes before this verifier wrote its artifact. I did not revert or modify those changes.

## Blockers

None.

## Decision

GlobalReviewDebuggingClaim: APPROVED
