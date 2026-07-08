# V67 Verification - Todo 6 and Todo 7

Verifier: V67 verify-domain-scenarios
Thread: codex://threads/019f401e-d766-7030-af83-d5374e1f70e3

## Verdicts

VerificationClaim: Todo 6 APPROVED
VerificationClaim: Todo 7 APPROVED

## Summary

Todo 6 domain/MCP integration is approved. The MCP registry remains 25 tools with the existing claim-domain tail, domain and MCP decision surfaces preserve existing fields and add `workflow_judgment` plus `operator_next_steps`, and all checked outputs remain advisory-only and redacted.

Todo 7 workflow scenario coverage is approved after G's addendum fixed the prior basedpyright blocker. Runtime tests, type checks, lint, compile, JSON validation, manual QA, and safety scans are now clean.

## Resolved Finding

- Todo 7: prior `tests/unit/legal_ontology/workflow_scenario_requests.py:90` basedpyright failure is resolved. The helper now shapes the legal checkpoint/review payload as `JsonObject` with `list[JsonValue]` fields before passing it to `WorkflowJudgmentRequest`.

## Commands

- `uv run --with pytest --with pydantic python -m pytest tests/unit/legal_ontology/test_domain_decision_engine_v1.py tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py tests/unit/legal_ontology/test_workflow_judgments_v1.py`
  - Result: 17 passed, 1 existing pytest config warning for `asyncio_mode`.
- `uv run --with pydantic python -m compileall trustgraph_legal tests/unit/legal_ontology tests/integration/legal_ontology tests/utils/workflow_scenario_expectations.py`
  - Result: passed.
- `uv run --with ruff ruff check trustgraph_legal/domain_workflow_integration.py trustgraph_legal/domain_decisions.py trustgraph_legal/mcp_claim_domain_handlers.py tests/unit/legal_ontology/test_domain_decision_engine_v1.py tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py tests/unit/legal_ontology/test_workflow_judgments_v1.py tests/unit/legal_ontology/workflow_scenario_requests.py tests/utils/workflow_scenario_expectations.py`
  - Result: passed.
- `uv run --with basedpyright --with pytest --with pydantic basedpyright trustgraph_legal/domain_workflow_integration.py trustgraph_legal/domain_decisions.py tests/unit/legal_ontology/test_domain_decision_engine_v1.py tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py`
  - Result: 0 errors, 0 warnings, 0 notes.
- `uv run --with basedpyright --with pytest --with pydantic basedpyright tests/unit/legal_ontology/workflow_scenario_requests.py tests/utils/workflow_scenario_expectations.py tests/unit/legal_ontology/test_workflow_judgments_v1.py tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py`
  - Result after addendum: 0 errors, 0 warnings, 0 notes.
- `uv run --with basedpyright --with pytest --with pydantic basedpyright trustgraph_legal/domain_workflow_integration.py trustgraph_legal/domain_decisions.py tests/unit/legal_ontology/test_domain_decision_engine_v1.py tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py tests/unit/legal_ontology/workflow_scenario_requests.py tests/utils/workflow_scenario_expectations.py tests/unit/legal_ontology/test_workflow_judgments_v1.py`
  - Result after addendum: 0 errors, 0 warnings, 0 notes.
- `uv run --with pydantic python -m py_compile tests/unit/legal_ontology/workflow_scenario_requests.py`
  - Result after addendum: passed.
- `python3 -m json.tool tests/fixtures/claim-domain-v1/synthetic_claim_states.json >/dev/null`
  - Result: passed.
- `python3 -m json.tool .omo/evidence/debt-brain-structural-depth-v1/task-6-domain-integration.json >/dev/null`
  - Result: passed.
- `python3 -m json.tool .omo/evidence/debt-brain-structural-depth-v1/task-7-scenario-coverage.json >/dev/null`
  - Result: passed.

## Manual QA

- MCP tool order: `count=25`, claim-domain tail is `list_claim_domain_routes`, `explain_collection_workflow_state`, `evaluate_claim_domain_decision`, `explain_claim_action_packet`.
- Manual decision probe covered all 34 fixture scenarios through both direct domain evaluation and MCP `evaluate_claim_domain_decision`.
- Old decision fields remained present: `claim_ref`, `workflow_state`, `route_decisions`, `review_items`, `action_packet_candidates`, `source_refs`, `resource_versions`, `pii_profile`, `non_execution_semantics`.
- Additive fields were present: `workflow_judgment`, `operator_next_steps`.
- Operator steps were advisory-only: `review_status=human_review_required`, `non_execution_semantics=advisory_only_human_review_required`, with no command/mutation/deploy authority fields.
- Todo 7 relax decision is legitimate: integration asserts workflow envelope compatibility, while unit coverage asserts deterministic exact `stage`, `action`, `posture`, and `remediation_loop` for the 8 semireal scenarios using explicit support surfaces.

## Safety

- Fixture has 34 scenarios and all 8 required semireal workflow expectation rows.
- Safety scan found no forbidden fixture keys: `raw_text`, `source_text`, `raw_excerpt`, `body`, `source_path`, `debtor_contact_payload`, `filing_destination`, `court_destination_payload`, `remaining_balance`, `collectable_balance_authority`, `execution_command`.
- Evidence/fixture scan found no PII values or local paths such as `010-`, `900101-`, `/Users/`, raw debtor statement text, or leaked auth tokens.
- Static scan only found expected PII profile flags in the fixture and Todo 6 evidence's absent-field list.
- Todo 8/docs/deploy-readiness remains downstream; no remote deploy or production mutation was observed in the verified Todo 6/7 surfaces.

## Risks

- The existing pytest warning for `asyncio_mode` is unrelated to Todo 6/7 behavior but remains present.

## Addendum Recheck

G's addendum changed only `tests/unit/legal_ontology/workflow_scenario_requests.py`. Re-inspection found a narrow type-shaping fix with unchanged scenario semantics. Re-run results: combined Todo 6/7 pytest 17 passed, compileall passed, ruff passed, combined basedpyright passed 0/0/0, manual MCP/domain QA passed across 34 scenarios, JSON validation passed, and safety scan passed.
