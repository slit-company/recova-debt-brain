# P MCP Governance Review

Status: TODO 11 ACCEPTED FOR P CONTRACT REVIEW - TODO 12 PENDING

Member: P / mcp-governance-review
Scope: read-only contract review for Todo 11 additive MCP debtor graph tools and Todo 12 governance/review hooks. Production files were not edited.

## Baseline Reviewed

- Team plan: `/Users/cosmos/dev/ontology/trustgraph/.omo/plans/debtor-context-graph-v0.md`
- P worktree: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debtor-context-graph-v0-20260706/worktrees/P`
- P branch: `team/debtor-context-graph-v0-20260706/P`
- Current baseline HEAD: `13e7a097` (`Merge branch 'team/debtor-context-graph-v0-20260706/M'`)
- Todo 10 baseline: M integrated on master by merge `13e7a097`
- Route compatibility baseline: K final route compatibility integrated at `0fc37242`
- N branch state at checklist time: `13e7a097` (no Todo 11 implementation commit visible yet)
- O branch state at checklist time: `13e7a097` (no Todo 12 implementation commit visible yet)
- Current MCP domain baseline exposes exactly 16 tools.

This document is not an approval or rejection of N/O. It is the checklist P will use once N/O commits are available.

## Baseline Verification

Commands run from P worktree:

- `git rev-parse master team/debtor-context-graph-v0-20260706/N team/debtor-context-graph-v0-20260706/O team/debtor-context-graph-v0-20260706/P`
  - Result: all four refs equal `13e7a097a69bcc3c4ee44002ff4f7cd2239d7601`.
- `/opt/homebrew/bin/python3` import probe for `trustgraph_legal.mcp_domain.list_tools()`
  - Result: 16 tool names, matching the baseline list below.
- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_domain_tools.py -q`
  - Result: 6 passed.
- `/opt/homebrew/bin/python3 -m pytest tests/integration/legal_ontology/test_mcp_tools.py -q`
  - Result: 3 passed.
- PII regex scan over this artifact
  - Result: no findings.
- `git status --short --branch`
  - Result: P production worktree clean.

## Baseline 16 MCP Tools To Preserve

Existing tools must remain compatible and ordered before additive debtor tools unless N deliberately updates the expected-list tests with leader acceptance.

1. `list_debt_collection_tools`
2. `ingest_legal_document`
3. `ingest_ocr_markdown`
4. `get_ingest_status`
5. `classify_legal_document`
6. `extract_case_packet`
7. `get_case_graph`
8. `check_case_stop_gates`
9. `check_limitation_status`
10. `check_attachment_target_rules`
11. `summarize_case_ledger`
12. `recommend_next_action`
13. `list_unknown_document_types`
14. `review_extracted_fact`
15. `promote_ontology_candidate`
16. `reprocess_case`

Compatibility gate:

- `list_tools()` still returns the above 16 first, with unchanged `tool_name`, `group`, `scope`, input schema, output schema, and redaction contract.
- Existing `tests/unit/legal_ontology/test_mcp_domain_tools.py` and `tests/integration/legal_ontology/test_mcp_tools.py` still pass after additive debtor tool expectations are intentionally updated.
- Existing fake-MCP registration still imports `trustgraph.mcp_server.legal_tools` without importing the full global MCP SDK.

## Todo 11 Checklist - Additive MCP Debtor Graph Tools

Required additive tools:

- `assemble_debtor_documents`
- `build_debtor_context_graph`
- `get_debtor_graph_snapshot`
- `list_debtor_route_candidates`
- `explain_debtor_route_candidate`

Contract gates:

- Additive only: no existing 16-tool removal, rename, reorder, or incompatible schema change.
- Group is `debtor_graph`; scopes are limited to `debtor_graph:assembly`, `debtor_graph:build`, `debtor_graph:read`, and `debtor_graph:routes`.
- Tool definitions use the existing redacted `trustgraph_legal.mcp_domain` envelope: `schema_version`, `tool_name`, `group`, `scope`, `pii_profile`, `redaction`, `source_refs`, `warnings`, and `result`.
- No public `authorization`, `token`, `bearer`, `secret`, or auth-context argument appears in tool parameters, function signatures, input schemas, tests, or evidence.
- Adapter auth stays context/resolver based through `trustgraph.mcp_server.legal_tools`; registered callables accept `arguments=...` only.
- Handler/domain code remains under `trustgraph_legal`; the MCP SDK layer stays a thin registration adapter.

Path and redaction gates:

- All file inputs that can read local content, including `assembly_path`, `graph_path`, route-resource paths, and legal-source paths, are resolved under `repo_root`.
- Outside-root paths return a rejected envelope with `reason == "path_outside_repo_root"`.
- Outside-root failure responses do not leak the attempted absolute path, file content, or sentinel secret strings.
- MCP responses do not include raw OCR text, source text, debtor names, resident-registration-number patterns, phone numbers, account-like identifiers, or full real OCR paths.
- `source_refs` are pointers only. Nested source refs must be normalized without copying excerpts.
- Route candidate outputs preserve advisory-only semantics and never claim filing, contact, payment demand, or collection execution.

Verification gates:

- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_debtor_context_tools.py tests/unit/legal_ontology/test_mcp_domain_tools.py -q`
- `/opt/homebrew/bin/python3 -m pytest tests/integration/legal_ontology/test_mcp_tools.py -q`
- Fake-MCP test proves no global `mcp` SDK import is required.
- Failure evidence includes outside-root `assembly_path` or `graph_path` rejection without path/content leakage.
- Happy evidence returns redacted route candidates through an MCP/fake-MCP call.
- `py_compile`, Python 3.9/import compatibility probe where relevant, PII scan, JSON evidence validation, and `git diff --check`.

## Todo 12 Checklist - Governance / Review Hooks

Required review cases:

- Unknown assemblies.
- Unresolved identity.
- Conflicting debtor facts or claim amounts.
- Draft, future, unretrieved, missing, or otherwise review-required legal sources.
- Blocked route candidates.
- Manual fact review decisions.

Service-record boundary gates:

- Governance records are service-side review/audit records, not production ontology/resource mutations.
- Production ontology, route resources, legal-source resources, and source OCR artifacts remain read-only in v0.
- Any promotion or review decision response must include explicit mutation flags such as `production_ontology_modified: false` or equivalent.
- Review records are serializable and PII-safe: ids, hashes, reason codes, review statuses, source refs, and aggregate counts are allowed; raw OCR text, excerpts, debtor identifiers, phones, accounts, and full real paths are not.
- Records include enough audit context for later service-side processing: record id, queue/reason code, target id, source refs or source fact ids, review status, created/updated timestamps or deterministic v0 stand-ins, approval metadata requirements, and no-direct-execution markers where routes are involved.
- Manual fact review cannot silently mutate graph facts; it must return a queued or review decision record with audit metadata.
- Promotion without required approval metadata is rejected with audit fields, not applied.

Integration gates:

- Todo 12 may extend existing governance concepts or add `trustgraph_legal/debtor_governance.py`, but it must not push governance persistence into the MCP adapter.
- Todo 11 can surface governance results only through the existing redacted envelope and context-auth boundary.
- Governance review states must align with route/legal-source semantics accepted by Todo 9: approved legal source metadata can clear review blockers, but never direct-execution constraints.

Verification gates:

- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_debtor_governance.py -q`
- Evidence for unknown assembly happy path: review item plus reprocess suggestion.
- Evidence for failure path: promotion or manual approval attempt without required metadata is rejected with audit fields.
- PII scan over source, tests, resources, evidence, and this report.
- `py_compile`, Python 3.9/import compatibility probe where relevant, JSON evidence validation, and `git diff --check`.

## P Re-Review Steps After N/O Commits

When N commits Todo 11:

- Pin review to N's commit hash.
- Compare N against `13e7a097`.
- Verify the 16 baseline tools are still present first and in order.
- Inspect all new tool definitions, parameters, scopes, handler paths, and evidence files.
- Run the Todo 11 focused MCP/fake-MCP tests and path-failure evidence checks.
- Update this artifact with accepted/rejected findings.

When O commits Todo 12:

- Pin review to O's commit hash.
- Compare O against `13e7a097` or the leader-provided integration base.
- Inspect governance record models, service-side boundaries, mutation flags, and evidence files.
- Run the Todo 12 focused governance tests.
- Update this artifact with accepted/rejected findings.

Before final P acceptance:

- Review the integrated N+O state, not only each branch in isolation.
- Run the combined MCP/governance focused test surface.
- Confirm no global MCP SDK dependency is introduced into hermetic fake-MCP tests.
- Confirm no raw PII/path leakage in new MCP/governance evidence.

## Live Coordination Notes

- N Todo 11 public MCP output note: `explain_debtor_route_candidate` will not introduce new governance/review field names. It will summarize existing route candidate fields only: `review_status`, `no_direct_execution`, `required_facts`, `missing_facts`, `blocking_facts`, `legal_source_refs`, and `source_fact_ids`.
- P review implication: Todo 11 can be assessed as a route-candidate explanation surface rather than a governance-record surface. O-owned governance record names remain separate unless later explicitly integrated.

## Todo 11 Review - N Commit `5d68c0b3`

Verdict: ACCEPTED for P's MCP/governance contract-security scope.

Reviewed target:

- N commit: `5d68c0b33a2e1432682db77ed83aef90e837cfc8`
- Commit message: `feat(legal-mcp): expose debtor context graph tools`
- Base compared: `13e7a097`
- Changed implementation files: `trustgraph_legal/mcp_domain.py`, `trustgraph_legal/mcp_handlers.py`, `trustgraph_legal/mcp_debtor_handlers.py`
- Changed test/evidence files: `tests/unit/legal_ontology/test_mcp_debtor_context_tools.py`, `tests/unit/legal_ontology/test_mcp_domain_tools.py`, `tests/integration/legal_ontology/test_mcp_tools.py`, task-11 evidence JSON files.
- N report: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debtor-context-graph-v0-20260706/artifacts/N-mcp-debtor-tools-report.md`

Accepted contract points:

- Existing 16 MCP tools are preserved first and in order.
- Five debtor graph tools are appended after the existing 16:
  - `assemble_debtor_documents`
  - `build_debtor_context_graph`
  - `get_debtor_graph_snapshot`
  - `list_debtor_route_candidates`
  - `explain_debtor_route_candidate`
- New tools use group `debtor_graph` with scopes `debtor_graph:assembly`, `debtor_graph:build`, `debtor_graph:read`, and `debtor_graph:routes`.
- Public tool parameters do not include `authorization`, `token`, or `bearer`.
- Fake-MCP registration remains SDK-independent at the `trustgraph.mcp_server.legal_tools` adapter boundary.
- Context-auth remains outside tool payloads; P's direct fake-MCP probe found 21 registered tools, no `authorization` callable parameters, correct `debtor_graph:routes` scope, and no token echo.
- File reads for `ocr_root`, `assembly_path`, `graph_path`, `route_resources`, and `legal_sources` flow through repo-root bounded `path_arg`.
- Outside-root `graph_path` returns a rejected redacted envelope with `reason == "path_outside_repo_root"`, empty source refs, and no outside path/content echo.
- `explain_debtor_route_candidate` summarizes existing route fields only and does not create a new governance-record surface.
- Task-11 evidence JSON contains no raw OCR marker, local absolute path, outside-path marker, synthetic secret, RRN pattern, phone pattern, or account-like identifier match.

Verification reproduced by P:

- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_debtor_context_tools.py tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py -q`
  - Result: 13 passed.
- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_document_assembly.py tests/unit/legal_ontology/test_debtor_context.py tests/unit/legal_ontology/test_route_candidates.py tests/unit/legal_ontology/test_mcp_debtor_context_tools.py tests/integration/legal_ontology/test_debtor_context_pipeline.py tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py -q`
  - Result: 39 passed.
- `/opt/homebrew/bin/python3 -m py_compile trustgraph_legal/mcp_debtor_handlers.py trustgraph_legal/mcp_handlers.py trustgraph_legal/mcp_domain.py tests/unit/legal_ontology/test_mcp_debtor_context_tools.py tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py`
  - Result: passed.
- `/usr/bin/python3 -m py_compile trustgraph_legal/mcp_debtor_handlers.py trustgraph_legal/mcp_handlers.py trustgraph_legal/mcp_domain.py`
  - Result: passed on Python 3.9.6 parser/compile gate.
- `/Users/cosmos/.local/bin/basedpyright --level error ...`
  - Result: 0 errors.
- `git diff --check 13e7a097 5d68c0b3`
  - Result: passed.
- Evidence JSON parse and leak-marker checks
  - Result: passed for `task-11-mcp-happy.json` and `task-11-mcp-path-failure.json`.

Residual notes, not Todo 11 blockers:

- Full `/usr/bin/python3 -c 'import trustgraph_legal.mcp_domain'` still fails with `TypeError: unsupported operand type(s) for |: 'type' and 'type'`. This is pre-existing at baseline `13e7a097` via `trustgraph_legal/governance_models.py:202` (`PromotionAccepted | PromotionRejected`) and not introduced by N. N's changed modules pass the Python 3.9 `py_compile` gate.
- Size guard: `tests/integration/legal_ontology/test_mcp_tools.py` is 289 pure LOC and `tests/unit/legal_ontology/test_mcp_domain_tools.py` is 246 pure LOC after N. This is a maintainability warning for a future test split, not a P contract-security blocker for Todo 11.

## Todo 12 Review - O Commit `3901c90b`

Verdict: ACCEPTED for P's governance service-record boundary review.

Reviewed target:

- O commit: `3901c90bd83746a08042dbe4a1d69f785241ee2b`
- Commit message: `feat(legal-graph): add debtor governance records`
- Base compared: `13e7a097`
- Changed implementation files: `trustgraph_legal/debtor_governance.py`, `trustgraph_legal/debtor_governance_models.py`, `trustgraph_legal/debtor_governance_sources.py`
- Changed test/evidence files: `tests/unit/legal_ontology/test_debtor_governance.py` and `.omo/evidence/debtor-context-graph-v0/task-12-*`
- O evidence report: `.omo/evidence/debtor-context-graph-v0/task-12-report.md`

Accepted contract points:

- Governance records are service-side records over existing debtor graph and route outputs.
- No MCP SDK import was added.
- No MCP adapter, route resource, legal-source resource, ontology resource, or OCR source artifact was changed by O.
- Record schema includes the expected stable fields: `kind`, `subject_ref`, `reason_code`, `severity`, `review_status`, `source_refs`, `source_fact_ids`, `suggested_action`, `pii_profile`, and `audit`.
- Payload-level mutation flags are explicit and false: `production_resources_modified`, `production_ontology_modified`, `production_routes_modified`, and `production_legal_sources_modified`.
- Record-level audit flags keep `resource_mutation`, `production_ontology_modified`, `production_routes_modified`, and `production_legal_sources_modified` false and preserve `no_direct_execution`.
- Coverage includes unknown assemblies, unresolved identity, conflicting facts, legal-source review states, blocked/review routes, and manual fact review decisions.
- Manual approval without approval evidence is rejected service-side with `reason_code == "missing_manual_fact_approval_metadata"`, not applied to production graph or resources.
- Evidence JSON is serializable, PII-safe, and uses source refs / source fact ids rather than raw text or debtor identifiers.

Verification reproduced by P:

- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_debtor_governance.py -q`
  - Result: 3 passed.
- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_debtor_context.py tests/unit/legal_ontology/test_route_candidates.py tests/unit/legal_ontology/test_debtor_governance.py -q`
  - Result: 18 passed.
- `/opt/homebrew/bin/python3 -m py_compile trustgraph_legal/debtor_governance.py trustgraph_legal/debtor_governance_models.py trustgraph_legal/debtor_governance_sources.py tests/unit/legal_ontology/test_debtor_governance.py`
  - Result: passed.
- `/usr/bin/python3 -m py_compile trustgraph_legal/debtor_governance.py trustgraph_legal/debtor_governance_models.py trustgraph_legal/debtor_governance_sources.py`
  - Result: passed.
- `/usr/bin/python3 -c 'import trustgraph_legal.debtor_governance; print("python39_import_ok")'`
  - Result: `python39_import_ok`.
- `/Users/cosmos/.local/bin/basedpyright --level error trustgraph_legal/debtor_governance.py trustgraph_legal/debtor_governance_models.py trustgraph_legal/debtor_governance_sources.py tests/unit/legal_ontology/test_debtor_governance.py`
  - Result: 0 errors.
- `git diff --check 13e7a097 3901c90b`
  - Result: passed.
- JSON validation for `task-12-governance-happy.json` and `task-12-manual-rejection.json`
  - Result: passed.
- PII/evidence scan over `.omo/evidence/debtor-context-graph-v0/task-12-*`
  - Result: no findings.

Size guard:

- `trustgraph_legal/debtor_governance.py`: 180 pure LOC.
- `trustgraph_legal/debtor_governance_models.py`: 125 pure LOC.
- `trustgraph_legal/debtor_governance_sources.py`: 42 pure LOC.
- `tests/unit/legal_ontology/test_debtor_governance.py`: 204 pure LOC.

## Integrated N+O State Review

Verdict: ACCEPTED for P final MCP/governance boundary review.

Integrated target:

- N commit `5d68c0b3` integrated by merge `40d49aa8`.
- O commit `3901c90b` integrated by merge `880cba38`.
- Current main checkout `master`: `880cba3816f5c1ebef9483e7feda52e69b2ad8b6`.

Leader-provided integrated gates:

- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_debtor_context_tools.py tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py tests/unit/legal_ontology/test_debtor_governance.py -q` -> 16 passed.
- `/usr/bin/python3 -c 'import trustgraph_legal.debtor_governance; print("governance-import-ok")'` -> passed.
- MCP tool count is 21 with existing 16 first and five `debtor_graph` tools appended.

Integrated gates reproduced by P on main checkout:

- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_debtor_context_tools.py tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py tests/unit/legal_ontology/test_debtor_governance.py -q`
  - Result: 16 passed.
- `/usr/bin/python3 -c 'import trustgraph_legal.debtor_governance; print("governance-import-ok")'`
  - Result: `governance-import-ok`.
- `/opt/homebrew/bin/python3` MCP tool-list probe
  - Result: 21 tools; existing 16 first, followed by `assemble_debtor_documents`, `build_debtor_context_graph`, `get_debtor_graph_snapshot`, `list_debtor_route_candidates`, and `explain_debtor_route_candidate`.

Integrated-state notes:

- Main checkout has unrelated dirty deployment/team artifacts and local planning/evidence files. P did not modify or rely on those for the O review except to observe `master` at merge `880cba38` and rerun the integrated verification gates.
- The accepted Todo 11 route explanation surface and accepted Todo 12 governance record surface remain separate: Todo 11 summarizes existing route candidate fields; Todo 12 owns service-side governance record names.

## Current Verdict

Todo 11 is accepted for P review at N commit `5d68c0b3`.

Todo 12 is accepted for P review at O commit `3901c90b`.

The integrated N+O state at master merge `880cba38` is accepted for P final MCP/governance boundary review.
