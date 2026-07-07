# L Route Snapshot Review

Status: TODO 7 AND TODO 9 ACCEPTED FOR L CONTRACT REVIEW

Member: L / route-snapshot-review
Scope: read-only contract review artifact for Todo 7 snapshot semantics and Todo 9 StopGate/legal-source route semantics. No production files edited.

## Inputs Reviewed

- Team plan: `/Users/cosmos/dev/ontology/trustgraph/.omo/plans/debtor-context-graph-v0.md`
- Team state and guide under `.omo/teams/debtor-context-graph-v0-20260706/`
- L worktree: branch `team/debtor-context-graph-v0-20260706/L`, HEAD `b6ca1f60`
- J worktree: branch `team/debtor-context-graph-v0-20260706/J`, HEAD `b6ca1f60`; no Todo 7 implementation commits visible at review time
- K worktree: branch `team/debtor-context-graph-v0-20260706/K`, HEAD `27ed6cb1`; no Todo 9 implementation commits visible at review time
- Current master: `27ed6cb1`, which integrates H follow-up `6ee22757`
- Prior reports:
  - `artifacts/I-debtor-graph-contract-review.md`
  - `artifacts/H-debtor-graph-builder-report.md`
  - `artifacts/E-route-matcher-report.md`
  - `artifacts/B-route-sources-report.md`

## Current Disposition

No J/K implementation code is available yet, so this is an acceptance checklist and risk register, not an approval or rejection of Todo 7/9.

The earlier H route-status blocker is closed on master. H now emits clear route facts with `review_status="verified"` in `trustgraph_legal/debtor_context_builder.py:195`, and the route matcher already clears `verified` via `CLEAR_FACT_REVIEW_STATUSES` in `trustgraph_legal/route_candidates.py:11`.

E alternate commit `0465cc6e` broadens route clearing to accept `accepted`, but it is intentionally unintegrated. K owns whether to adopt any `accepted` semantics later, with explicit tests and leader acceptance. L should not treat that alternate as the default contract.

## Remaining Todo 7 Risks

### 1. Snapshot ids are still source-bundle-only

Current H/master still builds `graph_snapshot_id` from only `source_bundle_hash`:

- `trustgraph_legal/debtor_context_builder.py:86`
- `trustgraph_legal/debtor_context_builder.py:93`
- `trustgraph_legal/debtor_context_builder.py:96`

This is deterministic, but too narrow for replay/diff semantics. Todo 7 must ensure semantic graph changes are visible even when page hashes do not change.

Minimum acceptance:

- Same payload, same versions, same facts, same routes -> same semantic snapshot digest/id.
- Changing `source_bundle_hash` -> changed snapshot digest/id and explicit diff.
- Changing a fact's `object_value`, `confidence`, `review_status`, source hash/ref, chunk/span, extractor version, or ontology version -> changed semantic digest and `changed_facts`.
- Changing route candidate status, missing/blocking facts, legal source refs, confidence, or `no_direct_execution` -> changed semantic digest and `changed_routes`.
- Changing extractor, ontology, route, or legal rule-source versions -> changed semantic digest and version diff.
- `generated_at` must be excluded from deterministic identity or injected/frozen explicitly.
- If legacy `graph_snapshot_id` remains equal while the semantic digest differs, Todo 7 should report a snapshot-id collision/risk instead of treating the snapshots as identical.

### 2. Diff coverage must compare content, not ids only

`GraphSnapshot` carries `fact_assertion_ids`, `route_candidate_ids`, and versions in `trustgraph_legal/debtor_context_types.py:200`, but fact ids alone are not enough. H fact ids are derived from predicate/object/source/document, not from confidence, review status, versions, or line spans.

Minimum acceptance:

- `added_facts` / `removed_facts` by `fact_id`.
- `changed_facts` by canonicalized fact JSON for shared `fact_id`.
- `added_routes` / `removed_routes` by `route_id`.
- `changed_routes` by canonicalized route JSON for shared `route_id`.
- `changed_versions` for extractor, ontology, route, and legal rule-source metadata.
- `changed_source_bundle_hash` as a first-class field.
- No raw OCR text comparison or persistence.

### 3. Provenance validation must be stricter than `FactAssertion`

`FactAssertion.__post_init__()` rejects empty and placeholder `source_refs` in `trustgraph_legal/debtor_context_types.py:140`, but it does not validate the rest of the provenance envelope.

Minimum acceptance:

- Every non-derived material fact requires non-placeholder `source_refs`, `source_document_id`, `source_hash`, `chunk_id`, `line_start`, `line_end`, `extractor_version`, `ontology_version`, confidence, and review status.
- `source_hash` must be hash-shaped; `line_end >= line_start`; line spans should be positive.
- Placeholder values such as `missing`, `unknown`, `todo`, `placeholder:*`, or bracketed placeholders fail validation for provenance fields.
- Derived facts still need source refs or source fact ids explaining the derivation input.
- Existing StopGate placeholder provenance behavior must be treated as invalid evidence, not silently accepted.

### 4. PII scan must handle hash-shaped false positives safely

The plan regex still matches a phone-shaped numeric substring inside `source_bundle_hash` in task-6 failure evidence. In L's local check, the hit was limited to `source_bundle_hash` JSON values in `.omo/evidence/debtor-context-graph-v0/task-6-debtor-graph-failure.json`.

Minimum acceptance:

- Do not print matched hash values in human reports when classifying false positives.
- Add a structured PII gate that parses JSON and allowlists hash-only fields such as `source_hash`, `source_bundle_hash`, and hash-suffixed ids.
- Any match outside hash-only fields remains a failure.
- Any `raw_text`, `source_text`, `excerpt`, resident-registration-number pattern, phone number, or account-like identifier outside the hash allowlist fails.
- Evidence should say either `NO_FINDINGS` or `HASH_ONLY_FALSE_POSITIVES` with paths/counts only, not sensitive values.

## Remaining Todo 9 Risks

### 1. StopGate reason codes must bridge into route blockers

Current route matching reads StopGate/review reason codes into `review_handles` in `trustgraph_legal/route_candidates.py:153`, but a route only blocks when one of its `blocking_fact_handles` exactly matches a fact handle or review handle in `trustgraph_legal/route_candidates.py:102`.

Route resources often block on fact handles, while StopGate output exposes reason codes. Example: `bank_account_attachment` blocks on `insolvency_stay`, while the StopGate-style route uses `stay_or_discharge_detected`.

Minimum acceptance:

- A graph with `stop_gates=[{"reason_code": "stay_or_discharge_detected"}]` must put that reason code into affected collection route blockers even if no `insolvency_stay` fact exists.
- Route blockers should include StopGate reason codes, not only the lower-level fact handles.
- If K calls `evaluate_case_graph`, it must do so only for compatible case-packet shapes. If H `DebtorGraphPayload.case_packets` are not case-graph `entities` packets, K should consume provided `graph.stop_gates` or mark route evaluation `review_required` instead of pretending StopGate clearance.
- StopGate blockers must never produce direct execution permission.

### 2. Legal source metadata is not yet attached at runtime

Route resources contain only source ids at runtime today:

- `trustgraph_legal/route_candidates.py:90`
- `trustgraph_legal/route_candidates.py:130`

The legal source resource contains the required metadata: `law_id`, `mst`, `article`, `effective_date`, `retrieved_at`, `retrieval_status`, `review_status`, and `law_source_ref`.

Minimum acceptance:

- Todo 9 must load `resources/legal_rules/debt_collection_route_sources_v0.json` or an injected equivalent during route evaluation.
- Every emitted legal source ref must be backed by metadata containing lawId/law_id, MST/mst, article, effective date, retrieval status, and review status.
- Draft, deprecated, future-only, missing, or unretrieved legal sources cannot clear a route to `possible`; they should produce `review_required`.
- Tests should include an approved-source happy route and a temp draft/review/future source failure route.
- If K keeps `RouteCandidate.legal_source_refs` as strings, the evidence must still prove those strings were resolved to metadata. If K wants structured legal-source objects in route output, coordinate a schema-owned change instead of silently changing the shared type.

### 3. No direct-execution claims

B resources already carry `no_direct_execution=true`, `direct_execution_allowed=false`, and `execution_semantics=none_advisory_only`. E route candidates also emit `no_direct_execution=True`.

Minimum acceptance:

- Todo 9 must preserve advisory-only semantics for every route status.
- Legal source approval can clear a review blocker, but it must not change `no_direct_execution`.
- Evidence should include a route with approved legal refs and still show advisory-only output.

### 4. H compatibility is resolved via `verified`

K should treat master/H as the current contract: H-derived clear facts are `verified`. Do not re-open the old `accepted` blocker unless K intentionally chooses to support `accepted` as a broader route matcher rule.

Minimum acceptance:

- A graph built from H/master facts with `verified` route-handle facts should keep `bank_account_attachment` non-missing and possible when no StopGate/legal-source blockers apply.
- If `accepted` support is added, it needs an explicit K-owned regression test and leader acknowledgement because E `0465cc6e` is not integrated by default.

## Python Size And Type Risks

Measured in L worktree:

- `trustgraph_legal/debtor_context_types.py`: 249 pure LOC.
- `trustgraph_legal/debtor_context_builder.py`: 236 pure LOC.
- `trustgraph_legal/route_candidates.py`: 176 pure LOC.

Implications:

- J/K should not add to `debtor_context_types.py` without a schema-owner decision; it is already at the ceiling.
- J should keep snapshot helpers in `trustgraph_legal/debtor_snapshots.py`.
- K has room in `route_candidates.py`, but StopGate/legal-source loading can quickly make it multi-responsibility. Split resource/source-status helpers before crossing the 250 LOC ceiling.
- Avoid broad dict plumbing in new code; parse JSON resources into typed/frozen values at the boundary.

## Required J/K Evidence Before Acceptance

Todo 7:

- Focused pytest for `tests/unit/legal_ontology/test_debtor_snapshots.py`.
- Happy snapshot diff JSON proving deterministic same-input behavior and semantic change detection.
- Failure evidence for missing/placeholder provenance.
- PII/hash gate evidence that distinguishes real PII from hash-only false positives without printing values.
- `py_compile`, type/LSP check if available, and `git diff --check`.

Todo 9:

- Focused pytest for `tests/unit/legal_ontology/test_route_candidates.py tests/unit/legal_ontology/test_stop_gates.py`.
- Happy route evidence with approved legal source metadata and advisory-only output.
- Failure route evidence where draft/deprecated/future legal source status yields `review_required`.
- StopGate reason-code blocker evidence where the reason code itself appears in route blockers.
- PII scan, `py_compile`, type/LSP check if available, and `git diff --check`.

## Review Verdict

Ready for J/K to implement against this checklist.

No Todo 7 or Todo 9 source approval is possible yet because J has no implementation commit and K has no Todo 9 implementation commit at this review point. The accepted-status route blocker is closed on master through H `verified` facts; remaining review focus is J/K: snapshot semantic digest/version coverage, provenance validation, StopGate/legal-source runtime semantics, and hash-shaped PII scan handling.

## Live In-Progress Review: J Todo 7 Draft

Observed after the first artifact draft:

- J has uncommitted `trustgraph_legal/debtor_snapshots.py`.
- J has uncommitted `tests/unit/legal_ontology/test_debtor_snapshots.py`.
- No J commit/evidence is available yet, so this is a draft review only.

Positive coverage in the visible draft:

- `replay_snapshot(...)` builds a semantic replay digest from source bundle hash, fact fingerprints, route fingerprints, and version fields.
- `diff_snapshots(...)` reports source bundle changes, added/removed/changed facts, added/removed/changed routes, and version changes.
- Tests cover stable replay ids, changed fact content, route status changes, legal rule-source version changes, and raw-text-field ignoring.
- The new module is 230 pure LOC, below the 250 LOC ceiling.

Open gaps before J acceptance:

1. Provenance validation is still too shallow.
   - Current draft only checks `source_refs`, `source_document_id`, `source_hash`, and `chunk_id`.
   - It does not validate placeholder values for `source_document_id`, `source_hash`, or `chunk_id`.
   - It does not validate `source_hash` shape, `line_start`, `line_end`, line ordering, `extractor_version`, `ontology_version`, confidence, or review status.
   - Add tests that mutate each required provenance field and assert deterministic issue codes.

2. Derived facts are skipped entirely.
   - `validate_snapshot_provenance(...)` skips `derived=True` facts before validating any derivation source.
   - Contract expectation: derived facts still need source refs or source fact ids explaining the derivation input.
   - Add either a derived-fact provenance contract or a specific issue code for derived facts lacking derivation evidence.

3. Snapshot-id collision/risk is not explicit.
   - J computes a replay id, which is good, but the diff does not explicitly report when legacy `graph_snapshot_id` is unchanged while semantic replay ids differ.
   - Add a collision/risk field or a test proving this case is visible in output.

4. PII/hash evidence gate is not yet present.
   - The draft ignores raw text fields during fingerprinting, but the required hash-shaped false-positive gate is not implemented in the visible J code.
   - J evidence should include `NO_FINDINGS` or `HASH_ONLY_FALSE_POSITIVES` with paths/counts only.

## Live In-Progress Review: K Todo 9 Draft

Observed after the first artifact draft:

- K has uncommitted edits to `trustgraph_legal/route_candidates.py`.
- K has uncommitted edits to `tests/unit/legal_ontology/test_route_candidates.py`.
- No K commit/evidence is available yet, so this is a draft review only.

Positive coverage in the visible draft:

- Loads `resources/legal_rules/debt_collection_route_sources_v0.json` through a `RouteLegalSource` value.
- Decorates route legal source refs with lawId, MST, article, and review status.
- Adds tests for approved metadata, StopGate reason-code blockers, and draft/deprecated/future-only legal source statuses.
- Preserves `no_direct_execution=True`.

Open gaps before K acceptance:

1. `route_candidates.py` is now at the file-size ceiling.
   - Measured draft size: 250 pure LOC.
   - Any further K edits should split legal-source catalog/status logic or StopGate bridge helpers before adding more lines.

2. StopGate bridging may be over-broad.
   - Current draft appends every StopGate reason code to every route unless already present as a template blocker.
   - This makes reason codes visible, but it may over-block unrelated routes.
   - K should either document this conservative v0 rule or map reason codes to affected route families explicitly.

3. H case-packet compatibility still needs a deliberate fallback.
   - Current draft calls `evaluate_case_graph(graph.to_json())` whenever `graph.case_packets` is non-empty.
   - H `DebtorGraphPayload.case_packets` are not guaranteed to be legacy case-graph packets with `entities`.
   - If K cannot evaluate a packet shape, it should consume `graph.stop_gates` or emit `review_required`, not silently treat the graph as StopGate-clear.

4. Legal-source status checks are incomplete.
   - The draft checks `review_status` markers, but not `retrieval_status` or `effective_date`.
   - Add tests for missing/unretrieved source metadata and future effective dates, or document why Todo 9 only gates review status.

5. Decorated string refs are a schema compromise.
   - Encoding `lawId`, `MST`, and `article` into `RouteCandidate.legal_source_refs` satisfies the current string-only schema without editing `debtor_context_types.py`.
   - It may surprise consumers expecting raw source ids.
   - If this approach stays, tests/evidence should prove raw source ids remain recoverable from the prefix and no direct-execution semantics changed. If structured legal-source output is preferred, coordinate a schema-owner change instead.

6. K has not broadened clear statuses to `accepted`.
   - This aligns with leader direction. Keep it that way unless K explicitly adopts `accepted` semantics with tests and leader approval.

## Follow-Up Review: J Commit `e9fcb007`

Status: TODO 7 ACCEPTED FOR L CONTRACT REVIEW

Reviewed J commit:

- `e9fcb007 feat(legal-graph): add debtor graph snapshot diffs`

Reviewed surface:

- `trustgraph_legal/debtor_snapshots.py`
- `tests/unit/legal_ontology/test_debtor_snapshots.py`
- `.omo/evidence/debtor-context-graph-v0/task-7-*`
- `artifacts/J-snapshot-diffs-report.md`

Verification L ran in J worktree:

- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_debtor_snapshots.py -q` -> 7 passed.
- `/opt/homebrew/bin/python3 -m py_compile trustgraph_legal/debtor_snapshots.py tests/unit/legal_ontology/test_debtor_snapshots.py` -> passed.
- `/Users/cosmos/.local/bin/basedpyright --level error trustgraph_legal/debtor_snapshots.py tests/unit/legal_ontology/test_debtor_snapshots.py` -> 0 errors.
- `/opt/homebrew/bin/python3 -m json.tool` over task-7 happy/failure evidence -> passed.
- `git diff --check e9fcb007^ e9fcb007` -> passed.
- Source size check: `trustgraph_legal/debtor_snapshots.py` 219 pure LOC; `tests/unit/legal_ontology/test_debtor_snapshots.py` 206 pure LOC.

Accepted coverage:

- Replay snapshot digest includes source bundle hash, fact fingerprints, route fingerprints, and version fields.
- Diff output reports source bundle changes, changed fact ids, changed route candidate ids, version changes, and `legacy_graph_snapshot_id_collision`.
- Provenance validation now covers missing/placeholder source refs, placeholder source document id, invalid source hash shape, placeholder chunk id, invalid line span, missing extractor version, placeholder ontology version, invalid confidence, and missing review status.
- Derived facts without source refs now require derivation evidence.
- Raw text-like fields are excluded from replay fingerprints.
- Task-7 PII evidence reports `HASH_ONLY_FALSE_POSITIVES` with paths/counts only and `matched_values_printed=false`.

Residual note:

- L's independent generic regex probe still finds one hash-shaped match in task-7 happy evidence, but it is confined to SHA-256-style snapshot metadata. This matches J's `HASH_ONLY_FALSE_POSITIVES` classification and is not a raw PII leak.

Final Todo 7 L verdict:

- J has closed the Todo 7 gaps previously listed by L.
- No blocking snapshot-id, provenance, raw-text, hash-only PII, type, focused-test, JSON, diff-check, or file-size issue remains from L's review.

## Follow-Up Review: K Commit `cb4ea60b`

Status: TODO 9 BEHAVIOR VERIFIED, BUT NEEDS COMPATIBILITY FIX BEFORE L ACCEPTANCE

Reviewed K commit:

- `cb4ea60b feat(legal-routes): attach stop gates and legal sources`

Reviewed surface:

- `trustgraph_legal/route_candidates.py`
- `tests/unit/legal_ontology/test_route_candidates.py`
- `.omo/evidence/debtor-context-graph-v0/task-9-*`
- `artifacts/K-route-stopgate-integration-report.md`

Verification L ran in K worktree:

- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_route_candidates.py tests/unit/legal_ontology/test_stop_gates.py tests/unit/legal_ontology/test_debtor_context.py -q` -> 23 passed.
- `/opt/homebrew/bin/python3 -m py_compile trustgraph_legal/route_candidates.py tests/unit/legal_ontology/test_route_candidates.py` -> passed.
- `/Users/cosmos/.local/bin/basedpyright --level error trustgraph_legal/route_candidates.py tests/unit/legal_ontology/test_route_candidates.py` -> 0 errors.
- `/opt/homebrew/bin/python3 -m json.tool` over task-9 happy/failure evidence -> passed.
- `git diff --check cb4ea60b^ cb4ea60b` -> passed.
- Source size check: `trustgraph_legal/route_candidates.py` 246 pure LOC; `tests/unit/legal_ontology/test_route_candidates.py` 227 pure LOC.
- PII evidence says `NO_FINDINGS`.

Behavior accepted if compatibility is fixed:

- Legal source refs are decorated with source id, lawId, MST, article, effective date, retrieval status, and review status while preserving `RouteCandidate.legal_source_refs` as strings.
- Legal source gating covers `review_status`, `retrieval_status`, and future `effective_date`.
- StopGate reason codes bridge into route blockers.
- StopGate bridge is no longer universal for title routes; title routes receive only global trust/provenance StopGate blockers.
- H-style non-legacy summary `case_packets` are not treated as StopGate-clear unless a compatible legacy `entities` packet shape exists.
- `accepted` remains out of `CLEAR_FACT_REVIEW_STATUSES`, preserving the leader's H-verified-fact disposition.
- `no_direct_execution=True` remains present in happy and failure route evidence.

Blocking finding:

1. Python import floor regression in `route_candidates.py`.
   - Evidence: `trustgraph_legal/route_candidates.py:7` imports `override` from `typing`, and `trustgraph_legal/route_candidates.py:31` uses `@override`.
   - The repo package metadata still contains multiple `requires-python = ">=3.8"` entries.
   - `/usr/bin/python3 --version` -> `Python 3.9.6`.
   - `/usr/bin/python3 - <<'PY'\nimport trustgraph_legal.route_candidates\nPY` fails with `ImportError: cannot import name 'override' from 'typing'`.
   - `py_compile` does not catch this because it compiles syntax without resolving the import.
   - Acceptance impact: Todo 9 route semantics are verified under `/opt/homebrew/bin/python3`, but the committed module cannot be imported on the advertised Python 3.8/3.9 floor.
   - Suggested fix: remove the `@override` decorator/import here, or import `override` from `typing_extensions` if that dependency is guaranteed for all supported runtimes, or explicitly raise the package Python floor with leader approval.

Warning-band note:

- `route_candidates.py` is 246 pure LOC. It is under the 250 ceiling but in the warning band; any further route/source/status expansion should split helper logic before adding more lines.

Todo 9 L verdict before K follow-up:

- Do not mark K Todo 9 fully accepted yet.
- The contract behavior requested by L is covered, but the Python import-floor regression should be fixed or explicitly dispositioned by the leader before integration.

This blocker is superseded by K follow-up commit `e6b38de2` below.

## Final Follow-Up Review: K Commit `e6b38de2`

Status: TODO 9 ACCEPTED FOR L CONTRACT REVIEW

Reviewed K follow-up commit:

- `e6b38de2 fix(legal-routes): drop route candidate import dependencies`

Reviewed surface:

- `trustgraph_legal/route_candidates.py`
- `tests/unit/legal_ontology/test_route_candidates.py`
- `.omo/evidence/debtor-context-graph-v0/task-9-*`
- `artifacts/K-route-stopgate-integration-report.md`

Verification L ran in K worktree:

- `/usr/bin/python3 --version && /usr/bin/python3 -c 'import trustgraph_legal.route_candidates; print("import-ok")'` -> Python 3.9.6 and `import-ok`.
- `/usr/bin/python3 -m py_compile trustgraph_legal/route_candidates.py tests/unit/legal_ontology/test_route_candidates.py` -> passed.
- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_route_candidates.py tests/unit/legal_ontology/test_stop_gates.py tests/unit/legal_ontology/test_debtor_context.py -q` -> 23 passed.
- `/Users/cosmos/.local/bin/basedpyright --level error trustgraph_legal/route_candidates.py tests/unit/legal_ontology/test_route_candidates.py` -> 0 errors.
- `/opt/homebrew/bin/python3 -m json.tool` over task-9 happy/failure evidence -> passed.
- `git diff --check e6b38de2^ e6b38de2` and `git diff --check cb4ea60b^ e6b38de2` -> passed.
- Source size check: `trustgraph_legal/route_candidates.py` 249 pure LOC; `tests/unit/legal_ontology/test_route_candidates.py` 227 pure LOC.
- Task-9 PII evidence says `NO_FINDINGS`.

Accepted coverage after follow-up:

- The prior `/usr/bin/python3` import-floor blocker is closed. Production module import no longer depends on Python 3.12 `typing.override`, top-level `pydantic`, or top-level `debtor_context_types`.
- The Todo 9 behavior verified at `cb4ea60b` remains intact: decorated legal source refs, review/retrieval/effective-date legal source gating, route-family scoped StopGate reason bridging, H-style non-legacy summary packet handling, and advisory-only route output.
- `accepted` remains out of clear route statuses, aligning with the leader/I final disposition that H `verified` facts resolve the earlier route-status issue. Any future `accepted` semantics remain K/leader-owned.
- Task-9 evidence does not print raw OCR text or PII matches, and the PII gate reports no findings.

Residual warning:

- `route_candidates.py` is 249 pure LOC. It is still under the 250 ceiling, but future route/legal-source expansion should split helper logic before adding more production lines.

Final Todo 9 L verdict:

- K has closed the Todo 9 gaps previously listed by L.
- No blocking StopGate, legal-source, direct-execution, H compatibility, accepted-status, PII, type, focused-test, JSON, diff-check, file-size, or Python import-floor issue remains from L's review.
