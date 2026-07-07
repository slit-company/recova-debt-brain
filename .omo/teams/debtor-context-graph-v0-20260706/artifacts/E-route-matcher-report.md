# Member E Route Matcher Report

## Scope
- Team: debtor-context-graph-v0
- Member: E route-matcher
- Worktree: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debtor-context-graph-v0-20260706/worktrees/E`
- Branch: `team/debtor-context-graph-v0-20260706/E`
- Commit: `14ad71d9 feat(legal-routes): evaluate debtor route candidates`

## Delivered
- Added `trustgraph_legal/route_candidates.py`.
- Added `tests/unit/legal_ontology/test_route_candidates.py`.
- Added task-8 evidence under `.omo/evidence/debtor-context-graph-v0/`.
- Did not edit route resource JSONs.

## Matcher Behavior
- Loads the curated Todo 4 route resource into frozen `RouteTemplate` values.
- Matches `DebtorGraphPayload.fact_assertions[].predicate` against `required_fact_handles` and `blocking_fact_handles`.
- Uses `stop_gates[].reason_code` and `review_items[].review_reason` as review/blocking handles.
- Emits `RouteCandidate` values with `possible`, `blocked`, `missing_facts`, and `review_required` statuses.
- Always emits `no_direct_execution=True` and `review_status=review_required`.

## Evidence
- Happy route evidence: `.omo/evidence/debtor-context-graph-v0/task-8-routes-happy.json`
- Failure/blocking evidence: `.omo/evidence/debtor-context-graph-v0/task-8-routes-failure.json`
- Focused pytest: `.omo/evidence/debtor-context-graph-v0/task-8-focused-pytest.txt`
- Route validator: `.omo/evidence/debtor-context-graph-v0/task-8-route-validator.txt`
- PII scan: `.omo/evidence/debtor-context-graph-v0/task-8-pii-scan.txt`
- Py compile: `.omo/evidence/debtor-context-graph-v0/task-8-py-compile.txt`
- Staged diff check: `.omo/evidence/debtor-context-graph-v0/task-8-diff-check.txt`
- Ruff availability note: `.omo/evidence/debtor-context-graph-v0/task-8-ruff.txt`

## Verification
- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_route_candidates.py -q`: 4 passed.
- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_route_candidates.py tests/unit/legal_ontology/test_validate_routes.py -q`: 7 passed.
- `/opt/homebrew/bin/python3 scripts/legal_ontology/validate_routes.py resources/legal_routes/debt_collection_routes_v0.json resources/legal_rules/debt_collection_route_sources_v0.json`: PASS, routes=18, legal_sources=18, legal_refs=35.
- LSP diagnostics on changed Python files: no diagnostics found.
- `/opt/homebrew/bin/python3 -m py_compile trustgraph_legal/route_candidates.py tests/unit/legal_ontology/test_route_candidates.py`: passed.
- JSON validation for both task-8 route evidence files: passed.
- Task-8 PII scan: `NO_FINDINGS`.
- `git diff --cached --check` before commit: passed.
- Ruff was unavailable in this environment: command not found and Python module not installed.

## Notes For Integrator
- The matcher consumes the current Todo 1 `DebtorGraphPayload` and Todo 4 route resource contract.
- `bank_account_attachment` becomes `possible` with `enforceable_title` and `third_party_debtor_bank_hint`.
- Asset/income routes surface exact missing handles instead of false positives.
- `insolvency_stay` blocks collection routes; `stay_or_discharge_detected` marks the insolvency review route as `review_required`.

## Follow-Up: Accepted Fact Status Compatibility
- Peer trigger: Member I found that H Todo 6 emits bank route predicates with `review_status="accepted"`, which originally caused E to return `review_required`.
- Resolution commit: `0465cc6e fix(legal-routes): accept integrated route facts`
- Contract change: `accepted` is now included in `CLEAR_FACT_REVIEW_STATUSES`.
- Regression coverage: `test_accepted_route_facts_clear_h_integrated_bank_route_contract`.
- Accepted-status evidence: `.omo/evidence/debtor-context-graph-v0/task-8-accepted-status-happy.json`
- Verification:
  - `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_route_candidates.py -q`: 5 passed.
  - `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_route_candidates.py tests/unit/legal_ontology/test_validate_routes.py -q`: 8 passed.
  - LSP diagnostics on changed Python files: no diagnostics found.
  - `/opt/homebrew/bin/python3 -m py_compile trustgraph_legal/route_candidates.py tests/unit/legal_ontology/test_route_candidates.py`: passed.
  - Accepted-status JSON evidence validates.
  - Accepted-status PII scan: `NO_FINDINGS`.
  - `git diff --cached --check` before commit: passed.
  - Ruff remained unavailable in this environment.
