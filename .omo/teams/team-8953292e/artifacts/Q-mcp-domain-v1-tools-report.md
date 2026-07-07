# Q mcp-domain-v1-tools report

Member: Q `mcp-domain-v1-tools`
Thread: `codex://threads/019f38dd-ce41-7720-a6ef-46ca1fbf7a02`
Worktree: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/team-8953292e/worktrees/Q`
Branch: `team/team-8953292e/Q`
Commit: `21e6c5bd955f5d0cafbc0399c493803dd8994940`

## Scope

Implemented Todo 12 only: appended four read-only claim-domain MCP tools after the existing 21 tools:

- `list_claim_domain_routes`
- `explain_collection_workflow_state`
- `evaluate_claim_domain_decision`
- `explain_claim_action_packet`

The existing 21 tool order is preserved. Public MCP callables still accept only `arguments`; auth remains context-only through the adapter token resolver. The new tools are advisory/read-only and do not perform debtor contact, filing, live law MCP calls, LLM calls, external service calls, or production mutations.

## Files

- `trustgraph_legal/mcp_domain.py`: appended claim-domain group/scope mappings and tool definitions.
- `trustgraph_legal/mcp_claim_domain_handlers.py`: new repo-root-bounded read/explain handlers over committed v1 resources and the deterministic decision engine.
- `tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py`: Todo 12 fake-MCP/order/auth/path tests.
- `tests/utils/legal_mcp_support.py`: shared fake-MCP and JSON assertion helpers used by MCP tests.
- `tests/unit/legal_ontology/test_mcp_domain_tools.py`: updated expected MCP surface to 25 tools.
- `tests/integration/legal_ontology/test_mcp_tools.py`: updated integration expectations and moved duplicated helpers to shared support.
- `.omo/evidence/debt-collection-domain-ontology-v1/task-12-mcp-happy.json`: tool-order proof and fake-MCP happy calls for all four new tools.
- `.omo/evidence/debt-collection-domain-ontology-v1/task-12-mcp-failure.json`: outside-root path and missing-auth failure evidence.

## Verification

- PASS: `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py -q` -> 13 passed.
- PASS: `/Users/cosmos/.local/bin/basedpyright --level error trustgraph_legal/mcp_claim_domain_handlers.py trustgraph_legal/mcp_domain.py tests/utils/legal_mcp_support.py tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py` -> 0 errors.
- PASS: `/opt/homebrew/bin/python3 -m py_compile trustgraph_legal/mcp_claim_domain_handlers.py trustgraph_legal/mcp_domain.py tests/utils/legal_mcp_support.py tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py`.
- PASS: evidence scan over `task-12-mcp-happy.json` and `task-12-mcp-failure.json` found no `/Users/cosmos`, `task-12-evidence-context-token`, or `task-12-outside-root-secret` leaks.
- PASS: post-commit Q worktree `git status --short` is clean.
- PASS: parent checkout Todo 12 owned paths are clean.

## Evidence highlights

- `task-12-mcp-happy.json` has `existing_21_remain_first: true`, `four_tools_appended: true`, `listed_count: 25`, and fake-MCP happy responses for all four new tools.
- `task-12-mcp-failure.json` has `path_leaked: false`, `secret_leaked: false`, missing auth `PermissionError`, and public callable parameters `["arguments"]`.

## Notes

The broad warning-level `basedpyright` surface remains noisy in legacy MCP tests, so the committed type gate uses `--level error`. No error-level diagnostics remain on changed files.
