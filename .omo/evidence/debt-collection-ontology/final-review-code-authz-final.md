# Final Code Authz Re-review

codeQualityStatus: CLEAR
recommendation: APPROVE
reportPath: `.omo/evidence/debt-collection-ontology/final-review-code-authz-final.md`
blockers: []

## Scope

Narrow final re-review of the current uncommitted auth-boundary diff after the second blocker fix.

Focus:
- Whether the previous blocker is resolved: `GatewayTokenVerifier.verify_token()` must not report lazy IAM dependency/configuration failures as bad bearer tokens.
- Whether the final changed unit is acceptable: `trustgraph-mcp/trustgraph/mcp_server/auth.py`, `trustgraph-mcp/trustgraph/mcp_server/mcp.py`, and `tests/unit/legal_ontology/test_mcp_auth_boundary.py`.
- Broader legal ontology/MCP verification requested by the assignment.

Not reviewed as a full branch quality gate: the many unrelated uncommitted legal ontology changes outside this auth-boundary slice.

## Skill-Perspective Check

Ran the required skill-perspective check before judging test relevance and maintainability:
- `omo:remove-ai-slops`: consulted. The new regression test is not deletion-only, not tautological, not merely asserting a requested removal, and not just mirroring a constant. It would fail against the previous broad-catch behavior because `verify_token()` would return `None` instead of raising `RuntimeError`.
- `omo:programming`: consulted, including the Python and code-smell references. The final auth unit has minor adapter-bound type looseness (`Any` around external MCP/IAM identity/pubsub seams), and `mcp.py` remains oversized. I do not treat these as final blockers for this narrow re-review because the auth extraction keeps the new focused unit under the 250 pure-LOC threshold, the oversized `mcp.py` condition is pre-existing and not worsened by the final fix, and the observable auth failure boundary is locked by tests.

Diff does not contain a blocking violation of either skill perspective.

## Previous Blocker Resolution

Resolved.

The previous blocker report said `_authorised_legal_scopes(...)` was called inside the same broad `except Exception` block that handled gateway auth failures, so lazy IAM failures were logged as token rejection and returned `None`.

Current code separates the two phases:
- Gateway token validation phase: `trustgraph-mcp/trustgraph/mcp_server/auth.py:38-52` creates `WebSocketManager`, runs `start()` and `whoami()`, logs gateway failures, returns `None`, and always attempts cleanup.
- Scope authorizer phase: `trustgraph-mcp/trustgraph/mcp_server/auth.py:54-64` calls `_authorised_legal_scopes(...)` after gateway validation has succeeded; any authorizer exception is logged with `logger.exception(...)` and re-raised as `RuntimeError("MCP IAM scope authorizer failed")`.
- Server wiring uses this verifier: `trustgraph-mcp/trustgraph/mcp_server/mcp.py:320-327`.

That matches the requested boundary: gateway `start/whoami` failures are token denial, while IAM scope authorizer failures are surfaced as server authorizer failure.

## Test Evidence

Command:

```text
/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_auth_boundary.py -q
```

Result:

```text
collected 3 items
tests/unit/legal_ontology/test_mcp_auth_boundary.py ... [100%]
3 passed in 0.33s
```

Command:

```text
/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology -q
```

Result:

```text
collected 42 items
tests/unit/legal_ontology/test_mcp_auth_boundary.py ... [50%]
42 passed in 1.72s
```

Command:

```text
/opt/homebrew/bin/python3 -m pytest tests/integration/legal_ontology/test_mcp_tools.py -q
```

Result:

```text
collected 3 items
tests/integration/legal_ontology/test_mcp_tools.py ... [100%]
3 passed in 2.23s
```

## Findings

### CRITICAL

None.

### HIGH

None.

### MEDIUM

None.

### LOW

1. `trustgraph-mcp/trustgraph/mcp_server/mcp.py` remains oversized.

Pure LOC measurement reports `mcp.py` at 1571 pure LOC, far above the programming-skill 250-line threshold. This is a standing maintainability risk, but the final auth fix does not add the blocker back and the auth verifier has been extracted to `auth.py` at 178 pure LOC. Not approval-blocking for this narrow re-review.

2. New auth-boundary files are untracked in the working tree.

`trustgraph-mcp/trustgraph/mcp_server/auth.py` and `tests/unit/legal_ontology/test_mcp_auth_boundary.py` are currently untracked. This is not a code-quality blocker for the current executable review because the requested commands collected and passed them, but they must be included when the branch is committed.

## Review Notes

- The new regression `tests/unit/legal_ontology/test_mcp_auth_boundary.py:61-90` is relevant: it simulates a successful gateway `whoami()` and a failing scope authorizer, then requires `RuntimeError` matching `scope authorizer`.
- The test is not hollow: under the previous broad-catch implementation it would have failed because no `RuntimeError` would be raised.
- The gateway success path remains covered by `tests/unit/legal_ontology/test_mcp_auth_boundary.py:17-58`, including the scope authorizer receiving the gateway identity and the verifier returning the authorized scopes.
- The adapter integration check still verifies raw token strings are rejected, per-tool required scope is enforced, and tokens are not echoed: `tests/integration/legal_ontology/test_mcp_tools.py:194-255`.

## Final Decision

The prior HIGH blocker is fixed, no new security or compatibility blocker is introduced in the final changed auth-boundary unit, the new test is behavior-relevant, and the requested legal ontology/MCP verification is green.

VERDICT: ACCEPT
