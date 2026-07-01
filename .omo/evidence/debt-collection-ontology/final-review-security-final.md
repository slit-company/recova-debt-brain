# Debt Collection Ontology Final Security/Privacy Re-Review

Date: 2026-06-30

## verdict

FAIL

## recommendation

REJECT

## originalIntent

Ship a TrustGraph debt-collection ontology/MCP domain surface that can be used by MCP clients without accepting unverified tokens, bypassing gateway/IAM authorization, leaking raw bearer tokens or legal PII, exposing source text through provenance fields, reading outside the repo root, or executing filing/contact/collection/payment actions.

## desiredOutcome

The user should receive a final gate report proving the prior blockers are closed: generic MCP auth uses a real gateway-verified token path, debt tools enforce per-scope authorization backed by the gateway/IAM regime, `source_refs` are pointer-only, path inputs are repo-root bounded, tokens and raw PII are not echoed, and tool calls remain advisory/non-executing.

## userOutcomeReview

Current code and evidence close several prior security/privacy blockers:

- Generic MCP server wiring now uses `GatewayTokenVerifier`, not the old passthrough verifier.
- `_get_manager()` now passes `require_token().token` into the WebSocket/socket-key path, so the stale `AuthContext.encode()` regression is fixed.
- Debt-collection adapter calls reject raw string token resolvers, require a gateway-marked `AuthContext`, and check the requested tool scope locally.
- Nested caller-supplied `source_refs` are normalized to pointer strings and redacted.
- Outside-root path attempts return `path_outside_repo_root` without echoing file path/content.
- Focused probes found no raw PII leakage from user-controlled fields and no token echo in tool output.
- Direct execution remains unavailable: `execute_direct_collection_filing` returns `unknown_tool`, and recommendations carry the non-execution flag.

The user-visible outcome is still not safe enough to approve because gateway-backed per-scope authorization is not actually proven or implemented. The current code authenticates through the gateway with `whoami`, then derives debt-tool scopes locally from returned roles. In the TrustGraph gateway/IAM contract, `whoami` is an authenticated self-read, and authorization decisions are supposed to go through `authorise()`. The final scoped smoke uses a fake gateway that returns a `reader` role, so it proves local role mapping behavior, not a real gateway/IAM per-scope authorization decision.

## blockers

### B1. Gateway authentication is still being treated as gateway authorization

Severity: High

Evidence:

- `trustgraph-mcp/trustgraph/mcp_server/auth.py:21-44` validates the bearer token by opening a gateway WebSocket and calling `manager.whoami()`, then returns MCP `AccessToken` scopes from `_legal_scopes_from_identity(identity)`.
- `trustgraph-mcp/trustgraph/mcp_server/auth.py:83-98` maps `reader`, `writer`, and `admin` roles to local legal MCP scopes.
- `trustgraph-mcp/trustgraph/mcp_server/tg_socket.py:91-98` implements `whoami()` as an IAM `whoami` request.
- `trustgraph-base/trustgraph/base/iam_client.py:54-57` documents `whoami` as authenticated-only self-read with "no capability check".
- `trustgraph-base/trustgraph/base/iam_client.py:104-122` documents `authorise()` as the IAM capability decision API.
- `trustgraph-flow/trustgraph/gateway/auth.py:263-308` documents roles from JWT/API-key resolution as ignored by gateway policy and backward-compatibility hints; policy decisions go through `authorise`.
- `trustgraph-flow/trustgraph/gateway/auth.py:344-397` implements the real gateway authorization decision path.
- `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py:87-105` enforces scopes from the MCP auth context, but those scopes were locally derived from `whoami` roles rather than an IAM `authorise` decision for the requested debt-tool capability/scope.

Impact:

- A token that can pass gateway authentication and expose a broad or misleading role can receive local debt-tool scopes without a gateway/IAM authorization check for `read:tools`, `governance:review`, `governance:reprocess`, etc.
- The documented contract says the gateway remains the source of truth for identity and permissions; the current implementation only proves gateway-backed identity plus local role mapping.

Fix expectation:

- Before a debt tool handler runs, ask the gateway/IAM authorization path for the requested scope/capability, or consume explicit gateway-issued capability/scope data that is documented and tested as authoritative.
- Re-run the scoped MCP smoke against a fake or real gateway that models deny/allow from `authorise`, not just `whoami` roles.

### B2. Scope evidence is overfit to the local role-mapping implementation

Severity: Medium

Evidence:

- `.omo/evidence/debt-collection-ontology/final-mcp-scope-smoke.txt` says the fake gateway maps `reader-token` to role `reader` via `whoami` and verifies `reader_governance_rejected=true`.
- That smoke does not exercise an IAM `authorise` denial for `governance:review` or any explicit per-tool capability check.
- `.omo/evidence/debt-collection-ontology/f2-code-quality.md` records a programming/slop review, but it does not call out this overfit evidence shape.

Impact:

- The test proves the current local implementation rejects one role/scope combination; it does not prove the security property the user asked for: gateway-backed per-scope authorization.
- This is a remove-ai-slops/programming concern as well as a security concern: the evidence mirrors implementation internals and creates false confidence.

## passing checks

- Generic MCP token path: PASS for current wiring. `McpServer._get_manager()` passes `require_token().token` to `get_socket_manager`.
- Raw token resolver rejection: PASS. Direct probe returned `raw_token_resolver_rejected=true`.
- Local scope denial: PASS as a local check. Direct probe returned `reader_governance_denied=true`.
- Token non-echo: PASS. Direct probe returned `adapter_token_not_echoed=true`; live smoke reports `token_echo=false`.
- Nested source refs pointer-only: PASS. Direct probe returned `source_refs_pointer_only=true` and no `excerpt`/`raw_text` in top-level refs.
- Repo-root path bounds: PASS. Direct probe returned `outside_repo_rejected=true` and `outside_repo_no_path_echo=true`.
- Raw PII shape leaks: PASS for focused adversarial probes. User-controlled review fields were redacted and raw national-ID/phone values were absent.
- Direct execution: PASS. Direct execution probe returned `unknown_tool`; recommendations remain non-executing.
- Focused tests: PASS. `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m pytest -p no:cacheprovider tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py -q` -> 9 passed.
- Compile check: PASS. `py_compile` over the named auth/MCP/domain files exited 0.
- Diff whitespace: PASS. `git diff --check` exited 0.

## checked artifact paths

- `trustgraph-mcp/trustgraph/mcp_server/auth.py`
- `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py`
- `trustgraph-mcp/trustgraph/mcp_server/mcp.py`
- `trustgraph-mcp/trustgraph/mcp_server/tg_socket.py`
- `trustgraph_legal/mcp_domain.py`
- `trustgraph_legal/mcp_handlers.py`
- `trustgraph_legal/mcp_envelope.py`
- `trustgraph_legal/mcp_inputs.py`
- `trustgraph-base/trustgraph/base/iam_client.py`
- `trustgraph-flow/trustgraph/gateway/auth.py`
- `trustgraph-flow/trustgraph/gateway/endpoint/auth_endpoints.py`
- `docs/product/debt-collection-ontology/mcp-domain-server-contract.md`
- `tests/unit/legal_ontology/test_mcp_domain_tools.py`
- `tests/integration/legal_ontology/test_mcp_tools.py`
- `.omo/evidence/debt-collection-ontology/final-mcp-scope-smoke.txt`
- `.omo/evidence/debt-collection-ontology/f2-code-quality.md`
- `.omo/evidence/debt-collection-ontology/f3-real-qa.txt`
- `.omo/evidence/debt-collection-ontology/f4-scope-fidelity.md`
- `.omo/evidence/debt-collection-ontology/final-mcp-smoke.txt`
- `.omo/evidence/debt-collection-ontology/final-mcp-smoke.json`
- `.omo/evidence/debt-collection-ontology/final-review-code-rerun.md`
- `.omo/evidence/debt-collection-ontology/final-review-goal-rerun.md`
- `.omo/evidence/debt-collection-ontology/final-review-security-rerun.md`

## exact evidence gaps

- No current code path calls gateway/IAM `authorise()` for the requested debt-tool scope before handler execution.
- No artifact proves `whoami` returns authoritative per-tool debt-collection capabilities/scopes; TrustGraph source comments state the opposite authorization model.
- The scoped MCP smoke uses a fake `whoami` role mapping and does not model gateway/IAM allow/deny decisions.
- The code-quality/slop evidence does not explicitly flag the overfit scope-smoke shape.

## final status

FAIL. Do not approve until per-scope debt-tool authorization is backed by the gateway/IAM authorization contract and re-verified with a non-overfit smoke.
