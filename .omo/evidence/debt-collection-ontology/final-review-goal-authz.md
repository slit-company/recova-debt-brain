# Final Gate Review - Debt Collection Ontology Authz

Date: 2026-07-01

## recommendation

REJECT

## originalIntent

Build the TrustGraph debt-collection ontology brain at v0: ontology config, OCR/ongoing ingest path, document registry, deterministic classification and field extraction, case graph, StopGate/governance workflows, and a single agent-agnostic MCP domain server that Hermes or any MCP client can attach to. The final slice specifically had to close the MCP domain server and authorization boundary.

## desiredOutcome

An MCP client can call the single TrustGraph MCP domain brain and get redacted, source-backed case graph, StopGate, governance, and advisory next-action results. Debt-collection tool access must be scoped through the real TrustGraph gateway/IAM authorization contract, not through an overfit fake gateway or local-only role/scoping behavior.

## userOutcomeReview

The v0 product spine is mostly present: ontology/rule resources exist, evaluator passes, unit/integration suites pass, MCP tools expose 16 domain contracts, recommendations remain non-executing, and outputs are redacted/source-backed in the reviewed fixtures.

The user-visible outcome still cannot be accepted because the highest-risk final slice, real gateway-backed MCP authorization, is not actually satisfied. The current `GatewayTokenVerifier` sends `operation: "authorise-many"` through `WebSocketManager.request("iam", ...)`, but the real gateway registry explicitly excludes `authorise`, `authorise-many`, and `get-signing-key-public` from the public API. The websocket mux looks up IAM operations in that registry and returns `unknown-service` when absent. Therefore a real gateway can reject valid MCP tokens during verification, while the retained scoped smoke passes only because its fake gateway implements an internal-only operation.

## blockers

1. Real gateway IAM `authorise-many` is not dispatchable through the implemented MCP verifier path.
   - `trustgraph-mcp/trustgraph/mcp_server/auth.py:25-30` starts a gateway websocket, calls `whoami()`, then calls `_authorised_legal_scopes(...)`.
   - `trustgraph-mcp/trustgraph/mcp_server/auth.py:98-104` sends `{"operation": "authorise-many"}` through `manager.request("iam", ...)`.
   - `trustgraph-flow/trustgraph/gateway/registry.py:198-205` says `authorise` and `authorise-many` are internal and excluded from the public API.
   - `trustgraph-flow/trustgraph/gateway/registry.py:398-404` registers `whoami`, but not `authorise` or `authorise-many`.
   - `trustgraph-flow/trustgraph/gateway/dispatch/mux.py:145-159` looks up `service == "iam"` operations via registry and returns `unknown-service` if absent.
   - Direct proof command: direct file import of `registry.py` printed `whoami=True`, `authorise=False`, `authorise-many=False`.

2. The scoped MCP smoke is overfit to a fake gateway.
   - `.omo/evidence/debt-collection-ontology/final-mcp-scope-smoke.txt` contains the requested booleans: `bad_token_rejected=true`, `authorise_many_used=true`, `reader_governance_rejected=true`, `token_echo=false`, and cleanup.
   - That artifact does not prove the real TrustGraph gateway can route `iam/authorise-many`; source inspection shows it cannot through this path.
   - This is a `remove-ai-slops` false-confidence issue: the evidence mirrors the intended behavior of the new implementation rather than exercising the real production boundary.

3. The current tests do not cover the production verifier boundary.
   - `/opt/homebrew/bin/python3 -m pytest tests/integration/legal_ontology/test_mcp_tools.py -q` passes, but `tests/integration/legal_ontology/test_mcp_tools.py` tests the adapter with handcrafted `AuthContext` objects and does not drive `GatewayTokenVerifier` against the real gateway mux/registry contract.
   - A direct helper probe confirmed `_authorised_legal_scopes` asks for `authorise-many` and filters allowed scopes, but that only proves the helper’s local logic, not route availability.

## F1-F4 closure

- F1 Plan compliance: cannot close. The scoped MCP/domain-server Must Have is not met against the real gateway contract.
- F2 Code quality: cannot close. Required `remove-ai-slops`/`programming` pass finds false-confidence auth evidence and missing verifier-boundary coverage.
- F3 Real manual QA: cannot close. The final scoped smoke is not a real-surface proof for the actual TrustGraph gateway route.
- F4 Scope fidelity: cannot close. The implementation claims gateway/IAM authorization, but the current path depends on an internal operation unavailable on the public websocket dispatch surface.

## verificationCommands

- `python3 scripts/legal_ontology/evaluate_packet.py --fixtures tests/fixtures/legal-ocr/manifest.json --out /tmp/final-review-task10-eval-gate.json`
  - Passed: `status=passed`, `tool_count=16`, `decision=보류`, `recommendation=hold_for_review`, `failure_probe=unknown_tool`, `issues=[]`.
- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology -q`
  - Passed: `39 passed`.
- `/opt/homebrew/bin/python3 -m pytest tests/integration/legal_ontology/test_mcp_tools.py -q`
  - Passed: `3 passed`.
- `python3 scripts/legal_ontology/validate_ontology.py resources/ontologies/recova-debt-collection.json`
  - Passed: `classes=36 objectProperties=41 datatypeProperties=44`.
- `git diff --check`
  - Passed.
- Direct gateway registry proof:
  - Command: direct import of `trustgraph-flow/trustgraph/gateway/registry.py` and lookup of `whoami`, `authorise`, `authorise-many`.
  - Result: `whoami=True`, `authorise=False`, `authorise-many=False`.
- Direct verifier-helper probe:
  - Result: `_authorised_legal_scopes` sends `kind=iam`, `operation=authorise-many`, `check_count=10`, and filters governance scopes out when denied by the fake manager.
- No-excuse/slop scan:
  - Result: strict checker reports residual style/size issues; the blocking interpretation is the auth-boundary false-confidence coverage, not the pre-existing MCP monolith alone.

## checkedArtifactPaths

- `.omo/plans/debt-collection-ontology.md`
- `.omo/evidence/debt-collection-ontology/f1-plan-compliance.md`
- `.omo/evidence/debt-collection-ontology/f2-code-quality.md`
- `.omo/evidence/debt-collection-ontology/f3-real-qa.txt`
- `.omo/evidence/debt-collection-ontology/f4-scope-fidelity.md`
- `.omo/evidence/debt-collection-ontology/final-mcp-scope-smoke.txt`
- `.omo/evidence/debt-collection-ontology/final-mcp-smoke.json`
- `.omo/evidence/debt-collection-ontology/final-cleanup.txt`
- `.omo/evidence/debt-collection-ontology/final-review-code-authz.md`
- `.omo/evidence/debt-collection-ontology/final-review-security-authz.md`
- `.omo/evidence/debt-collection-ontology/final-verification-20260701.txt`
- `.omo/evidence/debt-collection-ontology/final-ulw-notepad.md`
- `trustgraph-mcp/trustgraph/mcp_server/auth.py`
- `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py`
- `trustgraph-mcp/trustgraph/mcp_server/mcp.py`
- `trustgraph-mcp/trustgraph/mcp_server/tg_socket.py`
- `trustgraph_legal/mcp_domain.py`
- `trustgraph_legal/mcp_handlers.py`
- `trustgraph_legal/mcp_envelope.py`
- `trustgraph_legal/mcp_inputs.py`
- `scripts/legal_ontology/evaluate_packet.py`
- `tests/unit/legal_ontology/test_mcp_domain_tools.py`
- `tests/integration/legal_ontology/test_mcp_tools.py`
- `trustgraph-flow/trustgraph/gateway/registry.py`
- `trustgraph-flow/trustgraph/gateway/dispatch/mux.py`
- `trustgraph-flow/trustgraph/gateway/endpoint/iam_endpoint.py`
- `trustgraph-flow/trustgraph/iam/service/iam.py`
- `resources/ontologies/recova-debt-collection.json`
- `resources/legal_rules/debt_collection_stopgate_v0.json`

## exactEvidenceGaps

- No current evidence proves `iam/authorise-many` is callable through the real TrustGraph websocket gateway route used by `GatewayTokenVerifier`.
- The final scoped smoke uses a fake gateway that implements the intended `authorise-many` behavior even though the real gateway registry excludes that operation from the public dispatch surface.
- The focused MCP integration tests do not exercise `GatewayTokenVerifier.verify_token()` or the gateway mux registry lookup for `authorise-many`.
- The F reports that mark scoped MCP authorization complete are unsupported by the real gateway source.

## finalStatus

REJECT. Do not close F1-F4 until the verifier uses a dispatchable gateway/IAM authorization path, or the gateway intentionally exposes a properly gated public `authorise-many` operation, and a real-surface smoke/test proves bad-token rejection, per-scope allow/deny, reader governance denial, token non-echo, and cleanup through that actual path.
