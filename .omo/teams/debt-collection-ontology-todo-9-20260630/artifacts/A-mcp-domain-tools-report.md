# A Report - mcp-domain-tools

## Scope

Implemented the Todo 9 debt-collection MCP domain source layer in member A's isolated worktree.

Fresh review commit after C blocker fix:

- `588fba0c fix(legal-mcp): enforce MCP auth and repo-bound paths`

- `trustgraph_legal.mcp_domain.TOOL_DEFINITIONS`
- `trustgraph_legal.mcp_domain.list_tools()`
- `trustgraph_legal.mcp_domain.invoke_tool(tool_name, arguments=None, repo_root=None)`
- `trustgraph.mcp_server.legal_tools.register_debt_collection_brain_tools(mcp, repo_root=None, token_resolver=None, require_auth=True)`

The MCP server change is a thin registration hook only; domain behavior stays in `trustgraph_legal`.

## Final Tool List

1. `list_debt_collection_tools`
2. `ingest_legal_document`
3. `ingest_ocr_markdown`
4. `get_ingest_status`
5. `classify_legal_document`
6. `extract_case_packet`
7. `get_case_graph`
8. `check_case_stop_gates`
9. `check_limitation_status`
10. `check_attachment_target_rules`
11. `summarize_case_ledger`
12. `recommend_next_action`
13. `list_unknown_document_types`
14. `review_extracted_fact`
15. `promote_ontology_candidate`
16. `reprocess_case`

## Contract

- Tool contract schema: `trustgraph-legal-mcp-tool-contract/v1`
- Tool response schema: `trustgraph-legal-mcp-tool-response/v1`
- Response envelope keys: `schema_version`, `tool_name`, `group`, `scope`, `pii_profile`, `redaction`, `source_refs`, `warnings`, `result`
- Contract groups used by the 16 tools: `read`, `ingest`, `graph`, `stopgate`, `governance`
- Scope values start with their group, for example `read:tools`, `ingest:documents`, `graph:case`, `stopgate:check`, `governance:review`
- Default redaction: raw text and source text are excluded; source refs are redacted pointers
- The adapter no longer accepts `authorization` as a tool argument. Production registration passes the existing MCP auth-context token resolver (`_require_token`) into the thin helper, and fake-MCP tests pass a resolver directly. Tokens are not echoed into tool outputs.
- Path arguments are resolved under `repo_root`; outside-root paths return a stable redacted rejection envelope (`path_outside_repo_root`) and do not read or echo the requested server path.
- v0 write-like tools return review-safe/not-configured/planned envelopes and do not perform filing, contact, collection, storage mutation, or ontology mutation

## Verification

Ran from A worktree:

- `/opt/homebrew/bin/python3` smoke import/call for `list_tools`, `invoke_tool`, fake MCP registration with token resolver, and outside-root `case_graph_path`: passed
- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_domain_tools.py -q`: 5 passed
- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology -q`: 36 passed
- `git diff --check HEAD~1 HEAD`: passed

`/usr/bin/python3` limitation: it is Python 3.9.6 and cannot import the existing legal package because pre-existing modules such as `trustgraph_legal.registry` use runtime PEP 604 aliases; this fails before Todo 9 logic with `TypeError: unsupported operand type(s) for |: 'type' and 'type'`. Canonical verification used `/opt/homebrew/bin/python3` per leader guidance.

## Isolation Repair

During implementation, the first source patch was accidentally applied to the main checkout. The leader repaired isolation by copying those exact source files into A's worktree and removing the stray main-checkout files. I verified after repair:

- Main checkout status after this fix: `## master...origin/master [ahead 27]`, `?? .omo/`
- A worktree status before staging: modified/added only A-owned source and unit-test files

No main-checkout source files remain modified by A.
