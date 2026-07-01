# Final Security/Authz Re-Review

Repository: `/Users/cosmos/dev/ontology/trustgraph`
Review scope: current uncommitted debt-collection ontology/MCP diff, focused on MCP auth/security/privacy boundary after the `authorise-many` blocker fix.
Date: 2026-07-01

## Skill-Perspective Check

- `omo:remove-ai-slops` was consulted before judging tests and production code. Result: no deletion-only, tautological, implementation-constant-only, or requested-removal-only blocker tests found. One low duplication note is listed below.
- `omo:programming` plus its Python reference was consulted. Result: no blocker under the auth/privacy acceptance criteria. The new auth code still uses untyped `Any` around external MCP/pubsub/IAM seams; acceptable for this patch, but worth tightening later.

## Evidence Inspected

- Current worktree status and diff for the named files, plus untracked `auth.py`, `mcp_inputs.py`, and related MCP/privacy files.
- Smoke artifact `.omo/evidence/debt-collection-ontology/final-mcp-scope-smoke.txt`.
- Production IAM client contract in `trustgraph-base/trustgraph/base/iam_client.py`.
- Gateway IAM registry and `whoami` handling in `trustgraph-flow`.

## Verification Run

- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py -q`
  - Result: `11 passed in 2.33s`.
- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_auth_boundary.py -q`
  - Result: `2 passed in 0.24s`.
- `/opt/homebrew/bin/python3 -m py_compile trustgraph-mcp/trustgraph/mcp_server/auth.py trustgraph-mcp/trustgraph/mcp_server/legal_tools.py trustgraph-mcp/trustgraph/mcp_server/mcp.py trustgraph_legal/mcp_inputs.py trustgraph_legal/mcp_domain.py trustgraph_legal/mcp_envelope.py trustgraph_legal/mcp_handlers.py`
  - Result: passed with no output.

## Findings By Severity

### CRITICAL

None.

### HIGH

None.

### MEDIUM

None blocking.

Hardening note: `trustgraph-mcp/trustgraph/mcp_server/auth.py:135` falls back to `mcp-caller` when the `whoami` identity shape has no usable id/username/handle/email. Real IAM/no-auth `whoami` responses appear to include user ids, and the current path still asks internal IAM before granting tool scopes, so this is not a blocker for the current fix. Before broadening this auth layer, fail closed on malformed identity instead of authorizing a synthetic fallback identity.

### LOW

- `tests/unit/legal_ontology/test_mcp_auth_boundary.py:17` and `tests/unit/legal_ontology/test_mcp_auth_boundary.py:61` duplicate the same auth-boundary coverage now present in `tests/unit/legal_ontology/test_mcp_domain_tools.py:176` and `tests/unit/legal_ontology/test_mcp_domain_tools.py:220`. The duplicate tests pass and are not misleading, but they add maintenance surface.

## Acceptance Criteria Check

- No bearer token as a debt-tool argument: PASS. Registered debt tool handlers accept `arguments` only, and tests assert an `authorization=` kwarg is rejected (`legal_tools.py:71`, `tests/integration/legal_ontology/test_mcp_tools.py:218`).
- No auth token echo: PASS. Tool wrappers return redacted envelopes and tests/smoke assert token absence (`tests/integration/legal_ontology/test_mcp_tools.py:217`, smoke lines 19 and 22).
- No raw PII echo: PASS for covered sensitive shapes. `redact_json` recursively redacts handler output (`mcp_domain.py:140`, `mcp_envelope.py:45`), and tests cover national id, phone, account, and nested source-ref excerpts.
- No outside-root file reads: PASS. `path_arg` resolves and rejects paths outside the resolved repo root (`trustgraph_legal/mcp_inputs.py:36`), and tests assert neither secret content nor outside path is echoed.
- Public gateway websocket `iam/authorise-many` is not used for MCP scope checks: PASS. `GatewayTokenVerifier` uses gateway `whoami` only, then delegates scopes to the injected/internal authorizer (`auth.py:35`). The fake websocket test raises if public IAM requests are attempted, and the smoke records `public_authorise_many_used=false`.
- Production path uses internal IAM `authorise_many`: PASS. `McpServer` defaults `scope_authorizer` to `IamScopeAuthorizer(self.pubsub_backend)` (`mcp.py:291`), and `IamScopeAuthorizer` calls `IamClient.authorise_many` (`auth.py:75`). The production `IamClient.authorise_many` returns the tuple shape consumed by this code.
- Reader scopes cannot call governance tools: PASS. Legal tool registration passes each tool's required scope to `require_token`/`_require_context_auth` (`legal_tools.py:46`, `legal_tools.py:87`), and tests assert a token with only `read:tools` cannot call `promote_ontology_candidate`.

## Scope And Regression Risk

The prior blocker is addressed: MCP scope authorization no longer goes through the public gateway websocket operation registry for `iam/authorise-many`. The new boundary is fail-closed on bad gateway auth and missing required scopes. Remaining risk is localized to future identity-shape hardening and duplicate test cleanup, neither of which invalidates the requested final accept criteria.

codeQualityStatus: WATCH
recommendation: APPROVE
blockers: []

VERDICT: ACCEPT
