# Debt Collection Ontology Final Security/Privacy Review

Date: 2026-06-30

## Recommendation

FAIL / REJECT

## Original Intent

Deliver a debt-collection ontology MCP/domain implementation that is safe for sensitive legal workflows: authenticated through MCP context, PII-redacted by default, source-grounded with pointer-only references, bounded to `repo_root` for path inputs, governance/rule-review constrained, and non-executing for filing/contact/payment/collection actions.

## Desired Outcome

The user should receive a domain MCP surface that any MCP client can call without leaking tokens or raw PII, without path traversal outside the configured repository root, and without enabling direct debt-collection execution. Evidence and report artifacts must remain PII-safe.

## User Outcome Review

The implementation is close on redaction, path-boundary, source-ref, and non-execution behavior, but it does not fully satisfy the expected security/privacy outcome. Two blockers remain:

1. Debt-collection MCP tools only require a non-empty auth-context token, while the main MCP verifier accepts any non-empty bearer token locally. These domain tools do not call the gateway, so gateway validation/scoping never occurs for them.
2. A committed integration test file contains literal raw sensitive-pattern strings. This violates the explicit review criterion to avoid raw PII patterns in committed changed files/evidence intended for reports.

## Blockers

### B1. Domain MCP auth is presence-only for debt-collection tools

Severity: High

Evidence:

- `trustgraph-mcp/trustgraph/mcp_server/mcp.py:81-88` accepts any non-empty bearer token into `AccessToken`.
- `trustgraph-mcp/trustgraph/mcp_server/mcp.py:399-402` registers debt-collection tools with `token_resolver=_require_token`.
- `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py:68-81` only checks that the resolver returns a non-empty string.
- The debt-collection handlers in `trustgraph_legal/mcp_domain.py` are local deterministic functions and do not call `get_socket_manager()`/gateway `whoami`, so the comment that the gateway is the source of truth is not true for this tool surface.

Impact:

- Any non-empty bearer token accepted by the MCP middleware can invoke the debt-collection domain tools.
- This is especially risky because some tools read bounded local inputs (`manifest_path`, `case_graph_path`, `zip_path`, `ontology_path`) and return derived content.

Reproduction command:

```bash
/opt/homebrew/bin/python3 - <<'PY'
import json, sys
from pathlib import Path
repo = Path("/Users/cosmos/dev/ontology/trustgraph")
sys.path.insert(0, str(repo))
sys.path.insert(0, str(repo / "trustgraph-mcp"))
from trustgraph.mcp_server import legal_tools

class FakeMcp:
    def __init__(self): self.registered = {}
    def tool(self, name=None):
        def decorate(fn):
            self.registered[name or fn.__name__] = fn
            return fn
        return decorate

fake = FakeMcp()
legal_tools.register_debt_collection_brain_tools(fake, repo, token_resolver=lambda: "any-non-empty-token")
response = fake.registered["list_debt_collection_tools"](arguments={})
print(json.dumps({"accepted": response["tool_name"] == "list_debt_collection_tools"}))
PY
```

Expected current output:

```json
{"accepted": true}
```

Fix expectation:

- Debt-collection tools need an authorization check that validates the token/scopes through the gateway or a real verifier before local tool execution.
- If the intended v0 behavior is local-only, the contract should not claim gateway validation for this surface.

### B2. Committed integration test contains literal raw sensitive patterns

Severity: Medium

Evidence:

- `tests/integration/legal_ontology/test_mcp_tools.py:113` contains a national-ID-shaped literal.
- `tests/integration/legal_ontology/test_mcp_tools.py:114` contains a phone-shaped literal.
- `tests/integration/legal_ontology/test_mcp_tools.py:115` contains an account-shaped literal.
- `git log --follow -- tests/integration/legal_ontology/test_mcp_tools.py` shows this is a committed implementation test file from the debt-collection MCP work.

Reproduction command:

```bash
awk '
  /[0-9][0-9][0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9][0-9][0-9][0-9]/ {print FILENAME ":" FNR ":national_id"}
  /(^|[^0-9])((\+82[-. ]?)?0[0-9][0-9]?[-. ]?[0-9][0-9][0-9][0-9]?[-. ]?[0-9][0-9][0-9][0-9])([^0-9]|$)/ {print FILENAME ":" FNR ":phone"}
  /bank account [0-9][0-9][0-9]-[0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]/ {print FILENAME ":" FNR ":account"}
' tests/integration/legal_ontology/test_mcp_tools.py
```

Expected current output:

```text
tests/integration/legal_ontology/test_mcp_tools.py:113:national_id
tests/integration/legal_ontology/test_mcp_tools.py:114:phone
tests/integration/legal_ontology/test_mcp_tools.py:115:account
```

Fix expectation:

- Construct sensitive test values from fragments, as `tests/unit/legal_ontology/test_mcp_domain_tools.py` already does, or use non-matching placeholders.
- Keep report/evidence artifacts free of literal sensitive patterns.

## Verified Passing Checks

- Tool contracts do not advertise `authorization`, `token`, or `bearer` parameters.
- Context token values are not echoed by adapter-registered tool responses in the focused probe.
- `case_graph_path` escapes are rejected for absolute outside paths, relative traversal, and symlink escapes; rejection does not echo attempted path or file content.
- Representative direct text payloads are redacted for national ID, phone, account, and address patterns.
- Top-level `source_refs` in representative MCP responses are pointer-only and do not contain raw text/excerpts.
- Direct execution probe `execute_direct_collection_filing` returns `unknown_tool`.
- `recommend_next_action` returns `no_direct_filing_contact_or_collection=true`.
- `.omo/evidence/debt-collection-ontology` and Todo 9 team report artifacts scanned in this review had no raw sensitive-pattern hits.

## Commands Run

```bash
/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py -q
# 8 passed

/opt/homebrew/bin/python3 -m py_compile trustgraph_legal/mcp_domain.py trustgraph-mcp/trustgraph/mcp_server/legal_tools.py trustgraph-mcp/trustgraph/mcp_server/mcp.py trustgraph-mcp/trustgraph/mcp_server/tg_socket.py scripts/legal_ontology/evaluate_packet.py
# passed

git diff --check
# passed

/opt/homebrew/bin/python3 - <<'PY'
from pathlib import Path
import json
from scripts.legal_ontology.evaluate_packet import evaluate_packet
repo = Path("/Users/cosmos/dev/ontology/trustgraph")
print(json.dumps(evaluate_packet(repo / "tests/fixtures/legal-ocr/manifest.json", repo)["summary"], ensure_ascii=False, sort_keys=True))
PY
# status=passed, tool_count=16, decision=보류, failure_probe=unknown_tool, issues=[]
```

Focused security probe result:

```json
{"auth_context_required": true, "non_execution_boundary": true, "path_escape_rejected": true, "redaction_probe": "passed", "source_refs_pointer_only": true, "token_echo": false}
```

## Checked Artifact Paths

- `trustgraph_legal/mcp_domain.py`
- `trustgraph_legal/pii.py`
- `trustgraph_legal/classifier.py`
- `trustgraph_legal/fields.py`
- `trustgraph_legal/case_graph.py`
- `trustgraph_legal/stop_gates.py`
- `trustgraph_legal/stopgate_types.py`
- `trustgraph_legal/governance.py`
- `trustgraph_legal/governance_models.py`
- `trustgraph_legal/governance_records.py`
- `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py`
- `trustgraph-mcp/trustgraph/mcp_server/mcp.py`
- `trustgraph-mcp/trustgraph/mcp_server/tg_socket.py`
- `scripts/legal_ontology/evaluate_packet.py`
- `tests/unit/legal_ontology/test_mcp_domain_tools.py`
- `tests/integration/legal_ontology/test_mcp_tools.py`
- `docs/product/debt-collection-ontology/domain-contract.md`
- `docs/product/debt-collection-ontology/mcp-domain-server-contract.md`
- `resources/legal_rules/debt_collection_stopgate_v0.json`
- `.omo/evidence/debt-collection-ontology/*`
- `.omo/teams/debt-collection-ontology-todo-9-20260630/artifacts/*`

## Evidence Gaps

- No evidence shows gateway-backed validation/scoping for debt-collection domain tool calls. Current code only proves token presence.
- The prior F2 code-quality artifact does not explicitly document the required remove-ai-slops/overfit-slop review lens. Direct review found the privacy blocker in the integration test despite prior scan claims.
- The final context artifact already reports bookkeeping staleness in the plan/ledger trail; this review did not treat that as the main security blocker, but it remains an approval evidence gap.

## Final Status

FAIL. Do not approve until B1 and B2 are fixed and re-verified.
