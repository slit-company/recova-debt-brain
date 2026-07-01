# Final Code/Authz Re-review

codeQualityStatus: BLOCK
recommendation: REQUEST_CHANGES
reportPath: `.omo/evidence/debt-collection-ontology/final-review-code-authz-rerun.md`

## Scope Reviewed

- Repository: `/Users/cosmos/dev/ontology/trustgraph`
- Scope: current uncommitted working tree, including tracked changes plus relevant untracked Python files under `trustgraph_legal/`, `trustgraph-mcp/trustgraph/mcp_server/`, `scripts/legal_ontology/`, and `tests/unit/legal_ontology/`.
- Key authz files reviewed:
  - `trustgraph-mcp/trustgraph/mcp_server/auth.py`
  - `trustgraph-mcp/trustgraph/mcp_server/mcp.py`
  - `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py`
  - `tests/unit/legal_ontology/test_mcp_auth_boundary.py`
  - `tests/unit/legal_ontology/test_mcp_domain_tools.py`
  - `tests/integration/legal_ontology/test_mcp_tools.py`
- Also sampled the split modules under `trustgraph_legal/` and ingest/evaluator changes for scope control and regression risk.

## Skill-Perspective Check

Ran the required perspective check before judging tests and maintainability.

- Loaded and consulted `omo:remove-ai-slops`.
- Loaded and consulted `omo:programming`, including Python `README.md`, `type-patterns.md`, `error-handling.md`, and `async-anyio.md`.
- Result:
  - The authorise-many registry blocker fix is real and the new auth tests are not hollow.
  - The split production modules are now under the 250 pure-LOC threshold, except the pre-existing oversized `mcp.py`.
  - The diff still violates both perspectives at the lazy dependency/auth boundary: production dependency/configuration errors from the IAM authorizer can be collapsed into ordinary token rejection.

## Findings

### CRITICAL

None.

### HIGH

1. Lazy IAM dependency failures are hidden as invalid-token auth denials.

`GatewayTokenVerifier.verify_token()` calls `_authorised_legal_scopes(...)` inside the same broad `except Exception` block that handles gateway auth failures, then returns `None` on any exception:

- `trustgraph-mcp/trustgraph/mcp_server/auth.py:42-51`

The IAM dependency loading itself is lazy and occurs only when `IamScopeAuthorizer._make_client()` runs:

- `trustgraph-mcp/trustgraph/mcp_server/auth.py:90-111`
- `trustgraph-mcp/trustgraph/mcp_server/auth.py:174-200`

Boundary probe:

```text
PYTHONPATH=trustgraph-mcp:. /opt/homebrew/bin/python3 - <<'PY' ...
MCP Bearer token rejected by gateway: ModuleNotFoundError
None
```

That probe used the real `IamScopeAuthorizer` path with a fake successful gateway `whoami`; `_load_iam_dependencies()` failed because `trustgraph-base` was absent from `PYTHONPATH`, and the verifier returned `None` instead of surfacing a dependency/configuration error. This is fail-closed, but it violates the assignment's explicit acceptance criterion that lazy imports must not hide production dependency errors.

Impact: a missing or API-broken IAM client dependency can present to clients and operators as token rejection rather than server misconfiguration. It also makes startup and verification evidence weaker because the production IAM dependency path is not fail-fast.

### MEDIUM

None.

### LOW

1. `trustgraph-mcp/trustgraph/mcp_server/mcp.py` remains an oversized module.

Pure LOC measurement reports `mcp.py` far over the 250-line programming-skill threshold. This is pre-existing and the current diff only wires auth/pubsub arguments, so I am not treating it as a blocker for this re-review. It remains a maintenance risk.

2. The new auth-boundary test is untracked and not in the requested py_compile list.

`tests/unit/legal_ontology/test_mcp_auth_boundary.py` is currently untracked, but the full required unit command collects it and it passes. I also compiled it separately. This is not a code blocker, but it must be included if the branch is committed.

## Positive Verification

Earlier registry blocker: fixed.

- Current auth code no longer sends MCP scope decisions through `WebSocketManager.request("iam", {"operation": "authorise-many"})`.
- `trustgraph-mcp/trustgraph/mcp_server/auth.py:38-45` uses the gateway WebSocket for `whoami`.
- `trustgraph-mcp/trustgraph/mcp_server/auth.py:75-78` uses the internal IAM client `authorise_many(...)`.
- Targeted search now finds only gateway `whoami` on the public WebSocket and internal `client.authorise_many(...)` for scope decisions.

Test shape: acceptable for the fixed blocker.

- `tests/unit/legal_ontology/test_mcp_auth_boundary.py:17-58` fails if the verifier uses the public WebSocket request path for scope decisions.
- `tests/unit/legal_ontology/test_mcp_auth_boundary.py:61-115` proves `IamScopeAuthorizer` calls `authorise_many(...)` and maps allowed checks back to scopes.
- `tests/unit/legal_ontology/test_mcp_domain_tools.py:125-170` rejects raw-token strings and requires a gateway-verified `AuthContext`.
- `tests/integration/legal_ontology/test_mcp_tools.py:194-255` covers the adapter-level auth contract and scope enforcement against fake MCP registration.

CLI/server wiring: mostly sensible.

- `trustgraph-mcp/trustgraph/mcp_server/mcp.py:291-298` builds or accepts a pubsub backend and injects `IamScopeAuthorizer`.
- `trustgraph-mcp/trustgraph/mcp_server/mcp.py:364-367` registers debt tools with `require_token`.
- `trustgraph-mcp/trustgraph/mcp_server/mcp.py:1945-1959` adds pubsub CLI args and passes config to `McpServer`.

Split/refactor shape: acceptable.

- `trustgraph_legal/classifier.py`, `classifier_types.py`, `classifier_rules.py`, and `classifier_manifest.py` split the former classifier responsibilities cleanly.
- `trustgraph_legal/mcp_domain.py`, `mcp_handlers.py`, `mcp_envelope.py`, and `mcp_inputs.py` split the former MCP domain module into registry/dispatch, handlers, envelope/redaction, and input/path helpers.
- No deletion-only or tautological test pattern was found in the reviewed authz tests.

## Verification Commands

Required commands were rerun against the current tree.

```text
/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology -q
41 passed in 0.97s
```

```text
/opt/homebrew/bin/python3 -m pytest tests/integration/legal_ontology/test_mcp_tools.py -q
3 passed in 2.18s
```

```text
/usr/bin/python3 -m py_compile trustgraph_legal/classifier.py trustgraph_legal/classifier_types.py trustgraph_legal/classifier_rules.py trustgraph_legal/classifier_manifest.py trustgraph_legal/mcp_domain.py trustgraph_legal/mcp_handlers.py trustgraph_legal/mcp_envelope.py trustgraph_legal/mcp_inputs.py trustgraph_legal/ingest.py trustgraph-mcp/trustgraph/mcp_server/auth.py trustgraph-mcp/trustgraph/mcp_server/legal_tools.py trustgraph-mcp/trustgraph/mcp_server/mcp.py scripts/legal_ontology/evaluate_packet.py tests/unit/legal_ontology/test_evaluate_packet.py tests/unit/legal_ontology/test_ingest.py tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py
exit 0
```

Additional checks:

```text
git diff --check
exit 0

/usr/bin/python3 -m py_compile tests/unit/legal_ontology/test_mcp_auth_boundary.py
exit 0

/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_auth_boundary.py -q
2 passed in 0.08s
```

Pure LOC check on reviewed changed files:

```text
trustgraph_legal/classifier.py                          89
trustgraph_legal/classifier_types.py                   137
trustgraph_legal/classifier_rules.py                   203
trustgraph_legal/classifier_manifest.py                 56
trustgraph_legal/mcp_domain.py                         155
trustgraph_legal/mcp_handlers.py                       182
trustgraph_legal/mcp_envelope.py                        80
trustgraph_legal/mcp_inputs.py                          46
trustgraph_legal/ingest.py                             152
trustgraph-mcp/trustgraph/mcp_server/auth.py           171
trustgraph-mcp/trustgraph/mcp_server/legal_tools.py     95
tests/unit/legal_ontology/test_mcp_domain_tools.py     199
tests/integration/legal_ontology/test_mcp_tools.py     279
```

## Blockers

- Separate lazy IAM dependency/configuration errors from normal gateway token rejection. At minimum, `GatewayTokenVerifier.verify_token()` should not catch `ImportError`/`ModuleNotFoundError`/programming errors from the scope authorizer as invalid tokens; preferably validate the default IAM authorizer dependencies at server construction or let those failures fail loudly with stack context.

VERDICT: REJECT
