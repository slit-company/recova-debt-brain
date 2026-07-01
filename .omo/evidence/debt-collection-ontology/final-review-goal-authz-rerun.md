# Final Gate Re-review - Debt Collection Ontology Authz Rerun

Date: 2026-07-01
Workspace: `/Users/cosmos/dev/ontology/trustgraph`

## recommendation

APPROVE

## blockers

None.

## originalIntent

Build the TrustGraph v0 debt-collection ontology/domain brain: a `recova-debt-collection` ontology, OCR markdown ingest and registry path, document classifier/field extraction, hybrid case graph, deterministic StopGate/rule governance, and one agent-agnostic MCP domain server that external MCP clients can call for redacted, source-backed legal workflow state. The server must not become a SaaS UI, Hermes-specific runtime, native-agent-memory legal source, live statute crawler, or direct filing/contact/payment/collection executor.

The specific rerun issue was the earlier authz blocker: the prior smoke incorrectly treated public websocket `iam/authorise-many` as a real TrustGraph route. The fixed target is: gateway websocket validates bearer token/identity via `whoami`; public websocket `iam/authorise-many` is not used; production debt-tool scope decisions use internal `IamClient.authorise_many`; scoped smoke proves the internal authorizer seam and reader governance denial.

## desiredOutcome

An MCP-compatible external agent can call the single TrustGraph MCP domain brain and receive redacted, source-backed case graph, StopGate, governance, and non-executing next-action responses. Tool access is scoped through gateway-verified identity plus IAM-backed scope decisions, without leaking bearer tokens or raw legal PII and without executing irreversible legal/business actions.

## userOutcomeReview

The requested v0 product spine is genuinely present enough to close F1-F4.

- Ontology/config spine is present: `resources/ontologies/recova-debt-collection.json` validates as `classes=36 objectProperties=41 datatypeProperties=44`.
- Continuous ingest path is present: `trustgraph_legal/ingest.py:107-151` calls the TrustGraph `load_text` lane with registry metadata and no raw text in the summary; `tests/unit/legal_ontology/test_ingest.py:75-110` covers the non-dry-run lane and duplicate skip behavior.
- Document classifier/fields are present: classifier rules produce confidence, review status, source spans, and redaction; field/case suites pass in the full unit run.
- Case graph/identity/provenance are present: `trustgraph_legal/case_graph.py` builds `case_packet_id`, hybrid evidence keys, documents, source spans, parties, claims, titles, attachment/asset/ledger facts, and identity review findings.
- StopGate/governance are present: approved curated rule source has 12 rules; StopGate tests cover missing execution clause, assignment chain, discharge/insolvency, limitation, exemption, amount mismatch, identity uncertainty, missing provenance, and unapproved rule-source blocking.
- MCP domain tools are present: `trustgraph_legal/mcp_domain.py:21-39` defines the 16-tool scope matrix, and `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py:39-59` registers the tools into the existing physical MCP server.
- Authorization/redaction are now aligned with real TrustGraph: `GatewayTokenVerifier` uses websocket `whoami` only for identity (`auth.py:35-45`), then delegates scope decisions to `scope_authorizer`; production default is `IamScopeAuthorizer` (`mcp.py:296-297`), whose implementation calls internal `IamClient.authorise_many` (`auth.py:65-88`). The public gateway registry explicitly excludes `authorise-many`, and the current code no longer sends it over `WebSocketManager.request`.
- Real-surface evidence is adequate for this rerun: the retained streamable HTTP smoke proves MCP server startup, bad token rejection, good token acceptance, debt-tool listing/call, and token non-echo; the scoped rerun proves `internal_scope_authorizer_used=True`, `public_authorise_many_used=False`, and reader governance rejection.

Older `final-review-*` artifacts are contradictory and stale: several describe the pre-fix role-mapping or public-websocket `authorise-many` implementation. I did not treat those stale reports as authoritative. Current source, current tests, `f2-code-quality.md`, `final-mcp-scope-smoke.txt`, and the verification rerun are authoritative for this gate.

## F1-F4 closure

- F1 Plan compliance: ACCEPT. Every Must Have in `.omo/plans/debt-collection-ontology.md` has a source/evidence path, and the Must NOT boundaries remain represented in code and tests.
- F2 Code quality: ACCEPT. The requested tests, evaluator, ontology validator, py_compile, and diff checks pass. My direct `remove-ai-slops` / `programming` pass found residual cleanup debt but no unresolved blocker, no deletion-only tests, no tautological removal tests, and no overfit auth smoke after the authorise-many fix.
- F3 Real manual QA: ACCEPT. The HTTP MCP smoke reaches the streamable MCP surface; the scoped smoke directly targets the previous authz failure class and verifies the corrected internal-authorizer behavior.
- F4 Scope fidelity: ACCEPT. No Hermes coupling, user-facing UX, auto filing/contact/payment/collection execution, unversioned legal memory, live statute auto-promotion, or multiple physical MCP services were found in the reviewed surface.

## verificationCommands

- `python3 scripts/legal_ontology/evaluate_packet.py --fixtures tests/fixtures/legal-ocr/manifest.json --out /tmp/final-review-task10-eval-gate-rerun.json`
  - Passed: `status=passed`, `tool_count=16`, `decision=보류`, `recommendation=hold_for_review`, `failure_probe=unknown_tool`, `issues=[]`.
- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology -q`
  - Passed: `41 passed in 1.43s`.
- `/opt/homebrew/bin/python3 -m pytest tests/integration/legal_ontology/test_mcp_tools.py -q`
  - Passed: `3 passed in 2.20s`.
- `python3 scripts/legal_ontology/validate_ontology.py resources/ontologies/recova-debt-collection.json`
  - Passed: `PASS ontology recova-debt-collection classes=36 objectProperties=41 datatypeProperties=44`.
- `git diff --check && git diff --check origin/master...HEAD`
  - Passed.
- `PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m py_compile ...`
  - Passed over reviewed legal/MCP/evaluator/test files.

## remove-ai-slops / programming pass

I loaded and applied `omo:remove-ai-slops` and `omo:programming` before approving. Direct pass result:

- No unresolved excessive/false-confidence tests for the auth fix. `tests/unit/legal_ontology/test_mcp_auth_boundary.py:17-58` proves `GatewayTokenVerifier` does not call public websocket IAM scope authorization, and `test_mcp_auth_boundary.py:61-115` proves `IamScopeAuthorizer` uses internal `authorise_many`.
- No deletion-only or mere requested-removal tests found in the focused auth/MCP tests.
- No unnecessary production extraction/parsing/normalization introduced for the auth fix. The split modules mostly reduce prior oversized classifier/MCP-domain files.
- Residual debt remains but is not a blocker for F1-F4: `trustgraph-mcp/trustgraph/mcp_server/mcp.py` is a pre-existing 1571 pure-LOC monolith; `tests/integration/legal_ontology/test_mcp_tools.py` is 279 pure LOC; auth boundary glue uses `Any` and cleanup catch blocks. These are maintenance targets, not completion blockers for the current objective.

The code-quality evidence also explicitly records the same skill perspective in `.omo/evidence/debt-collection-ontology/f2-code-quality.md`, including the post-auth-review smoke update away from fake public `authorise-many`.

## checkedArtifactPaths

- `.omo/plans/debt-collection-ontology.md`
- `.omo/evidence/debt-collection-ontology/f1-plan-compliance.md`
- `.omo/evidence/debt-collection-ontology/f2-code-quality.md`
- `.omo/evidence/debt-collection-ontology/f3-real-qa.txt`
- `.omo/evidence/debt-collection-ontology/f4-scope-fidelity.md`
- `.omo/evidence/debt-collection-ontology/final-mcp-scope-smoke.txt`
- `.omo/evidence/debt-collection-ontology/final-verification-20260701.txt`
- `.omo/evidence/debt-collection-ontology/final-mcp-smoke.txt`
- `.omo/evidence/debt-collection-ontology/final-mcp-smoke.json`
- `.omo/evidence/debt-collection-ontology/final-cleanup.txt`
- `.omo/evidence/debt-collection-ontology/final-ulw-notepad.md`
- `docs/product/debt-collection-ontology/domain-contract.md`
- `docs/product/debt-collection-ontology/mcp-domain-server-contract.md`
- `resources/ontologies/recova-debt-collection.json`
- `resources/legal_rules/debt_collection_stopgate_v0.json`
- `tests/fixtures/legal-ocr/manifest.json`
- `scripts/legal_ontology/evaluate_packet.py`
- `trustgraph_legal/ingest.py`
- `trustgraph_legal/classifier.py`
- `trustgraph_legal/classifier_rules.py`
- `trustgraph_legal/classifier_types.py`
- `trustgraph_legal/case_graph.py`
- `trustgraph_legal/stop_gates.py`
- `trustgraph_legal/governance.py`
- `trustgraph_legal/mcp_domain.py`
- `trustgraph_legal/mcp_handlers.py`
- `trustgraph_legal/mcp_envelope.py`
- `trustgraph_legal/mcp_inputs.py`
- `trustgraph-mcp/trustgraph/mcp_server/auth.py`
- `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py`
- `trustgraph-mcp/trustgraph/mcp_server/mcp.py`
- `trustgraph-mcp/trustgraph/mcp_server/tg_socket.py`
- `trustgraph-base/trustgraph/base/iam_client.py`
- `trustgraph-flow/trustgraph/gateway/registry.py`
- `trustgraph-flow/trustgraph/gateway/dispatch/mux.py`
- `tests/unit/legal_ontology/test_mcp_auth_boundary.py`
- `tests/unit/legal_ontology/test_mcp_domain_tools.py`
- `tests/integration/legal_ontology/test_mcp_tools.py`
- `tests/unit/legal_ontology/test_ingest.py`
- `tests/unit/legal_ontology/test_stop_gates.py`
- `tests/unit/legal_ontology/test_ontology_governance.py`

## exactEvidenceGaps

No acceptance-blocking evidence gaps remain.

Residual non-blocking gaps/risks:

- The scoped MCP smoke uses an injected internal `scope_authorizer` seam rather than a live Pulsar/RabbitMQ/Kafka-backed IAM service. Source and unit tests prove production wires that seam to `IamClient.authorise_many`, but a full deployment smoke with a real IAM pub/sub backend was not run in this workspace.
- Several stale review artifacts still report old blockers from earlier code states. They should not be used as current truth; the current source/tests/evidence supersede them.
- Style debt remains in the broader MCP monolith and a few boundary typing/cleanup patterns, but the direct slop pass found no unresolved blocker for the user's v0 product outcome.

VERDICT: ACCEPT
