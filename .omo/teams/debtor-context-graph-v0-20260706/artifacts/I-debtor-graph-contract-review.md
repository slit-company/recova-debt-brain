# I Debtor Graph Contract Review

Status: PRE-IMPLEMENTATION REVIEW

Member: I / debtor-graph-contract-review
Scope: Todo 6 read-only contract review artifact. No production files edited.

## Inputs Reviewed

- Team plan: `/Users/cosmos/dev/ontology/trustgraph/.omo/plans/debtor-context-graph-v0.md`
- I worktree: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debtor-context-graph-v0-20260706/worktrees/I`
- H worktree: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debtor-context-graph-v0-20260706/worktrees/H`
- Existing contracts:
  - `trustgraph_legal/debtor_context_types.py`
  - `trustgraph_legal/document_assembly.py`
  - `trustgraph_legal/document_assembly_pages.py`
  - `trustgraph_legal/document_assembly_cli.py`
  - `trustgraph_legal/case_graph.py`
  - `trustgraph_legal/route_candidates.py`
  - `tests/unit/legal_ontology/test_debtor_context_types.py`
  - `tests/unit/legal_ontology/test_document_assembly.py`
  - `tests/unit/legal_ontology/test_case_graph_builder.py`
  - `tests/unit/legal_ontology/test_route_candidates.py`
- Prior team reports:
  - `artifacts/A-schema-contract-report.md`
  - `artifacts/C-document-assembly-report.md`
  - `artifacts/E-route-matcher-report.md`
  - `artifacts/F-assembly-cli-report.md`

## H Branch State

H is available and on branch `team/debtor-context-graph-v0-20260706/H`, but it currently has no Todo 6 implementation diff.

Evidence:

- `git -C .../worktrees/H rev-parse --abbrev-ref HEAD` -> `team/debtor-context-graph-v0-20260706/H`
- `git -C .../worktrees/H status --short` -> no output
- `git -C .../worktrees/H ls-files trustgraph_legal/debtor_context.py tests/unit/legal_ontology/test_debtor_context.py` -> no output
- `trustgraph_legal/debtor_context.py` does not exist in I/H at review time.

This artifact is therefore a pre-implementation acceptance checklist and risk register. It should be updated after H commits Todo 6.

## H In-Progress Test Diff Check

After the initial artifact draft, H reported a first test diff. I read the current untracked file in H's worktree:

- `tests/unit/legal_ontology/test_debtor_context.py`

Observed coverage in that draft:

- Builds from `build_document_assembly(PAGES_FIXTURE, REPO_ROOT)`.
- Calls planned `build_debtor_context(assembly_payload, repo_root=REPO_ROOT)` twice.
- Pins deterministic `debtor_graph_id` to the source bundle hash prefix.
- Pins deterministic `GraphSnapshot.source_bundle_hash`.
- Requires at least one `case_packet`.
- Requires at least one fact assertion and non-empty, non-`placeholder:` source refs.
- Requires `identity_unresolved` review item via `reason_code`.
- Asserts redaction profile and absence of fixture OCR strings in serialized JSON.

Remaining gaps for H before Todo 6 acceptance:

- Also pin `graph_snapshot_id` determinism, not only `source_bundle_hash`.
- Assert every material fact has `source_document_id`, `source_hash`, `chunk_id`, `line_start`, `line_end`, `extractor_version`, `ontology_version`, confidence, and review status.
- Reject all placeholder source refs covered by `FactAssertion`, not only refs beginning with `placeholder:`.
- Add the weak-identity two-similar-debtors scenario promised by Todo 6, or prove the current fixture contains equivalent weak identity pressure.
- Add route-handle predicate coverage for `evaluate_route_candidates()` compatibility.
- Add summary-only assembly payload rejection.
- Add an explicit local/domain-only assertion by review: no MCP SDK import, no storage/client import, and no hidden output write in builder functions.

## Acceptance Checklist For Todo 6

Todo 6 should not be accepted until all items below are covered by `tests/unit/legal_ontology/test_debtor_context.py`, task-6 evidence, or direct code review.

1. Stable graph identity
   - `debtor_graph_id` must be deterministic for the same debtor identity evidence.
   - When identity evidence is weak or absent, `debtor_graph_id` must fall back to deterministic source-bundle material, not a name-only merge.
   - Similar names without shared identity evidence must remain separate or unresolved.
   - Required failure evidence: two similar debtor placeholders with no identity evidence produce `identity_unresolved` and no merge.

2. Stable snapshot identity
   - `graph_snapshot_id` must be derived from stable material, including `source_bundle_hash`, fact assertion ids, route candidate ids if present, and version metadata.
   - Re-running the same input should produce the same snapshot id except for fields explicitly allowed to vary.
   - `generated_at` may vary, but it must not be part of the deterministic snapshot identity unless intentionally frozen/injected in tests.

3. Source bundle hash
   - `GraphSnapshot.source_bundle_hash` is required and must be based on sorted source hashes from document pages/assemblies or case graph documents.
   - It must not hash raw OCR text into output fields, logs, or evidence.
   - Changing a page source hash should change the source bundle hash and snapshot id.

4. No raw OCR text
   - Todo 6 must consume assembly metadata and, if extracting fields, read source text only transiently.
   - `DebtorGraphPayload.to_json()` and task-6 evidence must not include `raw_text`, `source_text`, classifier excerpts, full OCR page bodies, phone numbers, account-like identifiers, or resident-registration-number patterns.
   - Preserve `pii_profile.raw_text_included=false` and `source_text_included=false`.

5. Fact provenance
   - Every material `FactAssertion` must include non-placeholder `source_refs`, `source_document_id`, `source_hash`, `chunk_id`, `line_start`, `line_end`, `extractor_version`, `ontology_version`, confidence, and review status.
   - Do not construct facts with `source_ref="missing"` or equivalent placeholders; the schema rejects these and downstream snapshot validation depends on it.
   - Derived facts can be marked `derived=True`, but still need source refs that explain the derivation input.

6. Case packet compatibility
   - Todo 6 may reuse `build_case_graph` for synthetic manifest compatibility, but must not force real OCR roots into the old fixture manifest shape.
   - Existing `case_graph` identity uncertainty behavior should be preserved: no name-only merge, explicit `identity_uncertain`, and `name_only_without_identity_evidence` review signals.
   - `case_packets` should remain source-grounded and PII-safe.

7. Route matcher compatibility
   - `route_candidates.evaluate_route_candidates()` consumes a typed `DebtorGraphPayload` and matches `FactAssertion.predicate` against route `required_fact_handles` and `blocking_fact_handles`.
   - Todo 6 facts must use predicates such as `enforceable_title`, `third_party_debtor_bank_hint`, `employer_hint`, `real_estate_registry_asset`, `insolvency_stay`, and `insolvency_signal` when those facts are known.
   - Do not store only human-readable claim/title objects without route-handle facts; that would make routes incorrectly `missing_facts`.
   - Route candidates must remain advisory with `no_direct_execution=True`.

8. StopGate and future integration
   - Todo 6 should carry `stop_gates` through the graph payload even if Todo 9 later deepens the integration.
   - If StopGate reason codes are available from current `evaluate_case_graph`, preserve them as `stop_gates[].reason_code`; route matcher already reads reason codes and review items.
   - No route should be marked possible by bypassing StopGate blockers.

9. No hidden side effects
   - Todo 6 is local deterministic domain logic under `trustgraph_legal`.
   - It must not import the MCP SDK, start MCP servers, write to TrustGraph storage, Supabase, Cloudflare, Vercel, or other remote services.
   - Output writing belongs only to explicit CLI/evidence commands in later todos; builder functions should return payloads.

10. Python size and type risk
   - `trustgraph_legal/debtor_context_types.py` is already near the local pure-LOC ceiling, so Todo 6 should not add to that file unless absolutely necessary.
   - Add `trustgraph_legal/debtor_context.py` with narrow responsibilities or split helper modules before it crosses the size threshold.
   - Avoid broad dict plumbing inside the builder. Convert boundary JSON into typed values or existing DTOs before deriving graph facts.

## Contract Notes

- `DebtorGraphPayload.to_json()` already serializes the required v0 top-level sections and redaction profile.
- `FactAssertion.__post_init__()` rejects empty and placeholder source refs. Todo 6 should treat that as a hard acceptance gate, not catch and suppress it.
- `DocumentAssemblyPayload.to_json(summary_only=True)` intentionally omits page/assembly arrays. Todo 6 should require full assembly payload when building facts, or explicitly return a controlled input error for summary-only payloads.
- TSV-backed assembly pages use `source_ref="ocr:<repo-relative-path>#page=<n>"`; fixture pages use `source_ref="fixture:<repo-relative-path>#page=<n>"`. Both are acceptable source refs if they stay root-bounded and redacted.
- Existing `case_graph._first_provenance()` can emit placeholder `"missing"` provenance when expected fields are absent. Todo 6 must not convert those placeholders into `FactAssertion`s unless it first marks the fact as absent/review-only without violating the source-ref contract.
- `route_candidates.evaluate_route_candidates()` sets `review_status="review_required"` for every emitted candidate today. That is acceptable for v0, but Todo 6 should not overwrite it with a more permissive status.

## High-Risk Failure Modes

1. Name-only merge
   - Risk: Similar debtor names collapse into one debtor graph without identity evidence.
   - Mitigation: Test weak identity with two similar placeholders and assert separate or unresolved output plus `identity_unresolved`.

2. Snapshot instability
   - Risk: `generated_at` or unordered dict/list traversal changes `graph_snapshot_id` on every run.
   - Mitigation: Sort source hashes, fact ids, case packet ids, and route ids before hashing; inject/freeze timestamp in tests.

3. Provenance placeholders
   - Risk: Existing case graph fallback provenance with `"missing"` leaks into `FactAssertion`, causing runtime errors or fake provenance.
   - Mitigation: Skip absent facts or create review items; never materialize placeholder-backed facts.

4. Route handle mismatch
   - Risk: Builder emits rich claims/titles but not the predicates the route matcher expects.
   - Mitigation: Include direct route-handle facts and cover bank/wage/property/insolvency handles in tests.

5. Summary-only assembly input
   - Risk: Todo 6 accepts summary-only assembly JSON and silently builds an empty graph.
   - Mitigation: Reject summary-only payloads with a controlled error unless full `document_pages` and `document_assemblies` exist.

6. Hidden raw text retention
   - Risk: Field extraction requires text and a developer stores OCR snippets for debugging.
   - Mitigation: Read text transiently, assert `raw_text`/`source_text` absent recursively, and run the plan PII scan over task-6 evidence.

7. Oversized builder
   - Risk: One monolithic `debtor_context.py` accumulates assembly parsing, extraction, identity, snapshot, route mapping, and CLI logic.
   - Mitigation: Keep Todo 6 to builder/domain only; defer CLI to Todo 10; split pure helpers if the module approaches the size target.

## Suggested Minimum Tests For H

- `test_builds_stable_debtor_graph_from_full_assembly_payload`
  - Same synthetic assembly input yields identical `debtor_graph_id`, `graph_snapshot_id`, and `source_bundle_hash`.
- `test_weak_identity_emits_identity_unresolved_without_name_only_merge`
  - Two similar debtor names without identity evidence do not merge and produce review item reason `identity_unresolved`.
- `test_material_facts_require_source_refs_and_versions`
  - Every fact has non-placeholder source refs, source hash, extractor version, ontology version, confidence, and review status.
- `test_graph_contains_route_handle_facts_for_existing_matcher`
  - A graph with enforceable title and bank hint yields facts whose predicates let `evaluate_route_candidates()` make `bank_account_attachment` non-missing.
- `test_summary_only_assembly_payload_is_rejected`
  - A summary-only document assembly payload cannot produce a fake empty graph.
- `test_debtor_graph_output_is_redacted`
  - Recursive assertion that no `raw_text`, `source_text`, `excerpt`, resident-registration-number, phone, or account-like pattern appears.

## Review Verdict

Pre-implementation status: READY FOR H TO IMPLEMENT AGAINST THIS CHECKLIST.

No H code is available yet, so there is no approval or rejection of Todo 6 implementation. The main acceptance risks are deterministic identity/snapshot derivation, provenance discipline, route-handle compatibility, and avoiding raw OCR or storage/MCP side effects.

## Post-Implementation Review: H Commit 611909b5

Review status: NEEDS FOLLOW-UP FOR ROUTE/PII GATE RISKS

Reviewed H commit:

- `611909b5 feat(legal-graph): build debtor context graphs`

Reviewed H files:

- `trustgraph_legal/debtor_context.py`
- `trustgraph_legal/debtor_context_builder.py`
- `tests/unit/legal_ontology/test_debtor_context.py`
- `.omo/evidence/debtor-context-graph-v0/task-6-debtor-graph-happy.json`
- `.omo/evidence/debtor-context-graph-v0/task-6-debtor-graph-failure.json`
- `artifacts/H-debtor-graph-builder-report.md`

Verification I ran in H worktree:

- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_debtor_context.py tests/unit/legal_ontology/test_route_candidates.py -q` -> 7 passed.
- `/usr/bin/python3 -m py_compile trustgraph_legal/debtor_context.py trustgraph_legal/debtor_context_builder.py tests/unit/legal_ontology/test_debtor_context.py` -> passed.
- `basedpyright --level error trustgraph_legal/debtor_context.py trustgraph_legal/debtor_context_builder.py tests/unit/legal_ontology/test_debtor_context.py` -> 0 errors.
- `/opt/homebrew/bin/python3 -m json.tool` over both task-6 evidence files -> passed.
- `git diff --check 611909b5^ 611909b5` -> passed.
- Size check: `debtor_context.py` 20 pure LOC, `debtor_context_builder.py` 236 pure LOC, `test_debtor_context.py` 118 pure LOC.

Accepted contract coverage:

- `build_debtor_context_from_path(...)` stays local and domain-only.
- No MCP SDK, storage, Supabase, Cloudflare, Vercel, network, DB, or output-write imports were found in H production files.
- `debtor_graph_id`, `graph_snapshot_id`, and `source_bundle_hash` are deterministic for unchanged source pages.
- Full assembly payloads are required; summary-only JSON and empty assembly payloads are rejected with `DebtorContextInputError`.
- Material facts carry source refs, source document id, source hash, chunk id, line span, extractor version, ontology version, confidence, and review status.
- Weak identity falls back to source-bundle identity, emits `identity_unresolved`, and the two-similar-debtors test proves no name-only merge across distinct source bundles.
- The happy evidence serializes schema v1, one case packet, 12 fact assertions, one identity review item, and no raw OCR body.

Findings:

1. Route matcher status compatibility is not fully accepted.
   - Evidence: H emits route-handle facts with `review_status="accepted"` in `trustgraph_legal/debtor_context_builder.py:195`.
   - Existing `route_candidates.CLEAR_FACT_REVIEW_STATUSES` does not include `accepted`; it clears `approved`, `assembled`, `confirmed`, `extracted`, and `verified`.
   - Live probe against H's happy fixture produced `bank_account_attachment.status == "review_required"` with `missing_facts == ()`, not `possible`.
   - Risk: Todo 6 can claim bank route handle coverage while downstream route evaluation remains more conservative than Todo 8's contract. H should either emit an existing clear status such as `extracted`/`confirmed`, extend route matcher clear statuses deliberately, or update acceptance wording/tests to require `review_required` for H-derived facts.

2. Snapshot id is deterministic but too narrow for future replay/diff semantics.
   - Evidence: `graph_snapshot_id="snapshot:{}".format(_digest_part(bundle_hash))` in `trustgraph_legal/debtor_context_builder.py:93`.
   - The snapshot id ignores fact assertion ids, route candidate ids, extractor versions, ontology version, route version, and legal rule-source version even though those are carried in `GraphSnapshot`.
   - Risk: future extractor or rule-version changes can alter graph facts while preserving the same page hashes and therefore the same snapshot id. Todo 7 may need to fix this before relying on snapshot ids for replay/diff.

3. Generated timestamp is currently a fixed constant.
   - Evidence: `GENERATED_AT = "2026-07-06T00:00:00Z"` in `trustgraph_legal/debtor_context_builder.py:23`.
   - This keeps tests deterministic, but the field is named `generated_at` and the plan calls for generated timestamp metadata.
   - Risk: downstream audit/evidence may read it as the real generation time. Prefer an injectable clock/default timestamp before user-facing CLI/evidence paths depend on it.

4. The plan's sensitive-pattern scan still needs an allowlist or evidence adjustment for hashes.
   - The strict regex from the plan matched a phone-shaped numeric substring inside `source_bundle_hash` values in `task-6-debtor-graph-failure.json`.
   - I treat this as a hash false positive, not a raw PII leak, but the final evidence gate says PII scan should return `NO_FINDINGS`.
   - H/leader should either record this as an explicit hash false-positive exception or adjust task/final evidence so the exact required scan is clean.

Overall verdict:

- No raw OCR text, hidden MCP/storage side effects, name-only merge, missing source refs, type errors, py_compile failures, JSON parse failures, or focused pytest failures found.
- Do not treat Todo 6 as fully route-compatible until finding 1 is resolved or explicitly accepted by the leader.
- Treat findings 2-4 as follow-up risks for Todo 7/final evidence unless the leader wants Todo 6 to repair them before integration.

## Final Follow-Up Disposition

Final status: TODO 6 ROUTE-STATUS BLOCKER RESOLVED ON MASTER; FORWARD RISKS REMAIN

Supersedes the earlier `NEEDS FOLLOW-UP FOR ROUTE/PII GATE RISKS` status for the route-status blocker.

H follow-up reviewed:

- `6ee22757 fix(legal-graph): clear verified route facts`
- Leader reports H was independently verified and merged to master as `27ed6cb1`.

What changed:

- H changed clear graph facts from `review_status="accepted"` to `review_status="verified"`.
- H updated `tests/unit/legal_ontology/test_debtor_context.py` to assert `bank_account_attachment.status == "possible"`.
- H regenerated task-6 evidence with `task_6_probe.bank_account_attachment_status == "possible"`.

Verification I ran:

- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_debtor_context.py tests/unit/legal_ontology/test_route_candidates.py -q` in H -> 7 passed.
- `/usr/bin/python3 -m py_compile trustgraph_legal/debtor_context.py trustgraph_legal/debtor_context_builder.py tests/unit/legal_ontology/test_debtor_context.py` in H -> passed.
- `basedpyright --level error trustgraph_legal/debtor_context.py trustgraph_legal/debtor_context_builder.py tests/unit/legal_ontology/test_debtor_context.py` in H -> 0 errors.
- JSON validation over H task-6 happy/failure evidence -> passed.
- Live H route probe -> `bank_account_attachment.status == "possible"`, `missing_facts == ()`, route-handle fact statuses `["verified"]`.
- `git diff --check 6ee22757^ 6ee22757` in H -> passed.

Route finding disposition:

- Finding 1 is closed for the integrated Todo 6 path because master uses H's `verified` fact statuses, which are already clear in the route matcher contract.
- E also produced alternate commit `0465cc6e fix(legal-routes): accept integrated route facts`, verified by I with 8 focused tests passing and an accepted-status live probe returning `possible`.
- Per leader disposition, E `0465cc6e` is not treated as integrated or accepted by default. It is an alternate patch for Todo 9/K to review deliberately alongside StopGate and legal-source semantics.

Remaining nonblocking risks assigned forward:

1. Snapshot identity remains source-bundle-only.
   - `graph_snapshot_id` is still derived from `source_bundle_hash` only. This is acceptable for Todo 6 integration per leader disposition, but Todo 7 should revisit snapshot ids so extractor/version/rule/fact changes can produce distinct replay/diff snapshots when source pages do not change.

2. Generated timestamp remains fixed.
   - `generated_at` is still the fixed value `2026-07-06T00:00:00Z`. This keeps deterministic tests stable, but Todo 7/10 should decide whether to inject a clock or rename the field semantics before operator-facing evidence relies on it.

3. Strict regex scan still has a hash-shaped false positive in H failure evidence.
   - The plan's broad sensitive-pattern regex still matches a numeric substring inside `source_bundle_hash` values in H `task-6-debtor-graph-failure.json`.
   - I found no raw OCR body, debtor placeholder leak, or actual phone/account/resident-registration-number evidence leak in task-6 JSON.
   - Per leader disposition, this should be handled in final evidence as an explicit hash false-positive/allowlist issue rather than blocking Todo 6.

Final I verdict:

- Todo 6 H implementation is acceptable for integration on the route-status issue after H `6ee22757` / master `27ed6cb1`.
- Do not integrate E `0465cc6e` implicitly; treat it as a Todo 9 candidate decision.
- Carry snapshot-id scope and hash-shaped scan false positives into Todo 7/final evidence tracking.
