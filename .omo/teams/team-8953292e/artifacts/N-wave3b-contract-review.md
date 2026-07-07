# N Wave 3b Contract Review

Reviewer: N / wave3b-review
Thread: codex://threads/019f38a5-92db-7280-80c0-a2a7a2295a00
Scope: read-only review of Todo 8 and Todo 10 outputs, evidence, source safety, and integration compatibility.
Worktree verified: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/team-8953292e/worktrees/N`
Branch verified: `team/team-8953292e/N`

## Pre-Implementation Checklist

- [x] Read team field manual and team state.
- [x] Confirm assigned worktree path and branch before inspection.
- [x] Confirm artifact-only write boundary.
- [x] Read Todo 8 and Todo 10 plan contracts.
- [x] Confirm L commit and report are available.
- [x] Confirm M commit and report are available.
- [x] Review Todo 8 diff and implementation against contract.
- [x] Review Todo 8 evidence, validator behavior, PII/path safety, and non-execution boundary.
- [x] Review Todo 10 diff and implementation against contract.
- [x] Review Todo 10 evidence, adapter identity/source semantics, PII/path safety, and v0 behavior preservation.
- [x] Run focused Todo 8 verification.
- [x] Run focused Todo 10 verification.
- [x] Run existing compatibility checks relevant to Wave 3b.
- [x] Run temporary L+M merge simulation from current master.
- [x] Record ACCEPTED/BLOCKED verdict for L.
- [x] Record ACCEPTED/BLOCKED verdict for M.
- [x] Record ACCEPTED/BLOCKED verdict for Wave 3b.

## Contract Notes

Todo 8 must add advisory action packet schemas at `resources/action_packets/debt_collection_action_packets_v1.json` plus a validator and tests. Required packet families are evidence-request, legal-action-review, finance-review, contact-review, monitoring/retry, and insolvency/recovery-review. Every schema must specify required inputs, source refs, PII profile, review status, non-execution semantics, and forbidden fields. No schema may include actual filing destination, debtor contact channel payload, or executable instruction.

Todo 10 must add a narrow DebtorContextGraph to claim-domain v1 compatibility adapter. It must map fact assertions, route candidates, governance records, and snapshots into claim-centered handles while preserving graph IDs and source refs. It must not change debtor identity merge behavior, graph snapshot generation, or route candidate v0 outputs. Adapter output must include claim root, source_bundle_hash, graph_snapshot_id, and no raw OCR text.

## Review Log

- Pending L/M outputs. N is ready to review once commits and reports are available.
- Current discovery:
  - `team/team-8953292e/L` equals current `master` (`fb36cbe8e2601e04e33c1d714dcd9095e3992a5e`); no L commit is available to review yet.
  - `team/team-8953292e/M` equals current `master` (`fb36cbe8e2601e04e33c1d714dcd9095e3992a5e`); no M commit is available to review yet.
  - `artifacts/L-action-packets-v1-report.md` is not present yet.
  - `artifacts/M-domain-graph-adapter-report.md` is not present yet.
- Unblocked review:
  - Reviewed L commit `7041c49b547e8eb8cc657305281907d25f917655` and report `artifacts/L-action-packets-v1-report.md`.
  - Reviewed M commit `8ddbe37edc43ee7aca989671c7b9946f5ce22836` and report `artifacts/M-domain-graph-adapter-report.md`.
  - L source review: PASS. The committed resource defines all six required packet families, sets root and per-packet non-execution semantics, includes PII profiles and forbidden fields, and has validator checks for required packet types, known source refs, workflow states, route-decision linkage, direct execution flags, debtor-contact payload fields, filing destination fields, and recursive forbidden keys.
  - L evidence review: PASS. `task-8-action-packet-validator.txt` reports `PASS action_packets recova-debt-collection-action-packets@v1.0.0 packet_types=6 required_inputs=42 source_refs=22`; failure evidence rejects `direct_execution_allowed`, non-advisory semantics, `filing_destination`, and `debtor_contact_payload`; focused pytest reports 4 passed; domain regression reports 36 passed; basedpyright reports 0 errors/0 warnings; size gate max is 222 pure LOC.
  - M source review: PASS. The adapter is additive and narrow, preserves `debtor_graph_id`, `graph_snapshot_id`, `source_bundle_hash`, fact IDs/source refs, legacy route IDs/refs, v1 route/source projections, governance handles, non-execution semantics, and PII profile; it rejects missing/placeholder fact source refs and unsupported explicit claim identity; tests assert v0 graph JSON remains unchanged after adaptation.
  - M evidence review: PASS. Focused pytest reports 7 passed; happy evidence includes claim root, source bundle hash, graph snapshot id, v0 route refs, v1 route/source projection, and `raw_text_included=false`; failure evidence covers `missing_source_ref` and `unsupported_claim_identity`; basedpyright reports 0 errors/0 warnings; size gate max is 210 pure LOC.
  - Source/resource/test PII/path review: PASS. Refined scan over merged changed files found no local source paths, temp paths, manual archive path, RRN-like values, or phone-like values in reviewed production/test/resource files. Routine command evidence contains execution worktree paths in pytest/isolation transcripts; I treated those as non-production evidence context and excluded only those known transcript lines from the refined safety gate.

## Post-Implementation Verification

Temporary merge simulation used a disposable worktree from `fb36cbe8e2601e04e33c1d714dcd9095e3992a5e` and merged `7041c49b` plus `8ddbe37e` without committing.

- Merge simulation: PASS. `git merge --no-ff --no-commit 7041c49b 8ddbe37e` reported automatic merge success.
- Todo 8 validator: PASS. `/opt/homebrew/bin/python3 scripts/legal_ontology/validate_action_packets_v1.py ...` reported `packet_types=6 required_inputs=42 source_refs=22`.
- Focused tests and MCP compatibility: PASS. `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_action_packets_v1.py tests/unit/legal_ontology/test_domain_graph_adapter_v1.py tests/unit/legal_ontology/test_debtor_context.py tests/unit/legal_ontology/test_mcp_domain_tools.py tests/unit/legal_ontology/test_mcp_debtor_context_tools.py tests/integration/legal_ontology/test_mcp_tools.py -q --no-header --no-summary` collected 25 tests and all passed.
- Python compile: PASS for all L/M changed Python files.
- Type check: PASS. `basedpyright` on all L/M changed Python/test files reported `0 errors, 0 warnings, 0 notes`.
- JSON parse: PASS for the action-packet resource, Todo 8 failure evidence, Todo 10 happy evidence, and Todo 10 failure evidence.
- Diff checks: PASS. `git diff --check HEAD` and `git diff --cached --check` reported no issues.
- Refined changed-file PII/path scan: PASS.

## Verdicts

L / Todo 8: ACCEPTED
M / Todo 10: ACCEPTED
Wave 3b: ACCEPTED
