# F2 Code Quality Review

Date: 2026-06-30

## Result

APPROVE.

## Test Evidence

- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology -q`
  - Result: 39 passed.
- `/opt/homebrew/bin/python3 -m pytest tests/integration/legal_ontology/test_mcp_tools.py -q`
  - Result: 3 passed.
- `python3 scripts/legal_ontology/evaluate_packet.py --fixtures tests/fixtures/legal-ocr/manifest.json --out .omo/evidence/debt-collection-ontology/task-10-eval.json`
  - Result: passed, `status=passed`, `tool_count=16`, `issues=[]`.

## Compile Evidence

- `/usr/bin/python3 -m py_compile trustgraph_legal/classifier.py trustgraph_legal/classifier_types.py trustgraph_legal/classifier_rules.py trustgraph_legal/classifier_manifest.py trustgraph_legal/mcp_domain.py trustgraph_legal/mcp_handlers.py trustgraph_legal/mcp_envelope.py trustgraph_legal/mcp_inputs.py trustgraph_legal/ingest.py trustgraph-mcp/trustgraph/mcp_server/auth.py trustgraph-mcp/trustgraph/mcp_server/legal_tools.py trustgraph-mcp/trustgraph/mcp_server/mcp.py scripts/legal_ontology/evaluate_packet.py tests/unit/legal_ontology/test_evaluate_packet.py`
  - Result: passed.

## Privacy Scan

Sensitive identifier and token-shaped scan over changed files, docs, scripts, tests, and task evidence: no raw sensitive-shape findings.

## Security Regression Evidence

- Raw string token resolver probe:
  - `raw_string_resolver_rejected=true`
  - `verified_context_accepted=true`
  - `scope_checked=true`
  - `token_echo=false`
- Literal sensitive-shape scan over MCP tests:
  - Result: no national-ID, phone, or account-shaped literals.
- Gateway-backed MCP smoke:
  - Result: bad token rejected, gateway `whoami` validated identity, public WebSocket `iam/authorise-many` was not used, internal scope-authorizer decisions rejected reader token for `promote_ontology_candidate`, 47 tools listed, debt tool present, token not echoed.

## Programming / Slop Review

- Loaded and applied `omo:programming` and `omo:remove-ai-slops` lenses after the final review flagged oversized modules and broad auth responsibility placement.
- Behavior was locked before refactor with focused tests:
  - `tests/unit/legal_ontology/test_document_classifier.py`: 6 passed.
  - `tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py`: 9 passed.
- Refactored oversized branch modules by responsibility:
  - `trustgraph_legal/classifier.py`: 411 pure LOC -> 89 pure LOC.
  - New classifier modules: `classifier_types.py` 137, `classifier_rules.py` 203, `classifier_manifest.py` 56.
  - `trustgraph_legal/mcp_domain.py`: 400 pure LOC -> 155 pure LOC.
  - New MCP modules: `mcp_handlers.py` 182, `mcp_envelope.py` 80, `mcp_inputs.py` 46.
  - New MCP auth boundary module: `trustgraph-mcp/trustgraph/mcp_server/auth.py` 102.
- The pre-existing `trustgraph-mcp/trustgraph/mcp_server/mcp.py` remains above the 250 LOC ceiling, but the new gateway-auth responsibility was moved out of that monolith into `auth.py`; the remaining `mcp.py` diff is limited to verifier wiring, registration, and token forwarding.
- Scoped MCP smoke was updated after final auth review: it no longer models authorization as fake `whoami` role mapping and no longer sends `authorise-many` through the public gateway WebSocket. The fake gateway validates token identity and rejects public `iam/authorise-many`; the injected internal scope-authorizer seam makes allow/deny decisions while production wires that seam to `IamClient.authorise_many`.

## Runtime Fix

Actual MCP server smoke initially exposed a FastMCP/Pydantic schema issue caused by recursive JSON type aliases in registered tool signatures. Commit `5d893e32` changed the adapter type surface to plain `Dict[str, Any]`. A later security review exposed presence-only auth for local debt-collection tools; the current working tree validates MCP tokens through the TrustGraph gateway before AccessToken creation and requires adapter calls to carry a gateway-verified `AuthContext`.

After that:

- server initialization passed
- streamable HTTP server started
- MCP client listed 47 tools
- `list_debt_collection_tools` was present
- `list_debt_collection_tools` call succeeded through a gateway-backed MCP client
- bad bearer token was rejected
- public gateway WebSocket `iam/authorise-many` was not used; production scope decisions use internal `IamClient.authorise_many`
- reader bearer token could not call governance-scope `promote_ontology_candidate`
- bearer test token was not echoed

## Residual Risk

The temporary smoke venv installed only the missing runtime dependencies needed for local MCP verification. Deployment packaging should still install `trustgraph-mcp` according to its `pyproject.toml`.
