# D Wave 1 Contract Review

Generated: 2026-07-07 01:27:37 KST
Reviewer: D / wave1-review
Scope: Read-only review of Todos 1-3 for `debt-collection-domain-ontology-v1`.

## Isolation Proof

- Worktree: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/team-8953292e/worktrees/D`
- Branch: `team/team-8953292e/D`
- `git rev-parse --show-toplevel`: D worktree path above
- `git status --short`: clean
- Current wave branches: A, B, C, and D all at base commit `89fff27f docs(legal-domain): plan claim ontology v1`
- Artifact directory scan: no A/B/C deliverable artifacts were present at initial review time
- Write scope used by D: this artifact only

## Source Material Read

- Team guide: `.omo/teams/team-8953292e/guide.md`
- Team state: `.omo/teams/team-8953292e/team.json`
- Plan: `.omo/plans/debt-collection-domain-ontology-v1.md`, Todos 1-3 controlling review scope
- Current compatibility references in D worktree:
  - `trustgraph_legal/mcp_domain.py`
  - `tests/unit/legal_ontology/test_mcp_domain_tools.py`
  - `tests/unit/legal_ontology/test_mcp_debtor_context_tools.py`
  - `trustgraph_legal/debtor_context_types.py`
  - `scripts/legal_ontology/validate_routes.py`

## Baseline Contract Facts

- Existing MCP compatibility is a hard regression gate. Current D worktree exposes 21 tools: the original 16 debt-collection tools first, followed by the five debtor-graph tools in this order: `assemble_debtor_documents`, `build_debtor_context_graph`, `get_debtor_graph_snapshot`, `list_debtor_route_candidates`, `explain_debtor_route_candidate`.
- `DebtorGraphPayload.to_json()` currently emits `schema_version`, `graph_snapshot_id`, nested `graph_snapshot`, graph sections, and `pii_profile` with raw/source text excluded.
- `FactAssertion` currently rejects missing and placeholder `source_refs` at construction time.
- Current route validator shape is `validate_routes.py <routes.json> <legal-sources.json>` and verifies nonempty route/source references, advisory semantics, and source ID linkage.
- Wave 1 must preserve the root boundary: `Claim` / `Receivable` is the ontology v1 conceptual root; `DebtorContextGraph` remains runtime memory root. Wave 1 may prepare handles for a later adapter, but must not alter debtor identity merge rules or v0 graph snapshot behavior.

## Review Checklist

### Cross-Cutting Gates

- New v1 resource files are additive. v0 resources are read-only references unless a Todo explicitly says otherwise.
- Evidence and reports must not contain raw manual prose, raw OCR text, resident-registration-number patterns, phone/account-like values, or local sensitive source paths.
- Deterministic tests must not call the live Korean-law MCP. Live lookup belongs only in execution evidence, then must be frozen into curated JSON.
- Legal temporal metadata must include explicit evaluation date policy and effective-date metadata. A record without a reliable effective date must be marked for review rather than guessed.
- Validators must own both happy path and failure path coverage for each Todo's resource or output.
- Existing MCP tests that assert the 21-tool order should remain untouched and passing.

### Todo 1: Manual Inventory / Candidate Extractor

Expected files or evidence:
- `scripts/legal_ontology/*manual*inventory*` or equivalent small extractor under `scripts/legal_ontology/`
- `tests/unit/legal_ontology/test_domain_manual_inventory.py`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-1-manual-inventory.json`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-1-manual-inventory-failure.txt`
- `artifacts/A-manual-inventory-report.md`

Accept if:
- Inventory is summary-only and contains counts for route, workflow, legal, finance, and action-packet candidates.
- Output does not include full body/prose text fields or the source manual path.
- Source references are redacted or abstracted enough for evidence sharing.
- Failure scenario for missing/invalid manual path exits with a controlled error and no sensitive path echo.
- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_domain_manual_inventory.py -q` passes.
- `python3 -m json.tool .omo/evidence/debt-collection-domain-ontology-v1/task-1-manual-inventory.json` passes.

Block if:
- Inventory copies manual paragraphs, raw identifiers, source paths, or OCR-like body text.
- Candidate extraction produces unbounded blobs instead of typed summary handles.
- Tests depend on the external manual being present without a controlled failure case.

### Todo 2: Claim-Centered Ontology v1

Expected files or evidence:
- `resources/ontologies/recova-debt-collection-v1.json`
- `scripts/legal_ontology/validate_domain_ontology_v1.py` or a clearly version-aware extension
- `tests/unit/legal_ontology/test_domain_ontology_v1.py`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-2-ontology-validator.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-2-ontology-validator-failure.txt`
- `artifacts/B-ontology-contract-report.md`

Accept if:
- `Claim` / `Receivable` is explicit root and links to debtor identity, creditor/assignee, guarantee/surety, case packet, documents/evidence, enforcement title, service/finality/execution clause, limitation, ledger facts, asset hints, route candidates, workflow states, StopGates, action packets, and governance records.
- Existing v0 public IDs are preserved or aliased; no silent public ID rename.
- Resource version is v1 and does not rewrite `resources/ontologies/recova-debt-collection.json`.
- Validator prints a PASS line with counts and root/edge confirmation.
- Failure fixture removing the root exits nonzero.
- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_domain_ontology_v1.py -q` passes.

Block if:
- Debtor becomes the ontology v1 root or `DebtorContextGraph` is redefined as the ontology root.
- Todo 2 changes debtor graph runtime identity or snapshot machinery.
- The ontology is a large unvalidated JSON blob without root/edge failure coverage.

### Todo 3: Curated Korean-Law Domain Sources v1

Expected files or evidence:
- `resources/legal_rules/debt_collection_domain_sources_v1.json`
- Source validator script or clearly version-aware existing validator
- `tests/unit/legal_ontology/test_domain_sources_v1.py`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-3-korean-law-source-map.json`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-3-source-validator.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-3-source-validator-failure.txt`
- `artifacts/C-legal-sources-report.md`

Accept if:
- Each source has stable `source_id`, law/source name, law ID/MST/article when available, effective date metadata, retrieved-at metadata, retrieval status, review status, source axis, usage links, and source ref.
- Resource-level or record-level evaluation date is explicit and tested.
- Ambiguous or unavailable legal lookups are recorded as candidates with `needs_legal_review`, not silently invented.
- Validator proves no Todo 3 route/workflow/StopGate source ref points to a missing `source_id`.
- Deterministic tests use only frozen JSON/resources, not live Korean-law MCP.
- `python3 -m json.tool resources/legal_rules/debt_collection_domain_sources_v1.json` passes.
- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_domain_sources_v1.py -q` passes.

Block if:
- Legal authority is guessed without retrieval/review metadata.
- Live Korean-law MCP calls appear in tests or import-time validator paths.
- Legal source evidence includes raw manual prose, local source paths, or raw personal data.

## Current Verdicts

| Slice | Status | Reason |
| --- | --- | --- |
| A / Todo 1 | Pending | No A artifact or branch delta available yet. |
| B / Todo 2 | Pending | No B artifact or branch delta available yet. |
| C / Todo 3 | Pending | No C artifact or branch delta available yet. |

## Peer Status Observed

- A thread `codex://threads/019f383e-6286-7550-add2-1abaeee11ed1` is in progress. It has red tests and is implementing the Todo 1 extractor, but branch `team/team-8953292e/A` still points at base commit `89fff27f` and there is no A artifact yet.
- B thread `codex://threads/019f383e-70d4-7170-9e27-c47c12559f73` is in progress. It has red tests and is implementing the Todo 2 v1 ontology resource/validator, but branch `team/team-8953292e/B` still points at base commit `89fff27f` and there is no B artifact yet.
- C thread `codex://threads/019f383e-8170-75f2-bc3e-e1ce117524f6` is in progress. It has live Korean-law discovery and direct law-text lookups underway for Todo 3 evidence, including an explicit note to separate local evaluation date from MCP lookup baseline, but branch `team/team-8953292e/C` still points at base commit `89fff27f` and there is no C artifact yet.
- D has not inspected peer uncommitted worktree files. Review will start from committed branch deltas and artifact files.

## Planned Focused Verification After A/B/C Land

- Inspect each peer branch diff read-only with `git diff 89fff27f..<branch> -- <owned paths>`.
- Run each Todo's focused pytest exactly as specified where dependencies are present.
- Run JSON validation over new resource and evidence JSON files.
- Run targeted PII/path scans over changed source/tests/resources/evidence/artifacts for full manual path, local worktree paths, resident-registration-number patterns, phone-like patterns, account-like patterns, and raw body-text field names.
- Re-run MCP compatibility tests if any source touches `trustgraph_legal/mcp_domain.py`, `trustgraph-mcp/`, or existing MCP tests.
- Update this artifact with accepted/blocked verdicts, exact commands, and evidence paths.

## Post-Implementation Review

Reviewed: 2026-07-07 01:53:04 KST
Base commit: `89fff27f docs(legal-domain): plan claim ontology v1`

### Reviewed Inputs

- A manual-inventory: `b96e92f3 test(legal-domain): inventory collection manual candidates`
- B ontology-contract: `69313f61 feat(legal-domain): add claim-centered ontology v1`
- C legal-sources: `4b39b7a5 feat(legal-domain): curate domain legal sources v1`
- Reports:
  - `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/team-8953292e/artifacts/A-manual-inventory-report.md`
  - `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/team-8953292e/artifacts/B-ontology-contract-report.md`
  - `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/team-8953292e/artifacts/C-legal-sources-report.md`

### Final Verdicts

| Slice | Verdict | Reason |
| --- | --- | --- |
| A / Todo 1 | ACCEPTED | Summary-only inventory contract passes; focused test, JSON parse, full basedpyright, diff check, and PII/path scan are clean. |
| B / Todo 2 | ACCEPTED | Claim/Receivable-rooted v1 ontology and validator pass contract tests; v0 resources and DebtorContextGraph runtime code are untouched. |
| C / Todo 3 | ACCEPTED | Domain source v1 resource has frozen Korean-law evidence, deterministic offline tests, explicit evaluation/effective metadata, and 3 legacy bundle refs marked `needs_legal_review`. |
| Wave 1 integration | BLOCKED | A and C both add `scripts/legal_ontology/__init__.py` with different contents, producing an add/add merge conflict before A+B+C can be integrated together. |

### Commands Run By D

- `git show --stat --oneline --decorate --name-status b96e92f3`
- `git show --stat --oneline --decorate --name-status 69313f61`
- `git show --stat --oneline --decorate --name-status 4b39b7a5`
- `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_domain_manual_inventory.py -q -p no:cacheprovider`
- `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_domain_ontology_v1.py -q -p no:cacheprovider`
- `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_domain_sources_v1.py -q -p no:cacheprovider`
- `/opt/homebrew/bin/python3 -m json.tool .omo/evidence/debt-collection-domain-ontology-v1/task-1-manual-inventory.json`
- `/opt/homebrew/bin/python3 -m json.tool resources/ontologies/recova-debt-collection-v1.json`
- `/opt/homebrew/bin/python3 scripts/legal_ontology/validate_domain_ontology_v1.py resources/ontologies/recova-debt-collection-v1.json`
- `/opt/homebrew/bin/python3 -m json.tool resources/legal_rules/debt_collection_domain_sources_v1.json`
- `/opt/homebrew/bin/python3 scripts/legal_ontology/validate_domain_sources_v1.py resources/legal_rules/debt_collection_domain_sources_v1.json resources/legal_routes/debt_collection_routes_v0.json resources/legal_rules/debt_collection_stopgate_v0.json`
- `git diff --check 89fff27f..b96e92f3`
- `git diff --check 89fff27f..69313f61`
- `git diff --check 89fff27f..4b39b7a5`
- `git grep` PII/path scans over each commit's changed source/test/resource/evidence paths
- `git merge-tree 89fff27f b96e92f3 4b39b7a5`
- `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_domain_tools.py tests/unit/legal_ontology/test_mcp_debtor_context_tools.py -q -p no:cacheprovider`
- `basedpyright` over A changed Python/test files
- `basedpyright --level error` over B changed Python/test files
- `basedpyright --level error` over C changed Python/test files

### Verification Results

- Todo 1 focused pytest: PASS, 2 tests.
- Todo 2 focused pytest: PASS, 3 tests.
- Todo 3 focused pytest: PASS, 3 tests.
- Existing MCP compatibility tests from D: PASS, 11 tests. The 21-tool order remains untouched because A/B/C do not modify `trustgraph_legal`, `trustgraph-mcp`, or existing MCP tests.
- JSON parse checks: PASS for Todo 1 inventory evidence, Todo 2 ontology resource, and Todo 3 domain source resource.
- Todo 2 validator: `PASS ontology recova-debt-collection-v1 root=Claim/Receivable classes=22 objectProperties=20 datatypeProperties=11 requiredEdges=20`.
- Todo 3 validator: `PASS domain_sources recova-debt-collection-domain-sources@v1.0.0 legal_sources=21 routes=18 route_source_refs=64 stopgates=12 stopgate_source_refs=12 workflow_refs=12 workflow_source_refs=29`.
- PII/path scans: PASS for B and C. A scan only matched `body_text` inside `tests/unit/legal_ontology/test_domain_manual_inventory.py` as a forbidden-key test denylist; no emitted evidence/manual path/phone/RRN/account pattern was found.
- Worktree status after D verification: A, B, C, and D worktrees clean.

### A / Todo 1 Findings

- Owned-path boundary: PASS. Changed files are the manual inventory scripts/tests plus task-1 evidence and a package marker.
- Manual inventory output: PASS. `task-1-manual-inventory.json` has a summary `source` object with `source_paths_included=false`, and `pii_profile.raw_text_included=false`, `source_text_included=false`, `matched_text_included=false`.
- Downstream usefulness: PASS. Counts include 115 headings, 66 route candidates, 12 workflow candidates, 9 fact handles, 6 risk/blocker candidates, 4 legal-source candidates, 8 finance candidates, 5 scoring fields, and 6 action-packet candidates.
- Non-execution semantics: PASS. Route/action candidates are advisory/draft-only and direct execution is forbidden.
- Size/typing risk: WARN. `scripts/legal_ontology/domain_manual_inventory.py` is 236 pure LOC, below the 250 ceiling but in the warning band.

### B / Todo 2 Findings

- Owned-path boundary: PASS. Changed files are the v1 ontology resource, validator, focused test, and task-2 evidence only.
- Claim/Receivable root: PASS. Resource metadata declares `root: Claim/Receivable`, `runtime_memory_root: DebtorContextGraph`, and `non_execution_semantics: descriptive_only`; classes `claim` and `receivable` carry root/root-alias roles.
- DebtorContextGraph runtime behavior: PASS. No changes touch `trustgraph_legal/debtor_context_types.py`, `trustgraph_legal/mcp_domain.py`, `trustgraph-mcp`, or v0 ontology/route/source resources.
- Validator failure coverage: PASS. Missing `claim` root and missing required edge both fail.
- Size/typing risk: WARN. `scripts/legal_ontology/validate_domain_ontology_v1.py` is 222 pure LOC. Full `basedpyright` reports 11 warnings around JSON `Any` flow and deprecated `typing.Sequence`; `basedpyright --level error` reports 0 errors.

### C / Todo 3 Findings

- Owned-path boundary: PASS. Changed files are the domain source v1 resource, validator/common helper, focused test, task-3 evidence, and a package marker.
- Korean-law evidence: PASS. Evidence records Korean-law MCP availability, exact-match searches, two long-title search API 404s resolved by direct `law_id`/`mst` article lookups, and 18 article-level records verified by `get_law_text`.
- Deterministic offline tests: PASS. Test/resource paths do not call live Korean-law tools; the evidence explicitly records `deterministic_tests_use_live_mcp=false`.
- Temporal metadata: PASS. Resource has `evaluation_date: 2026-07-07`; verified records include effective dates, retrieved-at timestamps, retrieval status, review status, and lookup basis date.
- Legacy bundle handling: PASS. Three v0/domain bundle IDs are preserved for compatibility and marked `needs_legal_review` instead of being represented as exact article authority.
- Size/typing risk: WARN. `scripts/legal_ontology/validate_domain_sources_v1.py` is 239 pure LOC. Full `basedpyright` reports 2 `Any` warnings; `basedpyright --level error` reports 0 errors.

### Integration Findings

- BLOCKING: `scripts/legal_ontology/__init__.py` has an add/add merge conflict between A and C.
  - A content: `__all__: list[str] = []`
  - C content: blank file
  - `git merge-tree 89fff27f b96e92f3 4b39b7a5` reports `added in both` with conflict markers for that file.
  - Recommended integration resolution: keep A's typed package marker (`__all__: list[str] = []`) unless the leader prefers a blank package marker, then rerun A/C focused tests and MCP compatibility tests after merge.
- Non-blocking: B and C validators are near the 250 pure-LOC ceiling and should be split before future expansion.
- Non-blocking: B/C full basedpyright warnings should be cleaned up when integrating or before Wave 2 extends these validators, especially the untyped `json.load` flow.

### Overall Review Decision

Wave 1 implementation is contract-sound at the individual Todo level, but integration is not yet accepted because the shared `scripts/legal_ontology/__init__.py` add/add conflict must be resolved before the branches can be combined.

## Re-Review After A Package Marker Fix

Reviewed: 2026-07-07 01:57:13 KST
A latest commit: `a08ba68f fix(legal-domain): align legal ontology package marker`

### Re-Review Scope

- Re-checked only the prior Wave 1 integration blocker involving `scripts/legal_ontology/__init__.py`.
- Did not re-open the already accepted Todo 1-3 functional contracts.
- Did not edit production/source/test/resource files.

### Commands Run By D

- `git show --oneline --no-patch a08ba68f`
- `git branch --contains a08ba68f`
- `git show a08ba68f:scripts/legal_ontology/__init__.py | wc -c`
- `git show 4b39b7a5:scripts/legal_ontology/__init__.py | wc -c`
- `git rev-parse a08ba68f:scripts/legal_ontology/__init__.py`
- `git rev-parse 4b39b7a5:scripts/legal_ontology/__init__.py`
- `git show a08ba68f:scripts/legal_ontology/__init__.py | od -An -tx1`
- `git show 4b39b7a5:scripts/legal_ontology/__init__.py | od -An -tx1`
- `git merge-tree 89fff27f a08ba68f 4b39b7a5`
- Temporary octopus merge simulation in `/tmp/d-wave1-merge-sim`: `git merge --no-commit --no-ff a08ba68f 69313f61 4b39b7a5`

### Re-Review Results

- A latest package marker is 0 bytes:
  - blob `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391`
  - byte dump is empty
- C package marker is 1 byte:
  - blob `8b137891791fe96927ad78e64b0aad7bded08bdc`
  - byte dump: `0a`
- `git merge-tree 89fff27f a08ba68f 4b39b7a5` still reports `added in both` for `scripts/legal_ontology/__init__.py`.
- The temporary octopus merge of A latest + B + C still exits nonzero:
  - `Added scripts/legal_ontology/__init__.py in both, but differently.`
  - `ERROR: content conflict in scripts/legal_ontology/__init__.py`
  - status shows `AA scripts/legal_ontology/__init__.py`
- The temporary worktree was removed after the simulation. D worktree stayed clean.

### Final Integration Verdict

Wave 1 integration remains BLOCKED.

The A fix changed the file from a typed package marker to a 0-byte file, but it still does not match C's one-newline package marker. Because the base commit has no `scripts/legal_ontology/__init__.py`, Git still treats A and C as an add/add conflict.

Recommended final fix: make A and C byte-identical. Either both should be truly 0-byte, or both should contain exactly one newline byte. After that, rerun the same merge simulation before accepting Wave 1 integration.

## Final Re-Review After Byte-Identical Marker Fix

Reviewed: 2026-07-07 02:02:20 KST
A latest commit: `e3ef0d3c fix(legal-domain): match package marker bytes`

### Final Re-Review Scope

- Re-checked only the prior Wave 1 integration blocker involving `scripts/legal_ontology/__init__.py`.
- Did not re-open the already accepted Todo 1-3 functional contracts.
- Did not edit production/source/test/resource files.

### Commands Run By D

- `git show --oneline --no-patch e3ef0d3c`
- `git branch --contains e3ef0d3c`
- `git show e3ef0d3c:scripts/legal_ontology/__init__.py | wc -c`
- `git show 4b39b7a5:scripts/legal_ontology/__init__.py | wc -c`
- `git rev-parse e3ef0d3c:scripts/legal_ontology/__init__.py`
- `git rev-parse 4b39b7a5:scripts/legal_ontology/__init__.py`
- `git show e3ef0d3c:scripts/legal_ontology/__init__.py | od -An -tx1`
- `git show 4b39b7a5:scripts/legal_ontology/__init__.py | od -An -tx1`
- `git merge-tree 89fff27f e3ef0d3c 4b39b7a5`
- `git merge-tree 89fff27f e3ef0d3c 69313f61`
- `git merge-tree 89fff27f 69313f61 4b39b7a5`
- Temporary octopus merge simulation in `/tmp/d-wave1-final-merge-sim`: `git merge --no-commit --no-ff e3ef0d3c 69313f61 4b39b7a5`
- Temporary merged-tree regression in `/tmp/d-wave1-final-qa`: focused Wave 1 tests plus MCP compatibility tests

### Final Re-Review Results

- A latest package marker is 1 byte:
  - blob `8b137891791fe96927ad78e64b0aad7bded08bdc`
  - byte dump: `0a`
- C package marker is 1 byte:
  - blob `8b137891791fe96927ad78e64b0aad7bded08bdc`
  - byte dump: `0a`
- `git merge-tree 89fff27f e3ef0d3c 4b39b7a5` exits 0 and no longer reports `added in both`, `CONFLICT`, or conflict markers for `scripts/legal_ontology/__init__.py`.
- Pairwise merge-tree checks for A latest + B and B + C also exit 0 without conflict markers.
- Temporary octopus merge of A latest + B + C from base `89fff27f` exits 0:
  - `Automatic merge went well; stopped before committing as requested`
  - merged status shows `A scripts/legal_ontology/__init__.py`, not `AA`
  - merged marker remains 1 byte
- Temporary merged-tree regression passed:
  - `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_domain_manual_inventory.py tests/unit/legal_ontology/test_domain_ontology_v1.py tests/unit/legal_ontology/test_domain_sources_v1.py tests/unit/legal_ontology/test_mcp_domain_tools.py tests/unit/legal_ontology/test_mcp_debtor_context_tools.py -q -p no:cacheprovider`
  - Result: 19 passed
  - `git diff --check` in the merged tree exited 0
- Temporary worktrees were removed after verification. D worktree stayed clean.

### Final Integration Verdict

Wave 1 integration is ACCEPTED.

The prior add/add conflict is resolved because A and C now carry byte-identical `scripts/legal_ontology/__init__.py` blobs. The combined A latest + B + C merge succeeds and the focused merged-tree regression passes.

Residual risks remain non-blocking and unchanged from the earlier post-implementation review:
- A main script and B/C validators are near the 250 pure-LOC ceiling; split before future expansion.
- B/C full basedpyright warnings around JSON `Any` flow should be cleaned up before validator expansion, although error-level checks were clean in the prior review.
