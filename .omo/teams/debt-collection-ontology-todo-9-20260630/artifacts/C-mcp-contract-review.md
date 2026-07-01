# Member C - Todo 9 MCP Contract Review

Reviewer: C / `mcp-contract-review`
Date: 2026-06-30
Scope: read-only acceptance, security boundary, scope matrix, schema/source_refs review

## Verdict

Todo 9 is not acceptance-ready yet because A/B Todo 9 implementation changes were not visible in my bound review snapshot: A, B, and C branches were all at the same base commit and A/B worktrees reported clean. This report therefore records the contract acceptance gate and post-implementation checks that must pass once A/B land code.

Current direction from A is compatible with the contract if implemented as described: domain logic in `trustgraph_legal.mcp_domain`, a thin MCP adapter at `trustgraph.mcp_server.legal_tools`, fake-MCP-testable registration, no execution actions, and a stable envelope containing `schema_version`, `tool_name`, `group`, `scope`, `pii_profile`, `source_refs`, `warnings`, and `result`.

## Isolation Evidence

Captured before review:

```text
pwd
/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debt-collection-ontology-todo-9-20260630/worktrees/C

git rev-parse --show-toplevel
/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debt-collection-ontology-todo-9-20260630/worktrees/C

git status --short --branch
## team/debt-collection-ontology-todo-9-20260630/C

git -C /Users/cosmos/dev/ontology/trustgraph status --short --branch
## master...origin/master [ahead 21]
?? .omo/
```

Read-only branch/worktree comparison:

- A worktree status: `## team/debt-collection-ontology-todo-9-20260630/A`
- B worktree status: `## team/debt-collection-ontology-todo-9-20260630/B`
- `git diff --stat C..A`: empty
- `git diff --stat C..B`: empty
- A/B/C Todo 9 branch heads at review time: `6943267d2e774540f2f8a0eb30f74085d9a79bd7`

## Sources Reviewed

- Team manual: `.omo/teams/debt-collection-ontology-todo-9-20260630/guide.md`
- Team state: `.omo/teams/debt-collection-ontology-todo-9-20260630/team.json`
- Domain contract: `docs/product/debt-collection-ontology/domain-contract.md`
- MCP server/auth baseline: `trustgraph-mcp/trustgraph/mcp_server/mcp.py`, `trustgraph-mcp/trustgraph/mcp_server/tg_socket.py`
- MCP package metadata: `trustgraph-mcp/pyproject.toml`
- Test dependency baseline: `tests/requirements.txt`, `tests/pytest.ini`
- Legal domain outputs: `trustgraph_legal/registry.py`, `trustgraph_legal/fields.py`, `trustgraph_legal/pii.py`, `trustgraph_legal/stopgate_types.py`, `trustgraph_legal/stop_gates.py`, `trustgraph_legal/governance.py`, `trustgraph_legal/governance_models.py`
- Existing tests: `tests/unit/legal_ontology/test_stop_gates.py`, `tests/unit/legal_ontology/test_ontology_governance.py`, `tests/unit/test_agent/test_mcp_tool_auth.py`, `tests/integration/test_tool_group_integration.py`

## Required Tool Group / Scope Matrix

Todo 9 should expose the v0 domain brain through one MCP-facing contract with these groups and scope rules:

| Group | Scope boundary | Expected tools | Acceptance checks |
| --- | --- | --- | --- |
| `read` | Read-only packet, document, and summary access. | `get_case_packet`, `get_case_documents`, `summarize_case_ledger` | Must not create facts, queue items, rule outcomes, registry rows, or graph writes. |
| `ingest` | Create source document and ingest registry records. | `ingest_legal_document`, `ingest_ocr_markdown`, `get_ingest_status` | May create document/registry records only; no ontology/rule promotion. |
| `graph` | Read/build case graph and extraction facts. | `classify_legal_document`, `extract_case_packet`, `get_case_graph` | May create candidate facts with provenance; may not clear StopGates by itself. |
| `stopgate` | Evaluate legal/compliance preconditions. | `check_case_stop_gates`, `check_limitation_status`, `check_attachment_target_rules`, `recommend_next_action` | Must return domain decisions only; may create review items for risky/missing evidence; no legal/business execution. |
| `governance` | Review queue and candidate transitions. | `list_unknown_document_types`, `review_extracted_fact`, `promote_ontology_candidate`, `reprocess_case` | May transition review state according to approval rules; must not mutate raw documents. |
| `admin` | Privileged versions and diagnostics. | `get_domain_versions`, `promote_rule_source_version`, `run_packet_regression` | Requires explicit privileged scope and audit logging; raw-source access, if ever added, belongs here only with separate authorization. |

## Canonical Tool List Addendum

Leader resolved the final canonical public tool count as 16. The earlier leader message said 16 but enumerated 15; the correction adds `list_debt_collection_tools` as the self-description/admin/read tool. Treat the corrected list below as the mismatch baseline for committed code:

| Group | Canonical tools |
| --- | --- |
| `read` / self-description | `list_debt_collection_tools`, `summarize_case_ledger` |
| `ingest` | `ingest_legal_document`, `ingest_ocr_markdown`, `get_ingest_status` |
| `graph` | `classify_legal_document`, `extract_case_packet`, `get_case_graph` |
| `stopgate` | `check_case_stop_gates`, `check_limitation_status`, `check_attachment_target_rules`, `recommend_next_action` |
| `governance` | `list_unknown_document_types`, `review_extracted_fact`, `promote_ontology_candidate`, `reprocess_case` |

Acceptance checks:

- Committed public tool names must match the corrected 16 unless a difference is documented as a thin compatibility alias.
- Earlier matrix examples such as `get_case_packet`, `get_case_documents`, `get_domain_versions`, `promote_rule_source_version`, and `run_packet_regression` are contract examples only unless the leader adds them to the canonical public list.
- Do not treat the earlier 15/16 count mismatch as an implementation defect by itself; treat it as corrected leader context unless committed source diverges from the corrected 16.

## Stable JSON Envelope Gate

Every Todo 9 MCP domain tool response should have the same top-level envelope:

```json
{
  "schema_version": "trustgraph-legal-mcp-domain-tool/v1",
  "tool_name": "check_case_stop_gates",
  "group": "stopgate",
  "scope": "stopgate",
  "pii_profile": {
    "raw_text_included": false,
    "source_text_included": false,
    "redaction_status": "redacted-output"
  },
  "source_refs": [],
  "warnings": [],
  "result": {}
}
```

Acceptance checks:

- `schema_version`, `tool_name`, `group`, `scope`, `pii_profile`, `source_refs`, `warnings`, and `result` must always be present.
- `warnings` must be a list even when empty.
- `source_refs` must be a list even when empty; empty is acceptable only for metadata-only calls such as `get_domain_versions`.
- Domain-specific payloads must live under `result`, not as ad hoc top-level fields.
- Existing baseline legal outputs already include useful `schema_version`, `source_refs`, and `pii_profile` fields in several places, but they do not yet have the Todo 9 MCP envelope. The adapter must wrap them consistently.

## Expected Facade / Adapter APIs

A reported the intended API names during this review. Treat these as acceptance anchors:

- Source facade: `trustgraph_legal.mcp_domain`
- Source facade exports: `TOOL_DEFINITIONS`, `list_tools()`, `invoke_tool(...)`
- MCP adapter helper: `trustgraph.mcp_server.legal_tools.register_debt_collection_brain_tools(mcp, repo_root=None)`
- Earlier `mcp_tools` names were provisional. Any committed mismatch should be flagged unless it is a documented thin compatibility alias over the final public surface.

Acceptance checks:

- `trustgraph_legal.mcp_domain` must be importable without the global `mcp` SDK.
- `TOOL_DEFINITIONS` must include each tool's stable name, group, scope, input contract, output envelope contract, and mutation boundary.
- `list_tools()` must be deterministic and return only the domain tool definitions.
- `invoke_tool(...)` must return the stable envelope for every success/error path and must not expose raw PII by default.
- `register_debt_collection_brain_tools(mcp, repo_root=None)` must be testable with a fake MCP object and must not require importing `FastMCP` or the global `mcp` SDK at module import time.

## Source Refs Contract

Material facts and decisions must be source-backed:

- Every extracted or graph material fact must cite source document/chunk/span or reviewed derived-rule refs.
- Every StopGate result must include `source_refs` and `rule_refs` where a rule/fact drove the decision.
- Derived facts must cite all input facts plus the rule/version used.
- Missing provenance must not be silently accepted. Existing `trustgraph_legal.stop_gates` already turns missing/placeholder provenance into an `invalid_fact_without_provenance` StopGate; Todo 9 wrappers must preserve that behavior.
- MCP-exposed `source_refs` must not include raw excerpts or unredacted OCR text by default. Use identifiers, line/span refs, confidence, redaction status, and hashes.

## Security / Privacy Boundary

Baseline MCP auth is gateway-backed:

- `trustgraph-mcp` uses `FastMCP` with `PassthroughTokenVerifier`.
- The MCP server accepts any non-empty Bearer token locally, then forwards it to the TrustGraph gateway.
- `WebSocketManager` sends the in-band auth frame and `whoami` validates the token against the gateway.
- Per-token socket keys are hashed; raw tokens must not be logged or persisted.

Todo 9 acceptance checks:

- Domain tools must use the same auth path as existing MCP tools; no direct unauthenticated path to `trustgraph_legal` through MCP.
- Group/scope checks must be explicit in the domain adapter or delegated to existing gateway/tool capability controls with evidence.
- Default outputs must be redacted. Baseline `trustgraph_legal.pii`, `fields`, `registry`, `stopgate_types`, and `governance_models` already mark `raw_text_included: False` in outputs; wrappers must not regress that.
- Raw source fetches must not be added to normal `read`, `graph`, `stopgate`, or `governance` tools. If raw source access is ever implemented, it must be an explicitly privileged `admin` path with audit logging and a separate access policy.
- Logs should include document ids, hashes, rule ids, and source refs only; no raw OCR sensitive identifiers or Bearer tokens.

## Non-Execution Boundary

Todo 9 tools may recommend, block, request evidence, or create review/governance state. They must not perform legal/business execution:

- no court filing/submission
- no debtor/guarantor/employer/bank/insurer/court/registry contact
- no payment, transfer, settlement, attachment, collection, or seizure initiation
- no external business-system update that implies action completion
- no final legal representation claims

StopGate and recommendation tools should return only `가능`, `불가능`, or `보류` decisions plus reasons, missing evidence, required preconditions, source refs, rule refs, risk flags, and review items.

## Single Physical MCP Service

The repo already has one physical MCP package/service: `trustgraph-mcp`, with `mcp-server = "trustgraph.mcp_server:run"` and a single `FastMCP` instance in `McpServer`.

Acceptance checks:

- Prefer registering debt-collection domain tools into this existing physical MCP service/adapter path.
- The logical v0 name `debt-collection-brain-mcp` is acceptable as a domain/tool namespace, but should not create a second long-lived MCP server/port/process unless the leader explicitly accepts that architecture.
- Registration should be thin and testable without importing the real global `mcp` SDK.
- The adapter helper should be `trustgraph.mcp_server.legal_tools.register_debt_collection_brain_tools(mcp, repo_root=None)` and should register the `trustgraph_legal.mcp_domain` definitions into the existing server path.

## Test Hermeticity / MCP SDK Risk

Leader finding confirmed the canonical Python test environment does not globally provide the `mcp` SDK.

Baseline:

- `trustgraph-mcp/pyproject.toml` depends on `mcp`.
- `tests/requirements.txt` does not include `mcp`.

Acceptance checks:

- CI-style Todo 9 tests must not pass only because a developer has `mcp` globally installed.
- Preferred: domain registration helper can be tested with a fake MCP object, requiring no SDK import.
- If integration tests import `trustgraph.mcp_server` or real `FastMCP`, they must provide isolated venv/package evidence that installs `trustgraph-mcp` dependencies, or document the dependency path in the test command.
- Tests should cover the registration list and tool metadata without requiring a live MCP service unless explicitly marked integration/manual.

## Runtime Interpreter Compatibility Risk

Repo package metadata in the Python packages reviewed declares `requires-python = ">=3.8"`. Existing `trustgraph_legal` code already contains newer annotation/type-alias patterns, including runtime `|` union aliases in some modules, which may effectively raise the floor beyond 3.8 in practice.

Todo 9 should avoid raising the compatibility floor further unless the team makes that an explicit package decision. In new MCP/domain-brain code, avoid Python syntax that cannot parse or execute on the declared runtime floor, especially:

- `match` / `case`
- PEP 695 `type Foo = ...`
- runtime `A | B` unions outside deferred annotations
- `except*`
- 3.10+ only standard-library APIs without compatibility guards

Post-implementation evidence should include either a compile/import check under the declared floor or a deliberate metadata update documenting the new minimum Python version.

## Implementation Review - A Commit `dfa70336`

Status: not accepted; blocking contract/security findings remain.

Reviewed source:

- `trustgraph_legal/mcp_domain.py`
- `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py`
- `trustgraph-mcp/trustgraph/mcp_server/mcp.py`
- `trustgraph-mcp/trustgraph/mcp_server/__init__.py`
- `tests/unit/legal_ontology/test_mcp_domain_tools.py`
- A report artifact: `.omo/teams/debt-collection-ontology-todo-9-20260630/artifacts/A-mcp-domain-tools-report.md`

Positive checks:

- Corrected canonical 16 tool names exist at `dfa70336`.
- `trustgraph_legal.mcp_domain` exposes `TOOL_DEFINITIONS`, `list_tools()`, and `invoke_tool(...)`.
- `trustgraph.mcp_server.legal_tools.register_debt_collection_brain_tools(mcp, repo_root=None)` exists and is importable without importing the global `mcp` SDK.
- Pinned commit verification passed in a clean temp archive: `/opt/homebrew/bin/python3 -m pytest --rootdir=. tests/unit/legal_ontology/test_mcp_domain_tools.py -q` -> `4 passed`.
- `git diff --check 6943267d2e774540f2f8a0eb30f74085d9a79bd7 dfa70336` passed.
- Domain responses include stable envelope fields and default PII redaction metadata.
- v0 write-like operations are review-safe envelopes, not direct filing/contact/collection execution.

Blocking findings:

1. Bearer token is modeled as a tool argument, not the MCP auth context.
   Evidence: `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py` at `dfa70336` defines registered tool functions as `run(arguments=None, authorization=None)` and raises unless `authorization.startswith("Bearer ")`. `trustgraph-mcp/trustgraph/mcp_server/mcp.py` registers these functions directly with `self.mcp.tool(...)`.
   Risk: MCP clients/agents must pass Bearer secrets inside the tool-call payload even though the server already has MCP auth middleware. That can expose secrets to model/tool transcripts and bypasses the existing `_require_token()` / `get_access_token()` security boundary used by the rest of the server.
   Required fix: domain tools should rely on the existing MCP auth middleware/server context, or register a wrapper that obtains the token from trusted MCP context without making `authorization` part of the public tool input. Fake-MCP tests can still assert that no global SDK import is required.

2. Path arguments allow arbitrary server-side file reads.
   Evidence: `trustgraph_legal/mcp_domain.py` at `dfa70336` accepts absolute paths in `_path_arg`; `_case_graph` reads `case_graph_path` with `Path.read_text()` and `get_case_graph` returns the parsed JSON. I reproduced this from a clean archive by passing `case_graph_path=/tmp/c-review-secret.json`; the tool returned `server secret token abc123` in `result`.
   Risk: any authenticated MCP caller can ask the domain layer to read arbitrary JSON/zip/manifest/ontology files available to the server process. Regex PII redaction is not a general secret redactor, so non-PII secrets or business-confidential content can leak.
   Required fix: replace raw filesystem path inputs on public MCP tools with document/case ids or explicitly bounded artifact roots; if fixture paths are needed for tests, gate them behind local-only helpers or reject absolute/out-of-root paths in MCP-facing code.

Current A branch drift:

- While this review was in progress, A advanced beyond `dfa70336` to `928cf8df` and then accumulated additional dirty edits in `tests/unit/legal_ontology/test_mcp_domain_tools.py`, `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py`, `trustgraph-mcp/trustgraph/mcp_server/mcp.py`, and `trustgraph_legal/mcp_domain.py`.
- Current A worktree verification at the end of this C pass: `/opt/homebrew/bin/python3 -m pytest --rootdir=. tests/unit/legal_ontology/test_mcp_domain_tools.py -q` -> `4 passed`.
- This implementation review remains pinned to the requested `dfa70336`. A should send a fresh DONE with the final commit once the newer branch/dirty state is stable.

Secondary risks:

- `trustgraph-mcp/trustgraph/mcp_server/__init__.py` changed from wildcard export to `__all__ = ["run"]`, so `trustgraph.mcp_server.McpServer` is no longer available from the package root. I found no in-repo imports, but it is a possible public API compatibility break for external users.

## Implementation Re-Review - A Commit `588fba0c`

Status: accepted for C's Todo 9 contract/security scope. The two previous blockers are resolved in this commit.

Reviewed source:

- `trustgraph_legal/mcp_domain.py`
- `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py`
- `trustgraph-mcp/trustgraph/mcp_server/mcp.py`
- `trustgraph-mcp/trustgraph/mcp_server/__init__.py`
- `tests/unit/legal_ontology/test_mcp_domain_tools.py`

Resolved blocker checks:

1. Bearer token is no longer a public tool argument.
   Evidence: `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py` defines registered tool functions as `run(arguments=None)` only, uses a `token_resolver`, and rejects missing context with `PermissionError("MCP auth context required")`. `trustgraph-mcp/trustgraph/mcp_server/mcp.py` registers domain tools with `token_resolver=_require_token`, so production uses existing MCP auth context.

2. Public path arguments are repo-bound.
   Evidence: `trustgraph_legal/mcp_domain.py` resolves candidate paths, checks `resolved.relative_to(root)`, and converts outside-root paths to a stable rejected envelope through `PermissionError("path_outside_repo_root")`.

Verification run on a clean `588fba0c` archive:

- `/opt/homebrew/bin/python3 -m pytest --rootdir=. tests/unit/legal_ontology/test_mcp_domain_tools.py -q` -> `5 passed`
- `/opt/homebrew/bin/python3 -m pytest --rootdir=. tests/unit/legal_ontology -q` -> `36 passed`
- `git diff --check 588fba0c~1 588fba0c` -> passed
- Smoke reproduction:
  - registered fake-MCP tool signature contains no `authorization`
  - resolver token did not appear in response JSON
  - missing resolver rejected with `MCP auth context required`
  - `/tmp/c-review-secret-588.json` `case_graph_path` returned `{"status": "rejected", "reason": "path_outside_repo_root"}`
  - outside secret and outside path did not appear in response JSON
  - tool count remained 16
  - `from trustgraph.mcp_server import legal_tools` imported without the global `mcp` SDK

Residual notes:

- The public v0 tool groups in `588fba0c` are `read`, `ingest`, `graph`, `stopgate`, and `governance`; no canonical public `admin` tool is present. This matches the corrected 16-tool list where `list_debt_collection_tools` is self-description/read.
- `trustgraph.mcp_server.McpServer` is exposed through lazy `__getattr__` and `__all__`, but importing that symbol still requires the `mcp` package because the actual server module imports `FastMCP`. This is acceptable for production package usage; the SDK-independent adapter import boundary remains `trustgraph.mcp_server.legal_tools`.

## Post-Implementation Acceptance Checklist

Before leader accepts Todo 9, verify:

- A/B branches contain visible Todo 9 changes and are no longer identical to C/base.
- Corrected canonical 16 tools exist with exact public names, or any extra/legacy name is documented as a thin compatibility alias.
- `trustgraph_legal.mcp_domain` exposes `TOOL_DEFINITIONS`, `list_tools()`, and `invoke_tool(...)`.
- `trustgraph.mcp_server.legal_tools.register_debt_collection_brain_tools(mcp, repo_root=None)` is importable and fake-MCP-testable without a global `mcp` SDK.
- Every tool returns the stable envelope with the required top-level fields.
- `source_refs` is present and redacted for material facts and decisions.
- StopGate tools preserve deterministic `가능` / `불가능` / `보류` behavior and do not execute external actions.
- Group/scope metadata is correct and tested for the corrected public v0 groups: `read`, `ingest`, `graph`, `stopgate`, and `governance`; any future `admin` tool must be explicitly privileged and separately tested.
- `read` tools are mutation-free.
- `ingest`, `graph`, `governance`, and `admin` tools mutate only within their allowed boundary.
- Bearer-token behavior uses the existing MCP/gateway path; no unauthenticated MCP domain route exists.
- Bearer tokens are not public tool arguments and are not passed through model/tool payloads.
- Public MCP tools do not read arbitrary server filesystem paths from caller-controlled absolute or out-of-root path arguments.
- Tests do not silently require global `mcp`; fake-MCP registration tests or isolated venv evidence are present.
- No default output, fixture, log, or artifact contains raw national IDs, phone numbers, account numbers, full addresses, or raw OCR sensitive spans.
- New Python syntax does not unnecessarily raise the runtime floor beyond the repo/package declaration.
- The implementation remains one physical MCP service/adapter, with `debt-collection-brain-mcp` as a logical domain surface rather than an uncoordinated second service.

## Acceptance Risks

1. Previous `dfa70336` blockers are resolved at `588fba0c`: Bearer tokens are not public tool arguments, and caller-controlled paths are repo-bound.
2. Missing envelope consistency would make agent consumption brittle even if underlying legal functions work.
3. Missing or raw `source_refs` would break the core provenance and PII contract.
4. Tests that import real MCP SDK without isolated dependency setup would pass only on developer machines with global `mcp`.
5. New Python syntax could silently raise runtime requirements beyond `>=3.8`.
6. A second physical MCP service would fragment token handling, packet identity, and governance state unless deliberately accepted.
