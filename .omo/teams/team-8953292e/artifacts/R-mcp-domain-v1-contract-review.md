# R MCP Domain v1 Contract Review

Reviewer: R / mcp-domain-v1-review
Thread: codex://threads/019f38de-6893-7090-aa82-d8e5826e36e6
Scope: Todo 12 read-only contract/security review
Status: ACCEPTED - final review pinned to Q commit `21e6c5bd955f5d0cafbc0399c493803dd8994940`
Date: 2026-07-07

## Final Verdict

ACCEPTED. Q commit `21e6c5bd955f5d0cafbc0399c493803dd8994940` satisfies the Todo 12 MCP contract/security gates and is merge-ready from R's review lens.

No blocking findings.

Non-blocking note: the commit does not add a separate `final-tool-list.json`; the required tool-list evidence is present in `.omo/evidence/debt-collection-domain-ontology-v1/task-12-mcp-happy.json` under `tool_order` with the first 21 tools, four appended tools, listed count 25, and registered count 25.

## Pinned Review Target

- Branch: `team/team-8953292e/Q`
- Commit: `21e6c5bd955f5d0cafbc0399c493803dd8994940`
- Subject: `feat(legal-mcp): expose claim domain ontology tools`
- Q report: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/team-8953292e/artifacts/Q-mcp-domain-v1-tools-report.md`

Changed files are limited to the expected Todo 12 surfaces:

- `.omo/evidence/debt-collection-domain-ontology-v1/task-12-mcp-failure.json`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-12-mcp-happy.json`
- `tests/integration/legal_ontology/test_mcp_tools.py`
- `tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py`
- `tests/unit/legal_ontology/test_mcp_domain_tools.py`
- `tests/utils/legal_mcp_support.py`
- `trustgraph_legal/mcp_claim_domain_handlers.py`
- `trustgraph_legal/mcp_domain.py`

## Gate Results

- Tool order: PASS. `trustgraph_legal/mcp_domain.py` preserves the existing first 21 MCP definitions and appends exactly `list_claim_domain_routes`, `explain_collection_workflow_state`, `evaluate_claim_domain_decision`, and `explain_claim_action_packet`.
- Context auth and callable shape: PASS. `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py` still wraps every registered tool through `_require_context_auth(...)`; fake-MCP registered callables expose only `arguments`; no public `authorization`, `token`, `bearer`, or `secret` tool parameter is exposed.
- Token safety: PASS. Happy and failure evidence show no token echo, and an independent review script confirmed a hidden review token is not serialized.
- Repo-root path bounds: PASS. Outside-root path failure returns `path_outside_repo_root` in a redacted envelope with no file path or file-content leak.
- Advisory/non-executing semantics: PASS. Claim-domain route, workflow, decision, and action-packet handlers return advisory/read-only data; `evaluate_claim_domain_decision` and `explain_claim_action_packet` carry `advisory_only_human_review_required`, `direct_execution_allowed: false`, and no debtor-contact or filing-destination payload fields.
- Runtime isolation: PASS. Static search on the runtime files found no OpenAI/Anthropic/LLM, live service, Korean-law MCP, HTTP client, socket, subprocess, or production mutation calls. Hits were limited to existing descriptive strings saying production execution is not performed.
- Evidence JSON: PASS. Both `task-12-mcp-happy.json` and `task-12-mcp-failure.json` parse as JSON; semantic checks passed for tool order, auth, path redaction, token leak flags, and secret leak flags.
- PII/path leak scan: PASS. Evidence/source scan found no repo path, temp path, national-id shape, phone shape, task token, or outside-root secret leak in Todo 12 source/evidence/test surfaces.
- Helper extraction: PASS. `tests/utils/legal_mcp_support.py` centralizes the existing fake-MCP/envelope/leak helpers without weakening integration coverage; `tests/integration/legal_ontology/test_mcp_tools.py` still asserts the full expected tool set/count, stable redacted envelopes, source-ref redaction, sensitive-shape absence, context-auth registration, TypeError for public `authorization`, raw-token rejection, scope rejection, and missing-auth rejection. The new unit test adds explicit 21+4 ordering coverage.
- Diff check: PASS. No deployment/runbook or unrelated production files are touched.

## Reproduced Commands

- PASS: `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py -q` -> 13 passed.
- PASS: `/Users/cosmos/.local/bin/basedpyright --level error trustgraph_legal/mcp_claim_domain_handlers.py trustgraph_legal/mcp_domain.py tests/utils/legal_mcp_support.py tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py` -> 0 errors, 0 warnings, 0 notes.
- PASS: `/opt/homebrew/bin/python3 -m py_compile trustgraph_legal/mcp_claim_domain_handlers.py trustgraph_legal/mcp_domain.py tests/utils/legal_mcp_support.py tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py`.
- PASS: independent evidence parse/leak script over `task-12-mcp-happy.json` and `task-12-mcp-failure.json`.
- PASS: independent tool-order/auth/callable-shape script over `list_tools()` and fake-MCP registered callables.
- PASS: independent public sensitive parameter scan over `list_tools()`.

## Pre-Implementation Baseline

Superseded by the final review above.

Q is not ready for final review yet.

- `team/team-8953292e/Q` points at the same commit as `master` and R: `29b726cc Merge branch 'team/team-8953292e/O'`.
- `git log --oneline --decorate --no-merges master..team/team-8953292e/Q` returned no commits.
- `git diff --name-status master...team/team-8953292e/Q` returned no Todo 12 diff.
- No `Q-mcp-domain-v1-tools-report.md` exists in the team artifacts directory.
- No task-12 evidence files exist under `.omo/evidence/debt-collection-domain-ontology-v1/`.
- `git ls-tree -r --name-only team/team-8953292e/Q` shows the pre-existing MCP files only: `trustgraph_legal/mcp_domain.py` and `tests/unit/legal_ontology/test_mcp_domain_tools.py`; it does not show the Todo 12 test file or evidence artifacts.

Coordination updates from Q/leader, not independently reviewed because Q has not committed:

- Q reports the current MCP surface has 21 definitions in `trustgraph_legal/mcp_domain.py`, and `legal_tools.py` wraps them with context auth and no public `authorization` argument.
- Q reports a focused red baseline in `tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py` where all four failures are the missing Todo 12 tool surface rather than import or fixture noise.
- Q reports the required focused suite now passes 13 tests after adding four appended claim-domain tools and a dedicated handler module: `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py -q`.
- Q reports an uncommitted conservative test-size refactor: shared fake-MCP/tool-list scaffolding extracted to `tests/utils/legal_mcp_support.py`, with `tests/integration/legal_ontology/test_mcp_tools.py` trimmed while preserving 21+4 ordering behavior tests.

## Existing MCP Tool Baseline

`/opt/homebrew/bin/python3` importing `trustgraph_legal.mcp_domain.list_tools()` currently reports 21 tools in this order:

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
17. `assemble_debtor_documents`
18. `build_debtor_context_graph`
19. `get_debtor_graph_snapshot`
20. `list_debtor_route_candidates`
21. `explain_debtor_route_candidate`

Expected Todo 12 final state: these 21 remain first, followed by exactly four appended tools:

22. `list_claim_domain_routes`
23. `explain_collection_workflow_state`
24. `evaluate_claim_domain_decision`
25. `explain_claim_action_packet`

## Historical Final-Pass Checklist

Superseded by the reproduced final review above. This was the pre-commit checklist used to drive the pinned review:

- Tool order: prove the existing 21 MCP tools remain first and the four claim-domain tools are appended in the expected order.
- Context-auth wrapping: prove `legal_tools.py` continues wrapping every tool through context auth with no public `authorization` argument or token-style callable parameter.
- Tool registration: confirm the four new tools are registered through the existing MCP surface and remain read-only.
- Auth contract: confirm no authorization token is present in public tool schemas, tool arguments, callable parameters, evidence, or error output.
- Token handling: confirm missing-auth failure does not echo token material or resolver internals.
- Repo-root path bounds: confirm outside-root path failures are rejected and redacted, with no sensitive local path leak.
- Advisory boundary: confirm `evaluate_claim_domain_decision` and `explain_claim_action_packet` are advisory/non-executing and cannot contact debtors, file with a court, demand payment, execute attachment, or mutate production systems.
- Source refs and versions: confirm source refs, legal-source versions, effective dates, and domain resource versions align with Wave 1-3 resources.
- Runtime isolation: confirm the MCP runtime path does not call LLMs, live services, Korean-law MCP, production systems, or external network dependencies.
- PII/path safety: scan source, tests, evidence, and report for raw OCR text, resident-registration-number patterns, phone numbers, account-like identifiers, real names, and local sensitive paths.
- Python compatibility: inspect changed Python for strict typed boundaries, no public `Any` expansion, no broad exception leakage, and no import-floor regressions.
- Focused tests: run `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py -q`.
- Test extraction: review `tests/utils/legal_mcp_support.py` and the integration-test diff to ensure shared fake-MCP/tool-list scaffolding preserves, rather than weakens, existing integration assertions.
- Evidence JSON: inspect `.omo/evidence/debt-collection-domain-ontology-v1/task-12-mcp-happy.json`, `task-12-mcp-failure.json`, and `final-tool-list.json`.
- Diff check: verify Todo 12 touches only expected MCP/domain/evidence/test/report surfaces and does not mutate deployment/runbook or unrelated production files.
- Merge readiness: mark ready only if all contract checks pass with reproducible commands and no unreviewed security deferrals.

## Historical Missing Items

Superseded by Q commit `21e6c5bd955f5d0cafbc0399c493803dd8994940` and the reproduced final review above. These were the missing items before Q landed:

- A Todo 12 commit on `team/team-8953292e/Q`.
- The four additive read/explain MCP tools.
- Focused MCP tests, including `tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py`.
- Happy and failure evidence JSON for fake-MCP invocation, auth failure, and outside-root redaction.
- Final tool-list evidence proving the 21 + 4 order.
- `artifacts/Q-mcp-domain-v1-tools-report.md`.

## Current Verdict

ACCEPTED. Q Todo 12 is merge-ready from R's read-only MCP contract/security review perspective.
