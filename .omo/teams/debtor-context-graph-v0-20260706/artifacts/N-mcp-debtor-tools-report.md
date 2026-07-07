# N mcp-debtor-tools Todo 11 Report

## Scope

- Added five additive debtor graph MCP tools after the existing 16 tools:
  - `assemble_debtor_documents`
  - `build_debtor_context_graph`
  - `get_debtor_graph_snapshot`
  - `list_debtor_route_candidates`
  - `explain_debtor_route_candidate`
- Group/scopes: `debtor_graph`, with `debtor_graph:assembly`, `debtor_graph:build`, `debtor_graph:read`, and `debtor_graph:routes`.
- Public auth surface remains context-only. No `authorization`, `token`, or `bearer` tool arguments were added.
- `explain_debtor_route_candidate` summarizes existing route candidate fields only: `review_status`, `no_direct_execution`, `required_facts`, `missing_facts`, `blocking_facts`, `legal_source_refs`, and `source_fact_ids`.

## Evidence

- Happy fake-MCP call: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debtor-context-graph-v0-20260706/worktrees/N/.omo/evidence/debtor-context-graph-v0/task-11-mcp-happy.json`
- Outside-root failure fake-MCP call: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debtor-context-graph-v0-20260706/worktrees/N/.omo/evidence/debtor-context-graph-v0/task-11-mcp-path-failure.json`
- Failure evidence returns stable envelope with `warnings=["path_outside_repo_root"]`, empty `source_refs`, and no outside path/content echo.

## Verification

- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_debtor_context_tools.py tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py -q` -> 13 passed.
- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_document_assembly.py tests/unit/legal_ontology/test_debtor_context.py tests/unit/legal_ontology/test_route_candidates.py tests/unit/legal_ontology/test_mcp_debtor_context_tools.py tests/integration/legal_ontology/test_debtor_context_pipeline.py tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py -q` -> 39 passed.
- `/opt/homebrew/bin/python3 -m py_compile trustgraph_legal/mcp_debtor_handlers.py trustgraph_legal/mcp_handlers.py trustgraph_legal/mcp_domain.py` -> passed.
- `/usr/bin/python3 -m py_compile trustgraph_legal/mcp_debtor_handlers.py trustgraph_legal/mcp_handlers.py trustgraph_legal/mcp_domain.py` -> passed on Python 3.9.6.
- `/Users/cosmos/.local/bin/basedpyright --level error trustgraph_legal/mcp_domain.py trustgraph_legal/mcp_handlers.py trustgraph_legal/mcp_debtor_handlers.py tests/unit/legal_ontology/test_mcp_debtor_context_tools.py tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py` -> 0 errors.
- `git diff --check` -> passed.
- PII/path scan over task-11 evidence and changed files found no matches for raw OCR marker, absolute `/Users/cosmos` paths, synthetic secret, temp outside path marker, Korean RRN pattern, or phone pattern.

## Compatibility Note

- `/usr/bin/python3 -c 'import trustgraph_legal.mcp_domain'` is blocked by an existing Python 3.9 import-floor limitation in `trustgraph_legal/governance_models.py`: `PromotionAccepted | PromotionRejected` is evaluated at runtime.
- `/usr/bin/python3 -c 'import trustgraph_legal.mcp_debtor_handlers'` is blocked earlier by existing `@dataclass(..., slots=True)` usage in `trustgraph_legal/debtor_context_types.py`.
- These are outside Todo 11 scope and were not changed in N.

## Size Guard

- `trustgraph_legal/mcp_domain.py`: 167 pure LOC.
- `trustgraph_legal/mcp_handlers.py`: 213 pure LOC.
- `trustgraph_legal/mcp_debtor_handlers.py`: 93 pure LOC.
