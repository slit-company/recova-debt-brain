# Final Code Quality / Slop Re-review

Date: 2026-06-30

## Verdict

PASS with WATCH.

codeQualityStatus: WATCH
recommendation: APPROVE
reportPath: `.omo/evidence/debt-collection-ontology/final-review-code-final.md`

## Inputs / Scope

Reviewed the current working tree in `/Users/cosmos/dev/ontology/trustgraph` and the cited evidence at `.omo/evidence/debt-collection-ontology/f2-code-quality.md`.

The user request did not provide a notepad path, so no notepad artifact was inspected. Current tree evidence was treated as authoritative over stale prior review markdown.

Important files reviewed:

- `trustgraph_legal/classifier.py`
- `trustgraph_legal/classifier_types.py`
- `trustgraph_legal/classifier_rules.py`
- `trustgraph_legal/classifier_manifest.py`
- `trustgraph_legal/mcp_domain.py`
- `trustgraph_legal/mcp_handlers.py`
- `trustgraph_legal/mcp_envelope.py`
- `trustgraph_legal/mcp_inputs.py`
- `trustgraph-mcp/trustgraph/mcp_server/auth.py`
- `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py`
- `trustgraph-mcp/trustgraph/mcp_server/mcp.py`
- `tests/unit/legal_ontology/*`
- `tests/integration/legal_ontology/test_mcp_tools.py`

## Skill Perspective Check

Ran the required skill-perspective check before judging tests and maintainability:

- Loaded and applied `omo:remove-ai-slops`.
- Loaded and applied `omo:programming`.
- Loaded the Python programming reference `references/python/README.md`.
- Ran the programming no-excuse checker over the changed/reviewed Python files.

Result:

- `remove-ai-slops` perspective: no CRITICAL/HIGH slop remains in the refactored debt-collection production modules. No deletion-only tests, tautological removal tests, or implementation-constant-only tests were found in the final focused diff.
- `programming` perspective: the diff still has non-blocking violations: new extracted dataclasses omit `slots=True`, `auth.py` has a cleanup `except Exception: pass`, adapter/runtime code still uses `Any` at external boundaries, and the pre-existing `mcp.py` monolith remains oversized. These are listed below as MEDIUM/LOW, not blockers for this final pass because the specific prior production-size blockers are resolved and the remaining `mcp.py` auth change is narrow/extractive.

## Findings

### CRITICAL

None.

### HIGH

None.

### MEDIUM

1. `auth.py` still owns local role-to-legal-scope policy rather than proving gateway/IAM capability authorization per debt-collection tool.

`trustgraph-mcp/trustgraph/mcp_server/auth.py:83-98` maps gateway `whoami` roles into debt-tool scopes locally. `trustgraph-flow/trustgraph/gateway/registry.py:398-404` registers `whoami` as `AUTHENTICATED`, and `trustgraph-flow/trustgraph/iam/service/iam.py:513-517` documents that every authenticated user can read themselves. The current fake-gateway smoke proves the local reader-vs-governance split, but not a real IAM per-tool capability check.

This is not a final code-quality blocker because the previous blanket `LEGAL_MCP_GATEWAY_SCOPE` grant has been narrowed and the auth implementation has moved out of `mcp.py`. It remains a security/design evidence gap if the final product claim is that the gateway is the source of truth for debt-tool permissions.

2. Strict Python dataclass hygiene is still incomplete in new/extracted modules.

The no-excuse checker flagged missing `slots=True` on new frozen dataclasses, including `trustgraph_legal/classifier_types.py:70`, `trustgraph_legal/classifier_types.py:88`, `trustgraph_legal/classifier_types.py:120`, `trustgraph_legal/classifier_types.py:141`, `trustgraph_legal/classifier_types.py:149`, `trustgraph_legal/classifier_types.py:155`, `trustgraph_legal/mcp_domain.py:42`, `trustgraph_legal/mcp_envelope.py:14`, and `trustgraph_legal/ingest.py:33`.

This is mechanical cleanup debt, not a behavior blocker.

3. `auth.py` has a silent cleanup catch.

`trustgraph-mcp/trustgraph/mcp_server/auth.py:34-38` suppresses `manager.stop()` failures during token verification cleanup. The comment explains the intent, but the slop lens still prefers logging or a narrowly handled cleanup exception. Impact is limited to cleanup observability/resource leak risk, not token acceptance.

### LOW

1. The pre-existing `trustgraph-mcp/trustgraph/mcp_server/mcp.py` remains far over the 250 pure-LOC programming ceiling.

Current measurement: 1550 pure LOC. The final diff no longer keeps the debt auth verifier class in this monolith: `mcp.py` now imports `GatewayTokenVerifier` / `require_token` at `trustgraph-mcp/trustgraph/mcp_server/mcp.py:20`, registers debt tools at `trustgraph-mcp/trustgraph/mcp_server/mcp.py:344-347`, and passes `auth_context.token` in `_get_manager()` at `trustgraph-mcp/trustgraph/mcp_server/mcp.py:359-360`. This is acceptable for the requested final gate, but the file remains a standing refactor target.

2. The focused integration test file is slightly oversized.

`tests/integration/legal_ontology/test_mcp_tools.py` measures 279 pure LOC. It covers real contract boundaries, redaction, source refs, and adapter auth behavior, so it is not useless coverage, but it should be split if more MCP scenarios are added.

3. Boundary `Any` remains in the FastMCP/legal adapter surfaces.

Examples: `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py:4-8`, `trustgraph-mcp/trustgraph/mcp_server/auth.py:68`, `trustgraph-mcp/trustgraph/mcp_server/auth.py:83`, and `trustgraph_legal/ingest.py:21-29`. Some of this is justified by the FastMCP/Pydantic schema workaround documented in `f2-code-quality.md`; the rest is acceptable as boundary glue for this pass but should not spread into domain logic.

## Prior Blocker Re-check

- Oversized `trustgraph_legal/classifier.py`: PASS. Now 89 pure LOC.
- Oversized `trustgraph_legal/mcp_domain.py`: PASS. Now 155 pure LOC.
- Extracted classifier modules: PASS. `classifier_types.py` 137, `classifier_rules.py` 203, `classifier_manifest.py` 56 pure LOC.
- Extracted MCP domain modules: PASS. `mcp_handlers.py` 182, `mcp_envelope.py` 80, `mcp_inputs.py` 46 pure LOC.
- Auth logic inside giant `mcp.py`: PASS for code-quality scope. The verifier and token resolver now live in `trustgraph-mcp/trustgraph/mcp_server/auth.py`; `mcp.py` keeps only wiring.
- Old `_get_manager()` `AuthContext` regression: PASS. Current `trustgraph-mcp/trustgraph/mcp_server/mcp.py:359-360` passes `auth_context.token`.
- Old nested `source_refs` object leakage: PASS. Current adversarial probe returned `["document_id=doc-1|chunk_id=chunk-1"]` with no raw PII leak.

## Verification

Commands rerun in this review:

```text
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m pytest -p no:cacheprovider tests/unit/legal_ontology -q
Result: 39 passed.

PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m pytest -p no:cacheprovider tests/integration/legal_ontology/test_mcp_tools.py -q
Result: 3 passed.

PYTHONDONTWRITEBYTECODE=1 python3 <AST parse probe over 17 changed/reviewed Python files>
Result: AST_PARSE_OK files=17.

git diff --check
Result: passed.

PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 scripts/legal_ontology/evaluate_packet.py --fixtures tests/fixtures/legal-ocr/manifest.json --out /tmp/final-review-code-final-eval.json
Result: {"status":"passed","tool_count":16,"decision":"보류","recommendation":"hold_for_review","failure_probe":"unknown_tool","issues":[]}
```

Additional probes:

```text
reader_governance_rejected=true
global_scope_governance_allowed=true
source_refs_pointer_only=true
source_refs_pii_leak=false
```

Programming no-excuse scan:

```text
Result: failed with strict-style violations.
Blocking interpretation: no CRITICAL/HIGH final blockers for the requested prior blockers; violations are recorded above as MEDIUM/LOW residual debt.
```

## Blockers

None for code-quality approval.

## Final Status

PASS with WATCH. The prior code-quality/slop blockers are resolved enough for approval, with residual cleanup debt around strict Python hygiene and the broader authorization contract evidence.
