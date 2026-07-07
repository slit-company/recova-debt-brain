# I route-decision-table report

## Scope
- Member: I / route-decision-table
- Todo: 7. Add route decision table and priority scoring v1
- Branch: `team/team-8953292e/I`

## Deliverables
- Added `resources/decision_tables/debt_collection_route_decisions_v1.json`.
- Added `trustgraph_legal/route_decisions.py`.
- Added `scripts/legal_ontology/validate_route_decisions_v1.py`.
- Added `scripts/legal_ontology/route_decision_validation_common.py`.
- Added `tests/unit/legal_ontology/test_route_decisions_v1.py`.
- Generated task-7 evidence under `.omo/evidence/debt-collection-domain-ontology-v1/`.
- Commit: final hash reported in the DONE handoff.

## Contract
- Decision table version: `recova-debt-collection-route-decisions@v1.0.0`.
- Decision rows: 32, one for every route in `recova-debt-collection-routes@v1.0.0`.
- Statuses: `possible`, `review_required`, `blocked`, and `missing_facts`.
- Scoring: deterministic component weights only, capped at 0..100, with tie-breaker order `status_priority`, `priority_score_desc`, `legal_source_review_status`, `workflow_state_order`, `route_id_asc`.
- Traceability: route facts, workflow preconditions, legal-source review requirements, finance review triggers, StopGate-style advisory blockers, score components, and reason templates all carry source refs.
- StopGate coordination: Todo 7 does not depend on v0 behavior changes. It preserves shared reason names where applicable and models domain-v1 advisory blockers/review reasons for Todo 9/10/11 consumption.
- Execution boundary: every decision remains advisory-only with `direct_execution_allowed: false` and `non_execution_semantics: advisory_only_human_review_required`.

## Verification
- `PASS` focused pytest for `tests/unit/legal_ontology/test_route_decisions_v1.py`.
- `PASS` route decision validator over the new decision table and Todo 4-6 dependency resources.
- `PASS` JSON parsing over the decision table and task-7 happy/failure evidence.
- `PASS` Python bytecode compilation over changed Python files.
- `PASS basedpyright --level error` over changed Python/test files.
- Size check: all changed Python/test files are below 250 pure LOC.
- PII/path scan: recorded in task-7 evidence with no findings.

## Evidence
- `.omo/evidence/debt-collection-domain-ontology-v1/task-7-route-decision-happy.json`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-7-route-decision-failure.json`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-7-route-validator.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-7-focused-pytest.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-7-json-tool.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-7-py-compile.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-7-basedpyright-errors.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-7-size-check.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-7-pii-path-scan.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-7-diff-check.txt`
