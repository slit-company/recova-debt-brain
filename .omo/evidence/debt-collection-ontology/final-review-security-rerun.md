# Debt Collection Ontology Final Security/Privacy Re-Review

Date: 2026-06-30

## PASS/FAIL

FAIL

## recommendation

REJECT

## originalIntent

Deliver a TrustGraph debt-collection ontology/domain MCP surface that is safe for sensitive legal workflows: gateway-backed authentication, scoped local tool calls, no raw token echo, no raw sensitive identifier leakage, pointer-only source references, repo-root-bounded path inputs, and no direct filing/contact/payment/collection execution.

## desiredOutcome

The user should receive evidence that the prior security blockers were fixed and that the shipped artifact can be used by an MCP client without accepting unverified tokens, leaking secrets or raw PII, reading outside the configured repo root, or returning source text/excerpts through provenance fields.

## userOutcomeReview

The two prior explicit blockers were mostly addressed:

- The debt-collection adapter now requires a gateway-verified `AuthContext` and rejects raw string token resolvers.
- The changed source/test/doc files and existing evidence files no longer contain national-ID, phone, or account-shaped raw literals under the separator-required scan.

However, the re-review is still a FAIL. The current diff introduces or leaves two user-visible safety blockers:

- Generic MCP gateway-backed tools now pass an `AuthContext` object where the socket manager expects a raw token string, which breaks the authenticated gateway forwarding path outside the local debt-collection tools.
- Top-level `source_refs` are not pointer-only for adversarial caller-supplied case graphs; nested `source_refs` objects can be copied upward with an `excerpt` key, even though the value is redacted.

There is also an approval evidence gap: the latest code-quality report does not explicitly show the required `remove-ai-slops` overfit/slop and `programming` skill-perspective coverage, and the direct pass found an oversized touched Python module.

## blockers

### B1. AuthContext is passed into the generic gateway socket path

Severity: High

Evidence:

- `trustgraph-mcp/trustgraph/mcp_server/mcp.py:144-171` changed `_require_token()` to return `AuthContext`.
- `trustgraph-mcp/trustgraph/mcp_server/mcp.py:438-445` still assigns `token = _require_token()` and passes that object into `get_socket_manager(ctx, token)`.
- `trustgraph-mcp/trustgraph/mcp_server/mcp.py:174-198` passes that value to `_token_key(token)` and `WebSocketManager(..., token=token)`.
- `trustgraph-mcp/trustgraph/mcp_server/tg_socket.py:12-14` requires a string token because `_token_key()` calls `token.encode()`.

Focused probe:

```text
_token_key(AuthContext(...)) -> AttributeError: 'AuthContext' object has no attribute 'encode'
```

Impact:

- The new gateway verifier can create an MCP auth context, but existing generic TrustGraph MCP tools that use `_get_manager()` can fail before reaching the gateway.
- The focused pytest set does not cover this path; it only covers the local debt-collection adapter.

Fix expectation:

- `_get_manager()` should pass `_require_token().token` to `get_socket_manager()` or `_require_token()` should keep returning a token string for generic gateway tools while exposing a separate `AuthContext` resolver for debt tools.

### B2. `source_refs` are not pointer-only for caller-supplied nested source refs

Severity: High

Evidence:

- `trustgraph_legal/mcp_domain.py:355-363` returns caller-supplied `case_graph` dictionaries.
- `trustgraph_legal/mcp_domain.py:448-469` collects nested `source_refs` items by redacting and preserving the full object shape.
- A focused probe with a caller-supplied nested source ref containing an `excerpt` field returned top-level `source_refs` containing both the pointer string and a redacted object with an `excerpt` key.

Focused probe result:

```json
{
  "source_refs_pointer_only": false,
  "source_refs_raw_pii_redacted": true
}
```

Impact:

- Raw sensitive values are redacted, but the provenance field can still carry source-text/excerpt structure.
- This violates the requested pointer-only `source_refs` boundary and the test helper only checks representative outputs, not this adversarial input class.

Fix expectation:

- `_collect_source_refs()` should normalize every source ref to pointer identifiers only, such as strings or a minimal pointer schema, and must drop text/excerpt/raw fields from top-level `source_refs`.

### B3. Required slop/overfit review coverage is absent

Severity: Medium

Evidence:

- `.omo/evidence/debt-collection-ontology/f2-code-quality.md` records tests, compile checks, privacy scan, and security regression evidence, but does not explicitly document the required `remove-ai-slops` overfit/slop lens or `programming` criteria coverage.
- Direct `programming`/`remove-ai-slops` pass found `trustgraph-mcp/trustgraph/mcp_server/mcp.py` at 1620 pure LOC while the current diff adds auth logic to that file.

Impact:

- This does not replace B1/B2, but it is an approval evidence gap under the final-gate criteria.
- The oversized touched module increases review risk and helped hide the `_require_token()` return-type regression.

## evidence

### Prior blocker re-checks

- Adapter rejects raw string token resolvers:
  - `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py:12-18` defines `AuthContext` and `TokenResolver = Callable[[str], AuthContext]`.
  - `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py:87-105` rejects non-`AuthContext`, unverified, empty-token, and missing-scope contexts.
  - Consolidated probe: `adapter_raw_string_rejected=true`.
- Adapter requires gateway-verified AuthContext/scope:
  - `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py:46-56` passes each tool's required scope to the resolver.
  - `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py:100-105` enforces verified context and scope.
  - Consolidated probe: `adapter_verified_context_accepted=true`, `adapter_scope_required=true`.
- MCP TokenVerifier validates via gateway before AccessToken:
  - `trustgraph-mcp/trustgraph/mcp_server/mcp.py:72-95` starts a gateway WebSocket and calls `whoami()` before returning `AccessToken`.
  - `trustgraph-mcp/trustgraph/mcp_server/mcp.py:391` registers `GatewayTokenVerifier(websocket_url)`.
  - `rg` found no remaining `PassthroughTokenVerifier`.
- Tests no longer contain raw shaped literals:
  - Separator-required scan over the changed source/test/doc files returned no national-ID, phone, or account-shaped hits.
  - The tests still construct sensitive samples from fragments, which matches the prior fix expectation and does not create raw shaped literals.

### Additional requested checks

- Path bounding:
  - `trustgraph_legal/mcp_domain.py:396-407` resolves candidate paths and requires `resolved.relative_to(root)`.
  - Consolidated probe: `path_bounding_rejects_outside=true`.
- Token non-echo:
  - Consolidated probe: `adapter_token_non_echo=true`.
  - Tests assert fake tokens are not present in serialized authorized tool responses.
- `source_refs` pointer-only:
  - Consolidated probe: `source_refs_pointer_only=false`.
  - See blocker B2.
- Non-execution boundary:
  - `trustgraph_legal/mcp_domain.py:311-320` returns non-executing recommendations with `no_direct_filing_contact_or_collection=True`.
  - Consolidated probe: `non_execution_unknown_tool=true`, `non_execution_recommendation_flag=true`.
- Raw PII scan:
  - Separator-required scan over changed source/test/doc files: no hits.
  - Separator-required scan over `.omo/evidence/debt-collection-ontology` and `.omo/evidence/debt-collection-ontology-findings.md`: no hits.
- Focused pytest:
  - `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py tests/unit/legal_ontology/test_ingest.py -q`
  - Result: 11 passed.
- Compile/check:
  - `/opt/homebrew/bin/python3 -m py_compile ...`
  - Result: passed.
  - `git diff --check`
  - Result: passed.

## checked artifact paths

- `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py`
- `trustgraph-mcp/trustgraph/mcp_server/mcp.py`
- `trustgraph-mcp/trustgraph/mcp_server/tg_socket.py`
- `trustgraph_legal/mcp_domain.py`
- `trustgraph_legal/ingest.py`
- `tests/unit/legal_ontology/test_mcp_domain_tools.py`
- `tests/integration/legal_ontology/test_mcp_tools.py`
- `tests/unit/legal_ontology/test_ingest.py`
- `docs/product/debt-collection-ontology/mcp-domain-server-contract.md`
- `.omo/evidence/debt-collection-ontology/f2-code-quality.md`
- `.omo/evidence/debt-collection-ontology/f3-real-qa.txt`
- `.omo/evidence/debt-collection-ontology/final-review-security.md`
- `.omo/evidence/debt-collection-ontology/*`
- `.omo/evidence/debt-collection-ontology-findings.md`

## exact evidence gaps

- No focused test covers `_get_manager()` after `_require_token()` changed from raw string to `AuthContext`.
- No test covers adversarial nested `source_refs` objects containing source-text/excerpt-shaped keys.
- The latest code-quality report lacks explicit `remove-ai-slops` overfit/slop and `programming` criteria coverage.
- Runtime import of `trustgraph.mcp_server.mcp` under the base `/opt/homebrew/bin/python3` environment fails because the `mcp` package is not installed there; prior MCP runtime smoke evidence depends on a temporary venv artifact rather than the base interpreter.

## final status

FAIL. Do not approve until B1 and B2 are fixed and re-verified. B3 must also be closed before final gate approval.
