# F Workflow States Report

Member: F `workflow-states`
Commit: `31f01756 feat(legal-domain): add collection workflow states`
Branch: `team/team-8953292e/F`

## Changed Files

- `resources/workflows/debt_collection_workflow_v1.json`
- `scripts/legal_ontology/validate_workflow_v1.py`
- `tests/unit/legal_ontology/test_workflow_v1.py`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-5-*`

## What Landed

- Added workflow v1 with the 12 required canonical states:
  `intake`, `identity_evidence_package`, `limitation_review`, `title_acquisition`,
  `service_finality_execution_clause`, `voluntary_recovery`, `provisional_remedy`,
  `asset_discovery`, `execution_route_selection`, `insolvency_discharge_review`,
  `monitoring_retry`, and `closure`.
- Modeled state preconditions, exit conditions, required evidence, review states,
  blocked review branches, monitoring retry returns, and terminal closure.
- Kept route eligibility separable: each state uses
  `workflow_precondition_only_no_route_decision_logic`; no route scoring or route
  decision logic is encoded in the workflow resource.
- Added validator cross-checks for required state order, source refs against
  domain sources v1, transition endpoints, review-state catalog entries, loop
  states, and non-execution semantics.

## Evidence

- Focused pytest: `.omo/evidence/debt-collection-domain-ontology-v1/task-5-focused-pytest.txt`
- JSON parse: `.omo/evidence/debt-collection-domain-ontology-v1/task-5-json-tool.txt`
- Validator happy: `.omo/evidence/debt-collection-domain-ontology-v1/task-5-workflow-validator.txt`
- Validator failure: `.omo/evidence/debt-collection-domain-ontology-v1/task-5-workflow-validator-failure.txt`
- PII/path scan: `.omo/evidence/debt-collection-domain-ontology-v1/task-5-pii-path-scan.txt`
- py_compile: `.omo/evidence/debt-collection-domain-ontology-v1/task-5-py-compile.txt`
- basedpyright errors: `.omo/evidence/debt-collection-domain-ontology-v1/task-5-basedpyright-errors.txt`
- Size check: `.omo/evidence/debt-collection-domain-ontology-v1/task-5-size-check.txt`
- Diff check: `.omo/evidence/debt-collection-domain-ontology-v1/task-5-diff-check.txt`
- Isolation proof: `.omo/evidence/debt-collection-domain-ontology-v1/task-5-isolation-proof.txt`

## Verification

- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_workflow_v1.py -q` passed: 3 tests.
- Validator happy output: `PASS workflow recova-debt-collection-workflow@v1.0.0 states=12 transitions=23 loops=2 source_refs=94`.
- Invalid transition target fails with `unknown to_state unknown_workflow_state`.
- `python3 -m json.tool resources/workflows/debt_collection_workflow_v1.json` passed.
- `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m py_compile ...` passed.
- LSP diagnostics: no errors for changed Python files.
- `basedpyright --level error ...` reported no errors.
- PII/path scan: `NO_FINDINGS`.
- `git diff --check` and `git diff --cached --check` passed.
- Size check: validator 248 pure LOC; test 76 pure LOC.

## Residual Risks

- This slice is a workflow-state contract only. Route v1, route decision tables,
  action packets, MCP tools, and the decision engine still need to consume these
  workflow states in later todos.
- Workflow state source refs are intentionally tied to
  `debt_collection_domain_sources_v1.json`; if Todo 9 replaces legacy bundle refs
  with article-level StopGate refs, the workflow source map should be reviewed in
  that same pass.
