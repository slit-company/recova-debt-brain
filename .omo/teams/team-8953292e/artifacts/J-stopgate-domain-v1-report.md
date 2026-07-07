# J stopgate-domain-v1 report

## Outcome

Implemented Todo 9 as an opt-in domain-v1 StopGate surface while preserving the existing v0 `evaluate_case_graph` default behavior.

Commit: `c9aa656a` (`feat(legal-check): expand domain stop gates v1`)

## Delivered

- Added `resources/legal_rules/debt_collection_stopgate_domain_v1.json`.
- Added `trustgraph_legal/stop_gates_domain_v1.py` for explicit domain-v1 evaluation.
- Added `trustgraph_legal/stopgate_domain_resources.py` for curated source and route catalog loading.
- Added `tests/unit/legal_ontology/test_stop_gates_domain_v1.py`.
- Wrote task-9 happy/failure evidence under `.omo/evidence/debt-collection-domain-ontology-v1/`.

## Domain-v1 Reason Codes

Preserved v0-compatible codes where applicable:

- `limitation_risk`
- `discharge_proceeding_detected`
- `exempt_claim_targeted`
- `missing_enforcement_title`
- `missing_execution_clause`
- `amount_mismatch`

Added explicit domain-v1 advisory blockers/review reasons:

- `welfare_public_benefit_protected`
- `domain_legal_source_unapproved`
- `missing_service_finality_execution_clause_proof`
- `ambiguous_or_excessive_balance`
- `unsupported_contact_or_recovery_route`
- `route_legal_source_uncertain`

All v1 rules return advisory `보류` blockers/review reasons. No direct execution semantics were added.

## Isolation Repair

Incident: the first red test file was initially added in the parent checkout instead of the assigned J worktree. Feature work stopped, the misplaced untracked parent file was moved into J, and root confirmed the repair.

Final status facts after repair:

- Parent checkout status for `tests/unit/legal_ontology/test_stop_gates_domain_v1.py`, `resources/legal_rules`, and `trustgraph_legal`: clean / no entries.
- J worktree status for those same paths before commit: Todo 9-owned files only.
- Parent test file absent; J test file present.

## Evidence

- `.omo/evidence/debt-collection-domain-ontology-v1/task-9-stopgate-happy.json`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-9-stopgate-failure.json`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-9-focused-pytest.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-9-json-tool.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-9-py-compile.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-9-basedpyright.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-9-size-check.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-9-diff-check.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-9-isolation-repair.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-9-red-green-summary.txt`

## Verification

- PASS: `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_stop_gates_domain_v1.py tests/unit/legal_ontology/test_stop_gates.py -q`
- PASS: `json.tool` over the new v1 resource and both task-9 evidence JSON files.
- PASS: `/usr/bin/python3 -m py_compile` for changed Python files.
- PASS: `basedpyright --level error` for changed Python files.
- PASS: `git diff --check`.
- PASS: size check, with evaluator at 250 pure LOC.
- PASS: PII/path scan over new code, resource, evidence, and report.

## Safety

- Deterministic tests use curated local source v1 refs only.
- No live Korean-law MCP calls are used in tests.
- Evidence uses synthetic fixture refs and contains no source text.
- v0 StopGate tests remain green.
