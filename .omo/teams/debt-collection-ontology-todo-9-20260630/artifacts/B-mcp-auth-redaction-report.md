# B Report: MCP Auth, Redaction, and Integration Tests

Member: B `mcp-auth-redaction-tests`
Worktree: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debt-collection-ontology-todo-9-20260630/worktrees/B`
Branch: `team/debt-collection-ontology-todo-9-20260630/B`

## Scope

Owned test file:

- `tests/integration/legal_ontology/test_mcp_tools.py`

The test file targets the authoritative Todo 9 public API:

- `trustgraph_legal.mcp_domain.TOOL_DEFINITIONS`
- `trustgraph_legal.mcp_domain.list_tools()`
- `trustgraph_legal.mcp_domain.invoke_tool(tool_name, arguments=None, repo_root=None)`
- `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py`
- `register_debt_collection_brain_tools(mcp, repo_root=None)`

## Isolation Evidence

Initial bound-worktree evidence captured:

- `pwd`: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debt-collection-ontology-todo-9-20260630/worktrees/B`
- `git rev-parse --show-toplevel`: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debt-collection-ontology-todo-9-20260630/worktrees/B`
- B status: `## team/debt-collection-ontology-todo-9-20260630/B`
- Initial main status comparison: `## master...origin/master [ahead 21]`, `?? .omo/`

Leader later repaired an isolation issue: `tests/integration/legal_ontology/test_mcp_tools.py` had been created in the main checkout by mistake, then moved into B worktree and removed from main. After repair, B status showed `?? tests/integration/legal_ontology/`. This report records that repair as requested.

Current observed status before final B commit:

- B worktree: report artifact staged; integration test already committed as `eefbba6e`
- Main checkout comparison after A fixes: `## master...origin/master [ahead 25]`, `?? .omo/`

Leader later confirmed A source had been written to main, causing B contract failures. Leader moved that source into A worktree and removed the main stray files. B did not pull or copy source changes from main into the B worktree.

## Canonical Tool List

Leader corrected the final count to 16 tools by adding `list_debt_collection_tools` to the 15 plan-listed domain tools. B tests now assert exactly these names:

- `list_debt_collection_tools`
- `ingest_legal_document`
- `ingest_ocr_markdown`
- `get_ingest_status`
- `classify_legal_document`
- `extract_case_packet`
- `get_case_graph`
- `check_case_stop_gates`
- `check_limitation_status`
- `check_attachment_target_rules`
- `summarize_case_ledger`
- `recommend_next_action`
- `list_unknown_document_types`
- `review_extracted_fact`
- `promote_ontology_candidate`
- `reprocess_case`

The earlier 15-vs-16 mismatch is treated as a resolved coordination correction, not an A defect if A follows this final list.

## Test Coverage Added

`tests/integration/legal_ontology/test_mcp_tools.py` covers:

- stable contract publication through `TOOL_DEFINITIONS` and `list_tools()`
- exact 16-tool surface
- contract envelope fields: `schema_version`, `tool_name`, `group`, `scope`, `input_schema`, `output_schema`, `redaction`
- representative in-process tool calls through `invoke_tool()`
- response envelope keys: `schema_version`, `tool_name`, `group`, `scope`, `pii_profile`, `redaction`, `source_refs`, `warnings`, `result`
- StopGate result fields: `case_id`, `decision`, `risk_flags`, `source_refs`
- path arguments outside `repo_root` are rejected without echoing the attempted path or file content
- no raw national ID, phone, or account-like values in default responses
- redacted `source_refs` without `excerpt`, `text`, or raw source markers
- fake-MCP registration without importing the global MCP SDK package
- MCP auth-context/token-resolver requirement on adapter-registered calls
- no public `authorization` tool argument
- no token echo in tool responses

## Verification

Canonical Python used per leader note:

```bash
/opt/homebrew/bin/python3 -m pytest tests/integration/legal_ontology/test_mcp_tools.py -q
```

Initial observed result in B worktree before A integration:

- collection succeeds without importing global `mcp`
- 3 tests run
- 3 failures, all expected contract gaps while A source is absent from B:
  - `Todo 9 contract gap: missing trustgraph_legal.mcp_domain`
  - `Todo 9 contract gap: missing trustgraph-mcp/trustgraph/mcp_server/legal_tools.py`

Earlier run, before test import repair, failed during collection with:

- `ModuleNotFoundError: No module named 'mcp'`

That confirmed the leader finding that global MCP SDK is unavailable and the tests must avoid SDK-dependent collection paths.

After A commit `dfa70336`, B fast-forwarded its worktree to A's commit and reran:

```bash
/opt/homebrew/bin/python3 -m pytest tests/integration/legal_ontology/test_mcp_tools.py -q
```

Observed result:

- 3 tests collected
- 1 passed
- 2 failed

Failures:

- `TOOL_DEFINITIONS` public items still serialize through dataclass field `name` rather than exposing `tool_name` directly at that public definition surface.
- `invoke_tool("list_debt_collection_tools")` returns group `admin`, while B's strict contract expectation currently treats the self-description tool as final-list read/self-description coverage.

A's focused source tests do pass:

```bash
/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_domain_tools.py -q
```

Observed result:

- 4 passed

Additional exact group-map mismatches found by B's stricter contract expectations:

- `list_debt_collection_tools`: expected `read`, actual `admin`
- `get_ingest_status`: expected `ingest`, actual `read`
- `classify_legal_document`: expected `graph`, actual `read`
- `summarize_case_ledger`: expected `read`, actual `graph`

After A follow-up commit `928cf8df` and master merge `986e895f`, B fast-forwarded to master and reran:

```bash
/opt/homebrew/bin/python3 -m pytest tests/integration/legal_ontology/test_mcp_tools.py -q
/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_domain_tools.py -q
```

Observed result:

- `tests/integration/legal_ontology/test_mcp_tools.py`: 3 passed
- `tests/unit/legal_ontology/test_mcp_domain_tools.py`: 4 passed

After C flagged security blockers in A commit `dfa70336`, A landed security follow-up commit `588fba0c` and master merge `8af913f7`. B merged that source into its worktree, updated the integration contract test, and reran:

```bash
/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py -q
/opt/homebrew/bin/python3 -m py_compile tests/integration/legal_ontology/test_mcp_tools.py trustgraph_legal/mcp_domain.py trustgraph-mcp/trustgraph/mcp_server/legal_tools.py trustgraph-mcp/trustgraph/mcp_server/mcp.py trustgraph-mcp/trustgraph/mcp_server/__init__.py
git diff --check
```

Observed result:

- combined unit/integration slice: 8 passed
- py_compile: passed
- diff check: passed

## Final Acceptance

B acceptance is now unblocked. A source matches the strict public contract:

- `TOOL_DEFINITIONS` exposes `tool_name` directly.
- `list_debt_collection_tools` is grouped as `read`.
- `get_ingest_status` is grouped as `ingest`.
- `classify_legal_document` is grouped as `graph`.
- `summarize_case_ledger` is grouped as `read`.
- `register_debt_collection_brain_tools` uses MCP auth context/token resolver instead of public tool-payload Bearer values.
- adapter-registered tool callables do not expose an `authorization` parameter.
- `case_graph_path` and other path arguments cannot read outside `repo_root`; outside paths return `path_outside_repo_root` without leaking path or file content.

B did not edit A-owned source.

B integration test file is committed as:

- `eefbba6e test(legal-mcp): add debt collection MCP contract tests`

B tests remain strict around the leader-requested contract points:

- `tool_name`, not `name`
- contract and response schema versions
- per-tool groups matching final canonical `read`, `ingest`, `graph`, `stopgate`, and `governance`
- `redaction.default`
- input and output schema fields
- fake-MCP registered functions accepting `arguments` only
- context-token auth without token echo
- repo-bound path rejection
