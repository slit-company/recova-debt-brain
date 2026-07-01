# Final Goal Compliance Re-Review

Date: 2026-06-30

## recommendation

FAIL

## originalIntent

Deliver a TrustGraph debt-collection ontology/domain brain: v0 TrustGraph ontology config, OCR markdown ingest, document registry, case graph, deterministic StopGate checks, governance/review queues, and a single agent-agnostic MCP domain surface with scoped tools. The implementation must not leak raw sensitive identifiers, couple to Hermes, execute filings/contact/collection/payment actions, bypass TrustGraph provenance/source refs, or rely on a client agent's native memory as legal source of truth.

## desiredOutcome

An MCP-capable external agent can safely call a single TrustGraph MCP domain brain for source-grounded case structure, legal prerequisites, StopGate status, governance state, and non-executing next-action recommendations. The shipped artifacts should support every Must Have and Must NOT in `.omo/plans/debt-collection-ontology.md`, with trustworthy verification and code-quality evidence.

## userOutcomeReview

The current working tree fixes several prior failures: raw sensitive test literals are no longer present in the previously offending MCP tests, debt-collection adapter calls now require a structured `AuthContext`, a `trustgraph_legal.ingest.load_registry_records_to_trustgraph()` text-load lane exists and is unit-tested, non-execution behavior still evaluates cleanly, no Hermes coupling was found, and source refs/provenance are broadly present.

The re-review still cannot pass. The B1 security fix validates tokens through gateway `whoami`, but then grants the blanket legal MCP scope locally to every gateway-authenticated token. It does not ask the gateway/IAM regime for the requested debt-collection tool capability/scope. That leaves tool group/scope enforcement under-supported for governance/admin-class tools. The code-quality evidence also still lacks the required remove-ai-slops/programming coverage, and the direct slop pass found unresolved maintenance defects in branch/touched source.

## blockers

1. B1 remains functionally incomplete: gateway authentication is not gateway authorization.
   - `trustgraph-mcp/trustgraph/mcp_server/mcp.py:72-95` opens a gateway WebSocket, calls `whoami`, then returns `AccessToken(..., scopes=[LEGAL_MCP_GATEWAY_SCOPE])`.
   - `trustgraph-flow/trustgraph/gateway/registry.py:398-404` registers `whoami` as `AUTHENTICATED`.
   - `trustgraph-flow/trustgraph/iam/service/iam.py:513-517` documents that every authenticated user can read themselves via `whoami`; it is not a capability check.
   - `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py:108-113` allows any tool when `LEGAL_MCP_GATEWAY_SCOPE` is present.
   - Direct probe of the adapter showed `global_legal_scope` accepts `promote_ontology_candidate` (`governance:review`), while `read:tools` is rejected. Because `GatewayTokenVerifier` assigns the global legal scope after `whoami`, any gateway-authenticated token receives all debt-collection scopes locally.

2. Required slop/programming review coverage is still missing and direct pass found unresolved issues.
   - `.omo/evidence/debt-collection-ontology/f2-code-quality.md:9-57` records tests, py_compile, privacy scan, and security smoke, but does not document `omo:remove-ai-slops` overfit/slop coverage or the `omo:programming` criteria.
   - Pure LOC direct pass over changed/touched Python files found `trustgraph_legal/mcp_domain.py` at 387 pure LOC with no `SIZE_OK` exception, and touched `trustgraph-mcp/trustgraph/mcp_server/mcp.py` at 1620 pure LOC.
   - New/touched code also contains broad exception handling in `trustgraph-mcp/trustgraph/mcp_server/mcp.py:79-89` and untyped `Any` in the new ingest/adapter surfaces. These are maintenance/false-confidence risks under the loaded criteria.

## evidence

Passing evidence from this re-review:

- `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m pytest -p no:cacheprovider tests/unit/legal_ontology -q` -> 37 passed.
- `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m pytest -p no:cacheprovider tests/integration/legal_ontology/test_mcp_tools.py -q` -> 3 passed.
- Focused rerun of `tests/unit/legal_ontology/test_ingest.py tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py` -> 11 passed.
- `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m py_compile scripts/legal_ontology/evaluate_packet.py trustgraph_legal/ingest.py trustgraph-mcp/trustgraph/mcp_server/legal_tools.py trustgraph-mcp/trustgraph/mcp_server/mcp.py` -> passed.
- `git diff --check` -> passed.
- Direct `evaluate_packet()` call -> `{"status":"passed","tool_count":16,"decision":"보류","recommendation":"hold_for_review","failure_probe":"unknown_tool","issues":[]}`.
- Sensitive-shape scan over the MCP tests and final evidence markdown/text returned no national-ID, phone, or bank-account-shaped hits.

Prior-blocker status:

- B2 sensitive literals: PASS for current tested files. `tests/integration/legal_ontology/test_mcp_tools.py` now constructs sensitive values from fragments, and the scan returned no hits.
- TrustGraph text-load ingest lane: PARTIAL PASS. `trustgraph_legal/ingest.py:107-151` adds a non-dry-run `load_registry_records_to_trustgraph()` helper that calls `flow.load_text(...)`; `tests/unit/legal_ontology/test_ingest.py:73-137` covers one load call, duplicate skip, metadata, and no raw text in summary. The CLI and MCP ingest surfaces still remain dry-run/not-configured (`trustgraph_legal/ingest.py:59-104`, `trustgraph_legal/mcp_domain.py:190-204`, `:228-234`), but this re-review does not treat that as the primary blocker because the requested module-level text-load lane exists.
- Final bookkeeping: NOT A BLOCKER for this rerun by user instruction. F1-F4 remain unchecked in `.omo/plans/debt-collection-ontology.md`, but the user explicitly said not to fail solely because F1-F4 are not checked if this re-review is part of closing them.
- Non-execution boundary: PASS. `recommend_next_action` returns `no_direct_filing_contact_or_collection=true`, and `evaluate_packet()` still sees `execute_direct_collection_filing` as `unknown_tool`.
- No Hermes coupling: PASS. No Hermes-specific code/runtime dependency was found in the changed domain/MCP surfaces; docs describe the server as Hermes-agnostic.
- Provenance/source refs: PASS with residual normal risk. Registry records, case graph, StopGate payloads, and MCP envelopes include `document_id`, `source_hash`, `source_ref`/`source_refs`, `case_packet_id`, and pointer-only source refs in the reviewed paths.

## checkedArtifactPaths

- `.omo/plans/debt-collection-ontology.md`
- `.omo/evidence/debt-collection-ontology/f1-plan-compliance.md`
- `.omo/evidence/debt-collection-ontology/f2-code-quality.md`
- `.omo/evidence/debt-collection-ontology/f3-real-qa.txt`
- `.omo/evidence/debt-collection-ontology/f4-scope-fidelity.md`
- `.omo/evidence/debt-collection-ontology/final-review-goal.md`
- `.omo/evidence/debt-collection-ontology/final-review-security.md`
- `git diff origin/master...HEAD`
- `git diff`
- `docs/product/debt-collection-ontology/domain-contract.md`
- `docs/product/debt-collection-ontology/mcp-domain-server-contract.md`
- `trustgraph_legal/ingest.py`
- `trustgraph_legal/mcp_domain.py`
- `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py`
- `trustgraph-mcp/trustgraph/mcp_server/mcp.py`
- `trustgraph-flow/trustgraph/gateway/registry.py`
- `trustgraph-flow/trustgraph/iam/service/iam.py`
- `tests/unit/legal_ontology/test_ingest.py`
- `tests/unit/legal_ontology/test_mcp_domain_tools.py`
- `tests/integration/legal_ontology/test_mcp_tools.py`
- `scripts/legal_ontology/evaluate_packet.py`

## exactEvidenceGaps

- No current artifact proves the debt-collection tool's requested `scope`/capability is authorized by the TrustGraph gateway/IAM regime before local handler execution.
- Current code proves gateway authentication through `whoami`, but `whoami` is only an authenticated self-read and the MCP verifier locally grants `trustgraph-legal:mcp-domain` afterward.
- No current code-quality/review artifact explicitly covers the required remove-ai-slops overfit/slop pass or programming-rule criteria.
- No acceptable exception or refactor evidence exists for newly added `trustgraph_legal/mcp_domain.py` exceeding the 250 pure-LOC threshold, and the branch still edits the 1620 pure-LOC MCP server file.

## final

FAIL
