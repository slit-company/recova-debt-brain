# Final Goal-Compliance Re-Review

Date: 2026-06-30

## recommendation

FAIL

## blockers

1. Gateway-backed scoped MCP is not satisfied: the current implementation validates bearer tokens through gateway `whoami`, then derives debt-collection tool scopes locally from roles returned by `whoami`. TrustGraph's IAM contract documents `whoami` as an authenticated self-read with no capability check, and documents `authorise()` as the capability decision API. The requested scoped-MCP property therefore is not backed by the gateway authorization contract.
   - `trustgraph-mcp/trustgraph/mcp_server/auth.py:21` opens a gateway socket and calls `manager.whoami()`.
   - `trustgraph-mcp/trustgraph/mcp_server/auth.py:40` creates the MCP `AccessToken` using `_legal_scopes_from_identity(identity)`.
   - `trustgraph-mcp/trustgraph/mcp_server/auth.py:83` maps `reader`, `writer`, and `admin` roles to local debt-tool scopes.
   - `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py:87` enforces the locally assigned scope before invoking the local handler.
   - `trustgraph-mcp/trustgraph/mcp_server/tg_socket.py:91` implements `whoami()` as an IAM `whoami` request.
   - `trustgraph-base/trustgraph/base/iam_client.py:54` states `whoami` is `AUTHENTICATED-only` with no capability check.
   - `trustgraph-flow/trustgraph/gateway/registry.py:399` registers `whoami` with `capability=AUTHENTICATED`.

2. The final scoped MCP smoke is overfit to the local role-mapping implementation rather than the requested security property.
   - `.omo/evidence/debt-collection-ontology/final-mcp-scope-smoke.txt` uses a fake gateway that maps `reader-token` to role `reader` via `whoami`.
   - That proves local role-to-scope mapping and reader governance rejection, but it does not prove the gateway/IAM regime denied `governance:review` or authorized `read:tools` via an `authorise()` decision.
   - No artifact proves that `whoami` returns authoritative per-tool debt-collection capabilities/scopes.

3. The code-quality/slop evidence is incomplete under the required final-gate criteria.
   - I loaded and directly applied the `omo:remove-ai-slops` and `omo:programming` lenses.
   - `.omo/evidence/debt-collection-ontology/f2-code-quality.md` now mentions programming/slop review and refactors, but it does not explicitly cover the overfit/slop criterion for the scoped MCP smoke.
   - The direct slop pass found the scoped-smoke evidence mirrors implementation internals and creates false confidence for a gateway-backed authorization claim.

## originalIntent

Deliver a TrustGraph debt-collection ontology/domain brain with a v0 ontology config, OCR markdown ingest lane, document registry, case graph, deterministic StopGate checks, governance/reprocess paths, and a single agent-agnostic MCP domain surface. The result must be source-grounded, gateway-backed and scoped, Hermes-agnostic, non-executing, not dependent on client-native memory as legal source of truth, and safe for sensitive legal data.

## desiredOutcome

An MCP-capable external agent should be able to call one TrustGraph MCP domain brain and receive redacted, source-backed case structure, StopGate status, governance state, and non-executing recommendations. Tool access must be scoped through the TrustGraph gateway/IAM authorization model, not merely through local role mapping after authentication.

## userOutcomeReview

The current working tree satisfies several important requirements:

- `recova-debt-collection` ontology, domain contracts, rule sources, classifier/field extraction, case graph, StopGate, governance, and MCP facade files are present.
- Unit tests passed: `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology -q` -> 39 passed.
- Integration MCP tests passed: `/opt/homebrew/bin/python3 -m pytest tests/integration/legal_ontology/test_mcp_tools.py -q` -> 3 passed.
- Packet evaluation passed to `/tmp`: status `passed`, `tool_count=16`, decision `보류`, recommendation `hold_for_review`, direct execution probe `unknown_tool`.
- Compile check over the changed legal/MCP/evaluator files passed.
- Non-execution is represented in code: `recommend_next_action` returns `no_direct_filing_contact_or_collection=True`, while the direct filing probe is an unknown tool.
- No Hermes runtime coupling was found in the changed TrustGraph legal/MCP surfaces.
- Contract docs state native memory must not override MCP source refs/rule refs.
- Governance and reprocess service paths exist through `promote_ontology_candidate`, `review_extracted_fact`, and `reprocess_case`.

The user-visible outcome still fails because the highest-risk criterion, gateway-backed scoped MCP authorization, is unsupported. Current evidence shows a fake gateway `whoami` role mapped to local scopes, not a TrustGraph gateway/IAM authorization decision for each requested debt-tool scope.

## checked artifact paths

- `.omo/plans/debt-collection-ontology.md`
- `.omo/evidence/debt-collection-ontology/f1-plan-compliance.md`
- `.omo/evidence/debt-collection-ontology/f2-code-quality.md`
- `.omo/evidence/debt-collection-ontology/f3-real-qa.txt`
- `.omo/evidence/debt-collection-ontology/f4-scope-fidelity.md`
- `.omo/evidence/debt-collection-ontology/final-mcp-scope-smoke.txt`
- `.omo/evidence/debt-collection-ontology/final-mcp-smoke.txt`
- `.omo/evidence/debt-collection-ontology/final-mcp-smoke.json`
- `.omo/evidence/debt-collection-ontology/final-review-security-final.md`
- `.omo/evidence/debt-collection-ontology/final-review-code-rerun.md`
- `.omo/evidence/debt-collection-ontology/final-review-goal-rerun.md`
- `docs/product/debt-collection-ontology/domain-contract.md`
- `docs/product/debt-collection-ontology/mcp-domain-server-contract.md`
- `scripts/legal_ontology/evaluate_packet.py`
- `tests/unit/legal_ontology/test_mcp_domain_tools.py`
- `tests/integration/legal_ontology/test_mcp_tools.py`
- `trustgraph_legal/mcp_domain.py`
- `trustgraph_legal/mcp_handlers.py`
- `trustgraph_legal/mcp_envelope.py`
- `trustgraph_legal/mcp_inputs.py`
- `trustgraph_legal/ingest.py`
- `trustgraph-mcp/trustgraph/mcp_server/auth.py`
- `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py`
- `trustgraph-mcp/trustgraph/mcp_server/mcp.py`
- `trustgraph-mcp/trustgraph/mcp_server/tg_socket.py`
- `trustgraph-base/trustgraph/base/iam_client.py`
- `trustgraph-flow/trustgraph/gateway/registry.py`
- `trustgraph-flow/trustgraph/iam/service/iam.py`

## exact evidence gaps

- No current code path calls gateway/IAM `authorise()` for `read:tools`, `ingest:documents`, `graph:case`, `stopgate:check`, `governance:review`, or `governance:reprocess` before the debt-tool handler runs.
- No current artifact documents or proves that `whoami` returns authoritative per-tool debt-collection capabilities/scopes.
- The final scoped MCP smoke models authorization as fake-gateway role data returned from `whoami`, not as gateway/IAM allow/deny decisions.
- The F2 code-quality evidence does not explicitly cover the required overfit/slop criterion for this scoped-MCP evidence shape.
- The MCP contract document still contains a stale registration snippet using `_require_token`, while current code registers with `require_token`.

## final status

FAIL
