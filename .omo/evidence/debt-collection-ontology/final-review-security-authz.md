# Final Security/Authz Review - Debt Collection MCP

codeQualityStatus: WATCH
recommendation: APPROVE
reportPath: `.omo/evidence/debt-collection-ontology/final-review-security-authz.md`
blockers: None

## Scope

Reviewed repository `/Users/cosmos/dev/ontology/trustgraph` on branch `master`, current uncommitted diff only. Focus was the final MCP debt-collection domain-server authz/privacy boundary.

Key files inspected:
- `trustgraph-mcp/trustgraph/mcp_server/auth.py`
- `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py`
- `trustgraph-mcp/trustgraph/mcp_server/mcp.py`
- `trustgraph_legal/mcp_domain.py`
- `trustgraph_legal/mcp_inputs.py`
- `trustgraph_legal/mcp_handlers.py`
- `trustgraph_legal/mcp_envelope.py`
- `tests/integration/legal_ontology/test_mcp_tools.py`
- `tests/unit/legal_ontology/test_mcp_domain_tools.py`
- `.omo/evidence/debt-collection-ontology/final-mcp-scope-smoke.txt`

## Skill-Perspective Check

Ran the required skill-perspective check:
- Loaded `omo:remove-ai-slops`.
- Loaded `omo:programming`.
- Loaded the Python programming reference README before judging Python test relevance and maintainability.

Result: no blocking remove-ai-slops or programming-perspective violation in the security/authz acceptance path. The tests added here are not deletion-only, tautological, or mere requested-removal assertions; they exercise observable auth/path/privacy behavior. The production change does not add unnecessary data extraction/parsing for the stated authz/privacy goal.

## Commands And Evidence Inspected

- `git status --short --branch`
  - Confirmed branch `master...origin/master [ahead 36]` and relevant key files modified/untracked.
- `git diff -- trustgraph-mcp/trustgraph/mcp_server/auth.py trustgraph-mcp/trustgraph/mcp_server/legal_tools.py trustgraph-mcp/trustgraph/mcp_server/mcp.py trustgraph_legal/mcp_domain.py trustgraph_legal/mcp_inputs.py tests/integration/legal_ontology/test_mcp_tools.py tests/unit/legal_ontology/test_mcp_domain_tools.py`
  - Confirmed tracked diff removes passthrough token verifier and tool-argument auth pattern, adds required scopes to tool registration, and moves path/input/envelope handling into dedicated modules.
  - `auth.py` and `mcp_inputs.py` are untracked, so I inspected their current contents directly with `nl -ba`.
- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py -q`
  - Passed: `9 passed in 2.11s`.
- `rg -n "authorise_many_used|authorise-many|bad_token_rejected|reader_governance_rejected|token_echo=false|token_echo=False" .omo/evidence/debt-collection-ontology/final-mcp-scope-smoke.txt`
  - Confirmed `bad_token_rejected=true`, `authorise_many_used=true`, `reader_governance_rejected=true`, and `token_echo=false` / `token_echo=False`.
- Targeted keyword scan over MCP auth/path files and tests for `authorization`, `Bearer`, `token_resolver`, `AuthContext`, `require_token`, `authorise-many`, `whoami`, `path_arg`, `read_text`, `collect_registry_payload`.
- AST syntax check over the key Python modules: `ast_parse_ok 7`.
- Direct import smoke was attempted with `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=trustgraph-mcp:trustgraph-base:. /opt/homebrew/bin/python3 -c ...`; it failed because this local Python environment lacks the `mcp` package. I did not treat that as a code blocker because the supplied HTTP smoke explicitly used a temporary venv with `mcp` installed and reached the MCP SDK surface.

## Acceptance Checks

- No token required as a tool argument: PASS.
  - `legal_tools.py:21` exposes tool functions with only `arguments`; `legal_tools.py:78` invokes auth from context before dispatch.
  - Tests assert no `authorization` parameter and reject injected `authorization=...`: `tests/unit/legal_ontology/test_mcp_domain_tools.py:139`, `tests/integration/legal_ontology/test_mcp_tools.py:218`.

- MCP auth context/token resolver only: PASS.
  - `mcp.py:300` constructs `FastMCP` with `GatewayTokenVerifier`; `mcp.py:344` registers debt tools with `token_resolver=require_token`.
  - `legal_tools.py:96` calls `token_resolver(required_scope)` and `legal_tools.py:100` rejects raw token strings unless they are an `AuthContext`.

- Gateway token validated with `whoami`: PASS.
  - `auth.py:25` creates a gateway `WebSocketManager`, `auth.py:27` starts it, and `auth.py:28` calls `whoami` before returning an `AccessToken`.

- IAM `authorise-many` per-tool authorization used: PASS.
  - `auth.py:89` derives the set of debt tool scopes from `list_tools()`.
  - `auth.py:98` sends IAM operation `authorise-many`; `auth.py:103` consumes the gateway IAM response.
  - `mcp_domain.py:22` defines distinct per-tool scopes, and `legal_tools.py:48` binds each registered handler to its required scope.

- Reader tokens cannot invoke governance/write scopes: PASS.
  - `legal_tools.py:104` denies calls when the auth context lacks the required scope.
  - Unit/integration tests include a read-only context denied on `promote_ontology_candidate`: `tests/integration/legal_ontology/test_mcp_tools.py:236`.
  - Smoke evidence confirms `reader_governance_rejected=true`.

- Path traversal/outside-root reads blocked before file read: PASS.
  - `mcp_inputs.py:36` normalizes path input, resolves it, and `mcp_inputs.py:44` requires it to be under the resolved repo root before returning a path.
  - File reads happen only after `path_arg`: `mcp_handlers.py:32` before `collect_registry_payload`, and `mcp_handlers.py:180` before `read_text`.
  - `mcp_domain.py:142` catches `PermissionError` and returns stable redacted `path_outside_repo_root` errors without embedding the absolute path.

- Token/secret/path values are not echoed: PASS.
  - Auth failure logging in `auth.py:31` logs only the exception type, not the token.
  - Envelope redaction is centralized in `mcp_envelope.py:45`; nested source refs are converted to pointer strings at `mcp_envelope.py:89`.
  - Tests verify sensitive text and outside paths are absent from outputs: `tests/unit/legal_ontology/test_mcp_domain_tools.py:177`, `tests/unit/legal_ontology/test_mcp_domain_tools.py:198`, `tests/integration/legal_ontology/test_mcp_tools.py:106`.
  - Smoke evidence confirms `token_echo=false`.

## Findings

### CRITICAL

None.

### HIGH

None.

### MEDIUM

None.

### LOW

- `trustgraph-mcp/trustgraph/mcp_server/auth.py:70` - Non-blocking hardening note: `_identity_client_id` accepts several gateway identity shapes and falls back to `"mcp-caller"` at `auth.py:82` when no concrete identity is present. Normal IAM `whoami` returns `user.id`, and full IAM denies unknown users in `authorise-many`, so I do not see a current governance-scope escalation in the inspected path. A future hardening pass should fail closed on malformed `whoami` identity rather than authorizing a fallback principal.

## Verdict

The current diff fixes the stale rejected issues: Bearer auth is not a tool argument, gateway validation happens through MCP auth context, debt scopes are authorized through IAM `authorise-many`, reader contexts are denied governance tools, and path inputs are bounded under `repo_root` before file reads with stable redacted errors.

VERDICT: ACCEPT
