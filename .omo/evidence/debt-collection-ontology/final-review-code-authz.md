# Final Code/Authz Review

codeQualityStatus: BLOCK
recommendation: REQUEST_CHANGES

Scope reviewed: current uncommitted diff on `master`, including modified files and untracked split modules under `trustgraph_legal/`, `trustgraph-mcp/trustgraph/mcp_server/auth.py`, and `tests/unit/legal_ontology/test_evaluate_packet.py`.

Skill-perspective check: `omo:remove-ai-slops` and `omo:programming` were loaded and consulted, including the Python reference. The classifier/MCP split mostly satisfies the 250 pure-LOC and behavior-preservation goals, but the diff violates both perspectives at the auth boundary: the new runtime auth path is not covered by a real boundary test, and the current implementation is wired to a route the gateway explicitly does not expose.

## CRITICAL

1. `GatewayTokenVerifier` rejects valid MCP tokens because it sends `authorise-many` over the public websocket IAM dispatch path, but that operation is internal-only and absent from the gateway registry.

   References:
   - `trustgraph-mcp/trustgraph/mcp_server/auth.py:25-30` opens a gateway websocket, calls `whoami()`, then requires `_authorised_legal_scopes(...)` during token verification.
   - `trustgraph-mcp/trustgraph/mcp_server/auth.py:98-104` sends `{"operation": "authorise-many"}` through `manager.request("iam", ...)`.
   - `trustgraph-flow/trustgraph/gateway/dispatch/mux.py:145-159` routes websocket IAM requests through `_registry_lookup(inner_op)` and returns `"unknown-service"` when no operation is registered.
   - `trustgraph-flow/trustgraph/gateway/registry.py:198-205` states `authorise`, `authorise-many`, and `get-signing-key-public` are internal and excluded from the public API; the same file registers `whoami` at `registry.py:399` but not `authorise-many`.

   Evidence command:
   ```text
   rg -n 'name="(whoami|authorise|authorise-many)"|authorise, authorise-many|service == "iam"|_registry_lookup\(inner_op\)' trustgraph-flow/trustgraph/gateway/registry.py trustgraph-flow/trustgraph/gateway/dispatch/mux.py trustgraph-mcp/trustgraph/mcp_server/auth.py
   trustgraph-flow/trustgraph/gateway/dispatch/mux.py:145:            elif service == "iam":
   trustgraph-flow/trustgraph/gateway/dispatch/mux.py:146:                op = _registry_lookup(inner_op) if inner_op else None
   trustgraph-flow/trustgraph/gateway/registry.py:204:# authorise, authorise-many, get-signing-key-public) are likewise
   trustgraph-flow/trustgraph/gateway/registry.py:399:    name="whoami",
   ```

   Impact: with `McpServer` now using `GatewayTokenVerifier` in `trustgraph-mcp/trustgraph/mcp_server/mcp.py:300-307`, a valid Bearer token can be rejected before any MCP handler runs. This is not behavior-preserving and breaks the stated gateway/IAM scope-enforcement goal.

## HIGH

1. The new tests do not exercise the broken runtime auth verifier path.

   References:
   - `tests/integration/legal_ontology/test_mcp_tools.py:194-255` tests `legal_tools.register_debt_collection_brain_tools` with a fake `AuthContext`, but never imports or drives `GatewayTokenVerifier`.
   - `trustgraph-mcp/trustgraph/mcp_server/auth.py:18-46` is the production verifier being introduced.

   Impact: the green suite gives false confidence for the changed security boundary. This is a remove-ai-slops/programming test-shape violation: it tests an adapter with handcrafted data, not the actual boundary whose route changed.

## MEDIUM

None.

## LOW

1. `trustgraph-mcp/trustgraph/mcp_server/mcp.py` remains an oversized module at 1550 pure LOC. This appears pre-existing and the current diff reduces it, so I am not treating it as a blocker for this pass, but it remains a maintenance risk under the programming skill's 250 pure-LOC guidance.

## Passing Evidence

```text
/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology -q
39 passed in 0.33s

/opt/homebrew/bin/python3 -m pytest tests/integration/legal_ontology/test_mcp_tools.py -q
3 passed in 2.07s

/usr/bin/python3 -m py_compile trustgraph_legal/classifier.py trustgraph_legal/classifier_types.py trustgraph_legal/classifier_rules.py trustgraph_legal/classifier_manifest.py trustgraph_legal/mcp_domain.py trustgraph_legal/mcp_handlers.py trustgraph_legal/mcp_envelope.py trustgraph_legal/mcp_inputs.py trustgraph_legal/ingest.py trustgraph-mcp/trustgraph/mcp_server/auth.py trustgraph-mcp/trustgraph/mcp_server/legal_tools.py trustgraph-mcp/trustgraph/mcp_server/mcp.py scripts/legal_ontology/evaluate_packet.py tests/unit/legal_ontology/test_evaluate_packet.py tests/unit/legal_ontology/test_ingest.py tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py
exit 0

git diff --check
exit 0
```

Pure LOC check on changed Python files:

```text
  89 trustgraph_legal/classifier.py
 137 trustgraph_legal/classifier_types.py
 203 trustgraph_legal/classifier_rules.py
  56 trustgraph_legal/classifier_manifest.py
 155 trustgraph_legal/mcp_domain.py
 182 trustgraph_legal/mcp_handlers.py
  80 trustgraph_legal/mcp_envelope.py
  46 trustgraph_legal/mcp_inputs.py
 152 trustgraph_legal/ingest.py
  95 trustgraph-mcp/trustgraph/mcp_server/auth.py
  95 trustgraph-mcp/trustgraph/mcp_server/legal_tools.py
1550 trustgraph-mcp/trustgraph/mcp_server/mcp.py
 162 scripts/legal_ontology/evaluate_packet.py
  20 tests/unit/legal_ontology/test_evaluate_packet.py
 118 tests/unit/legal_ontology/test_ingest.py
 196 tests/unit/legal_ontology/test_mcp_domain_tools.py
 279 tests/integration/legal_ontology/test_mcp_tools.py
```

## Blockers

- Fix `GatewayTokenVerifier` so it performs `authorise-many` through an allowed/internal IAM path, or expose and gate the operation intentionally in the websocket route. The current public websocket request to `iam`/`authorise-many` is not dispatchable.
- Add a focused test for the production verifier or an equivalent fake gateway/websocket path proving `authorise-many` decisions become MCP `AccessToken.scopes` and denied scopes block the correct debt-collection tools.

VERDICT: REJECT
