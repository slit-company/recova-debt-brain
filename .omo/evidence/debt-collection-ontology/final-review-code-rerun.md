# Final Code Quality Re-review

Status: FAIL
codeQualityStatus: BLOCK
recommendation: REQUEST_CHANGES
reportPath: `.omo/evidence/debt-collection-ontology/final-review-code-rerun.md`

## Scope Reviewed

- Current working tree plus `git diff origin/master...HEAD`.
- Focus areas: `trustgraph_legal`, `trustgraph-mcp/trustgraph/mcp_server`, `scripts/legal_ontology`, legal ontology tests, and debt-collection docs.
- Current tree is dirty beyond `origin/master...HEAD`: tracked fixes in `mcp.py`, `legal_tools.py`, `ingest.py`, legal ontology tests/docs/scripts, plus untracked OMO artifacts and `tests/unit/legal_ontology/test_evaluate_packet.py`.

## Skill Perspective Check

- Ran the required skill-perspective check before judging tests/maintainability.
- Loaded/consulted `omo:remove-ai-slops`.
- Loaded/consulted `omo:programming`, plus Python `README.md`, `type-patterns.md`, `data-modeling.md`, `error-handling.md`, and `code-smells.md`.
- Result: the diff violates both perspectives:
  - A runtime type regression survives because tests cover the fake legal adapter but not the real generic MCP token path.
  - New production modules exceed the 250 pure-LOC ceiling, and one `SIZE_OK` waiver states multiple responsibilities rather than an indivisible exception.
  - The authorization scope implementation hardcodes a broad domain scope after `whoami` instead of preserving gateway-derived capabilities.

## Findings

### CRITICAL

1. Generic MCP tools now fail before opening a gateway socket.

`trustgraph-mcp/trustgraph/mcp_server/mcp.py:144` changed `_require_token()` to return `AuthContext`, but `McpServer._get_manager()` still passes that whole object to `get_socket_manager()` at `trustgraph-mcp/trustgraph/mcp_server/mcp.py:444`. `get_socket_manager()` calls `_token_key(token)` at `trustgraph-mcp/trustgraph/mcp_server/mcp.py:186`, and `_token_key()` requires a string because it calls `token.encode()` in `trustgraph-mcp/trustgraph/mcp_server/tg_socket.py:12`.

Evidence probe:

```text
AuthContext
False
AttributeError
'AuthContext' object has no attribute 'encode'
```

Impact: every existing generic MCP tool path that uses `_get_manager()` regresses at runtime. The new tests only exercise `legal_tools.register_debt_collection_brain_tools()` with a fake MCP object, so this slipped through.

### HIGH

1. Gateway-backed authorization still grants all legal tools to any gateway-authenticated token.

`GatewayTokenVerifier.verify_token()` returns `AccessToken(..., scopes=[LEGAL_MCP_GATEWAY_SCOPE])` at `trustgraph-mcp/trustgraph/mcp_server/mcp.py:91`, regardless of any per-tool or gateway-derived permissions. `_require_token()` accepts that broad scope for any required tool scope at `trustgraph-mcp/trustgraph/mcp_server/mcp.py:160`, and the legal adapter repeats the same wildcard acceptance in `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py:108`.

Impact: the tool metadata exposes fine-grained scopes like `ingest:documents`, `graph:case`, and `governance:review`, but the enforcement path treats the broad domain scope as sufficient for all of them. That contradicts the doc claim at `docs/product/debt-collection-ontology/mcp-domain-server-contract.md:49` that the gateway remains the source of truth for identity and permissions, unless `whoami` itself performs the complete per-tool capability check. The current code does not show or test that.

2. New production modules exceed the loaded programming/slop 250 pure-LOC ceiling.

Measured pure LOC:

```text
411 trustgraph_legal/classifier.py
387 trustgraph_legal/mcp_domain.py
```

`trustgraph_legal/classifier.py:13` has a `SIZE_OK` waiver, but its justification says the file keeps the classifier API, CLI, JSON contract, and deterministic rule table together. That names multiple responsibilities, not an indivisible state machine or pure data-table exception. `trustgraph_legal/mcp_domain.py` has no waiver and combines tool registry, envelope shaping, dispatch, path policy, redaction, source-ref extraction, and many handlers in one module.

Impact: this is not just style. These are new core production files in the branch, and the loaded skill criteria classify this as maintainability debt and AI-slop structure drift.

### MEDIUM

1. The new prompt semantics test is not runnable in the local verification environment.

`tests/unit/test_extract/test_ontology/test_legal_prompt_semantics.py:4` imports `ibis`. Local verification fails during collection:

```text
ModuleNotFoundError: No module named 'ibis'
```

`trustgraph-flow/pyproject.toml:22` declares `ibis`, and CI appears to install `trustgraph-flow`, so this may be an environment gap rather than a CI blocker. Still, the requested focused command including this test cannot pass in the current workspace.

2. MCP server live import/smoke is blocked locally.

`PYTHONPATH=trustgraph-mcp:. python3 - <<... import trustgraph.mcp_server.mcp ...` fails with:

```text
ModuleNotFoundError: No module named 'mcp'
```

This prevented a real `McpServer` import or streamable HTTP smoke in this environment. `py_compile` passed, but compile does not validate runtime imports.

### LOW

1. Current tree has an untracked test that is part of the passing legal suite.

`tests/unit/legal_ontology/test_evaluate_packet.py:13` covers the new `evaluate_packet.py --out` behavior, and the focused legal suite counted it. Because it is untracked, it will not be included in `origin/master...HEAD` or any commit unless explicitly added.

2. Source refs, provenance, redaction, and direct-execution boundaries look materially covered in the reviewed domain path.

The case graph and StopGate paths carry `source_ref`, `document_id`, and `chunk_id`, and invalid/missing provenance is tested. MCP envelope tests also assert redaction and direct execution rejection. No blocker found in this area during this pass.

## Verification Evidence

Passed:

```text
git diff --check
git diff --check origin/master...HEAD
PYTHONPATH=trustgraph-mcp:. python3 -m py_compile trustgraph_legal/*.py scripts/legal_ontology/*.py trustgraph-mcp/trustgraph/mcp_server/legal_tools.py trustgraph-mcp/trustgraph/mcp_server/mcp.py tests/unit/legal_ontology/*.py tests/integration/legal_ontology/test_mcp_tools.py
PYTHONPATH=trustgraph-mcp:. python3 -m pytest -q tests/unit/legal_ontology tests/integration/legal_ontology/test_mcp_tools.py
41 passed in 2.44s
PYTHONPATH=. python3 scripts/legal_ontology/check_fixture_manifest.py tests/fixtures/legal-ocr/manifest.json
PASS manifest
PYTHONPATH=. python3 scripts/legal_ontology/validate_ontology.py resources/ontologies/recova-debt-collection.json
PASS ontology recova-debt-collection classes=36 objectProperties=41 datatypeProperties=44
PYTHONPATH=. python3 - <<'PY' ... evaluate_packet(...)
{'status': 'passed', 'tool_count': 16, 'evaluated_tools': ['get_case_graph', 'check_case_stop_gates', 'recommend_next_action', 'execute_direct_collection_filing'], 'decision': '보류', 'recommendation': 'hold_for_review', 'failure_probe': 'unknown_tool', 'issues': []}
```

Failed/blocked:

```text
PYTHONPATH=trustgraph-mcp:. python3 -m pytest -q tests/unit/test_extract/test_ontology/test_legal_prompt_semantics.py
ERROR ... ModuleNotFoundError: No module named 'ibis'

PYTHONPATH=trustgraph-mcp:. python3 - <<'PY' ... import trustgraph.mcp_server.mcp ...
ModuleNotFoundError: No module named 'mcp'

_token_key(AuthContext(...))
AttributeError: 'AuthContext' object has no attribute 'encode'
```

## Blockers

- Fix the generic MCP token path so existing tools pass the raw bearer token string to `_token_key()` and `WebSocketManager`, while debt-collection tools still receive the verified auth context they need.
- Replace the hardcoded broad legal scope with gateway-derived capability data, or document and test the exact gateway contract that makes `LEGAL_MCP_GATEWAY_SCOPE` safe as an all-tools grant.
- Split or otherwise justify `trustgraph_legal/classifier.py` and `trustgraph_legal/mcp_domain.py` under the loaded 250 pure-LOC/AI-slop criteria. The current classifier waiver is not valid because it describes multiple responsibilities.
