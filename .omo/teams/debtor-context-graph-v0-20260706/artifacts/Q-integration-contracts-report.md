# Q Integration Contracts Report

Member: Q integration-contracts

Scope: Todo 13 additive integration/fake-MCP contract tests and task-13 evidence only.

## Result

- Strengthened `tests/unit/legal_ontology/test_mcp_debtor_context_tools.py`.
- Strengthened `tests/integration/legal_ontology/test_debtor_context_pipeline.py`.
- Added task-13 evidence under `.omo/evidence/debtor-context-graph-v0/`.
- No production source edits.

## Contract Edges Covered

- Existing 16 MCP tools remain ordered before the 5 debtor graph tools.
- Fake-MCP debtor callables do not accept `authorization`.
- Authorization passed as a tool argument is ignored by the SDK-independent domain layer without token echo.
- Outside-root debtor graph paths reject with `path_outside_repo_root` without path/content echo.
- Equivalent assembly inputs produce stable `graph_snapshot_id`, `snapshot_replay_id`, and route candidate IDs.
- `explain_debtor_route_candidate` exposes route fields only, excluding Todo 12 governance record keys `record_id`, `suggested_action`, and `audit`.
- `legal_tools.py` remains SDK-free at the fake-MCP adapter boundary.

## Evidence

- `.omo/evidence/debtor-context-graph-v0/task-13-fake-mcp-happy.json`
- `.omo/evidence/debtor-context-graph-v0/task-13-fake-mcp-failure.txt`
- `.omo/evidence/debtor-context-graph-v0/task-13-focused-pytest.txt`
- `.omo/evidence/debtor-context-graph-v0/task-13-mcp-compat-pytest.txt`
- `.omo/evidence/debtor-context-graph-v0/task-13-basedpyright.txt`
- `.omo/evidence/debtor-context-graph-v0/task-13-pii-scan.txt`
- `.omo/evidence/debtor-context-graph-v0/task-13-json-tool.txt`
- `.omo/evidence/debtor-context-graph-v0/task-13-py-compile.txt`
- `.omo/evidence/debtor-context-graph-v0/task-13-diff-check.txt`
- `.omo/evidence/debtor-context-graph-v0/task-13-ruff.txt`

## Gates

- Focused pytest: pass, 10 tests.
- MCP compatibility pytest: pass, 19 tests.
- `basedpyright`: 0 errors; one strict warning remains at the stdlib `json.loads` boundary in the typed test helper and is summarized without local paths.
- `py_compile`: pass.
- JSON evidence validation: pass.
- Sensitive-pattern PII scan: `NO_FINDINGS`.
- `git diff --check`: pass.
- `ruff`: not available on PATH in this worktree environment.
