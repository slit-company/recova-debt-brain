# debtor-context-graph-v0 - Work Plan

## TL;DR (For humans)
Recova가 채무자 한 명의 사건을 계속 기억하도록, OCR 페이지들을 문서와 절차로 묶고 그 결과를 채무자별 기억 그래프로 만드는 v0 계획이다. 그래프는 채권, 집행권원, 송달/확정, 시효, 압류 후보, 회생/파산 신호, route 후보를 증거와 함께 버전으로 남긴다.

**What you'll get:** 실제 OCR 묶음을 넣으면 “이 채무자 사건이 어디까지 왔고, 어떤 추심 루트가 가능하며, 무엇이 부족한지”를 redacted 그래프로 출력하는 기반. 나중에 Hermes/GPT/Claude 같은 에이전트는 MCP를 통해 이 그래프와 route 후보를 읽게 된다.

**Why this approach:** 지금 실제 OCR은 문서가 아니라 페이지 단위라서, 바로 전략 추천을 만들면 불안정하다. 먼저 페이지를 문서/절차/사건으로 재조립하고, 그 위에 채무자 기억 그래프와 route 판단을 올리는 순서가 맞다.

**What it will NOT do:** 실제 추심 실행, 법원 제출, 채무자 연락 자동화는 하지 않는다. 원문 개인정보를 MCP 응답에 직접 노출하지 않는다. v0에서 Supabase/원격 저장소까지 붙이지 않는다.

**Effort:** Large
**Risk:** Medium - real OCR page assembly and identity resolution are the hard parts, but the current legal/MCP skeleton is reusable.
**Decisions to sanity-check:** `채무자 1명 = DebtorGraph 1개`, graph output is redacted/source-ref based, storage is deferred until after deterministic local v0.

Your next move: start execution with `$omo:start-work .omo/plans/debtor-context-graph-v0.md`, or ask for high-accuracy plan review first. Full execution detail follows below.

---

> TL;DR (machine): Large/Medium risk. Add deterministic Debtor Context Graph v0 over page-level OCR, with document assembly, fact assertions, route templates, legal rule-source metadata, additive MCP tools, and full pytest/evidence gates.

## Scope
### Must have
- New domain logic lives under `trustgraph_legal`, not inside the MCP SDK layer.
- A deterministic `DocumentAssembly` layer that reads page-level OCR markdown and emits redacted document/procedure candidates.
- A stable `DebtorContextGraph` payload with:
  - `schema_version`: `recova-debtor-context-graph/v1`
  - `debtor_graph_id`
  - `graph_snapshot_id`
  - `identity_resolution`
  - `case_packets`
  - `document_assemblies`
  - `fact_assertions`
  - `claims`
  - `enforcement_titles`
  - `procedure_episodes`
  - `asset_hints`
  - `stop_gates`
  - `route_candidates`
  - `review_items`
  - `pii_profile`
- One stable `DebtorGraph` per debtor identity, with multiple `CasePacket` children. If identity is unresolved, use a deterministic bundle-hash fallback and emit `identity_unresolved` review.
- `FactAssertion` as the canonical fact wrapper. Every material fact must include source pointer, confidence, extractor version, ontology/rule version, and review status.
- `GraphSnapshot` as append-friendly version metadata. It must include source bundle hash, extractor versions, ontology version, route version, legal rule-source version, and generated timestamp.
- Route template resources from the 18 route candidates extracted from the long-term debt-collection manual.
- Versioned legal rule-source resources from the Korean-law MCP evidence: law name, lawId, MST, article, effective date, retrieved date/status, and graph use.
- Route candidate matcher that reports possible/blocked/missing-facts/review states and never claims direct execution.
- Additive MCP tools over the existing redacted `trustgraph_legal.mcp_domain` envelope.
- Tests and evidence that use:
  - synthetic minimized fixtures for precise red/green unit tests;
  - the real OCR corpus for PII-safe smoke/eval summaries.
- All outputs must be redacted. No raw OCR text, resident-registration-number patterns, phone numbers, or account-like identifiers in evidence or MCP responses.

### Must NOT have (guardrails, anti-slop, scope boundaries)
- Do not implement actual court filing, debtor contact, payment demand, or collection execution.
- Do not expose raw debtor names, resident-registration-number patterns, phone numbers, account-like identifiers, or full OCR source text in MCP responses, JSON evidence, or reports.
- Do not mutate unrelated dirty worktree files:
  - `deploy/recova-mcp-lab/README.md`
  - `docs/product/debt-collection-ontology/recova-mcp-client-guide.md`
  - `docs/product/debt-collection-ontology/recova-mcp-lab-runbook.md`
  - `scripts/recova_mcp/check_runbook.py`
  - `scripts/recova_mcp/rollback_lab.sh`
  - untracked deployment artifacts under `deploy/`, `scripts/recova_mcp/`, `.omo/evidence/recova-mcp-deployment/`
- Do not replace or remove the existing 16 MCP tools. New tools must be additive and compatible.
- Do not require live Supabase, remote database, Cloudflare, Vercel, or production MCP deployment for v0 acceptance.
- Do not run live Korean-law MCP lookups inside deterministic unit tests. Curated JSON fixtures/resources are the tested boundary.
- Do not call full `mcp` SDK in hermetic tests; keep tests on `trustgraph_legal.mcp_domain` and fake-MCP adapter boundary.

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: TDD for each new schema/builder/matcher module, then focused integration tests. Use `/opt/homebrew/bin/python3 -m pytest`.
- Evidence directory: `.omo/evidence/debtor-context-graph-v0/`.
- Required recurring gates:
  - `python3 -m json.tool` over every new JSON resource/evidence file.
  - focused pytest for each todo's changed module.
  - PII scan over changed source/tests/resources/evidence/docs:
    `rg -n "[0-9]{6}-[0-9]{7}|(?:\\+82[-.[:space:]]?)?0[0-9]{1,2}[-.[:space:]]?[0-9]{3,4}[-.[:space:]]?[0-9]{4}|(계좌|은행|입금|송금|account|bank).{0,24}[0-9]{2,6}[-.[:space:]][0-9]{2,6}[-.[:space:]][0-9]{2,8}|주민등록번호" <paths>`
  - `git diff --check` before every commit.
- Final test command target:
  - `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_document_assembly.py tests/unit/legal_ontology/test_debtor_context.py tests/unit/legal_ontology/test_route_candidates.py tests/unit/legal_ontology/test_mcp_debtor_context_tools.py tests/integration/legal_ontology/test_debtor_context_pipeline.py tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py -q`

## Execution strategy
### Parallel execution waves
> Target 5-8 todos per wave. Fewer than 3 (except the final) means you under-split.
- Wave 1 builds the local data contract and OCR page/document assembly surface. Todos 1-5 can mostly run in parallel after Todo 1, but keep model/resource file write scopes disjoint.
- Wave 2 builds debtor graph snapshots, route/legal resources, and route matcher. Todos 6-10 depend on Wave 1 contracts.
- Wave 3 adds MCP tools, real OCR eval harness, docs, and final integration. Todos 11-15 depend on Wave 2 outputs.

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1. Debtor context schema contract | none | 2, 6, 11 | 3, 4 after schema names settle |
| 2. DocumentAssembly page/document builder | 1 | 5, 6 | 3, 4 |
| 3. OCR corpus fixture/evidence harness | 1 | 5, 15 | 2, 4 |
| 4. Route/legal resource skeleton and validators | 1 | 8, 9 | 2, 3 |
| 5. DocumentAssembly CLI and tests | 2, 3 | 6, 15 | 4 |
| 6. DebtorContextGraph builder | 1, 2, 5 | 7, 9, 11 | 8 |
| 7. FactAssertion/GraphSnapshot replay and diff checks | 6 | 10, 15 | 8, 9 |
| 8. Route candidate matcher | 4 | 9, 12 | 7 |
| 9. StopGate/legal rule-source integration | 4, 6, 8 | 10, 12 | 7 |
| 10. End-to-end debtor context CLI | 6, 7, 8, 9 | 11, 15 | none |
| 11. Additive MCP debtor graph tools | 10 | 13, 15 | 12 |
| 12. Governance/review hooks for graph facts and routes | 8, 9 | 13, 15 | 11 |
| 13. Integration tests and fake-MCP contract tests | 11, 12 | 15 | 14 |
| 14. Product/developer docs | 10, 11 | 15 | 13 |
| 15. Real OCR eval and final evidence pack | all prior | final verification | none |

## Todos
> Implementation + Test = ONE todo. Never separate.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->
- [ ] 1. Define Debtor Context Graph v0 schema types and JSON contract
  What to do / Must NOT do: Add schema/model module(s) under `trustgraph_legal`, recommended path `trustgraph_legal/debtor_context_types.py`. Define dataclasses or typed helpers for `DocumentPage`, `DocumentAssembly`, `ProcedureEpisode`, `FactAssertion`, `GraphSnapshot`, `DebtorGraphPayload`, `RouteCandidate`, and shared `JsonValue`. Include `to_json()` methods and constants for schema/extractor/ontology/route/rule versions. Do not import MCP SDK. Do not persist raw OCR text in any `to_json()`.
  Parallelization: Wave 1 | Blocked by: none | Blocks: 2, 6, 11
  References (executor has NO interview context - be exhaustive): `trustgraph_legal/case_graph.py:17` for schema constants; `trustgraph_legal/case_graph.py:26` for dataclass style; `trustgraph_legal/classifier_types.py:88` for `ClassificationResult.to_json`; `.omo/research/debtor-context-graph/SYNTHESIS.md`.
  Acceptance criteria (agent-executable): `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_debtor_context_types.py -q` passes and proves `raw_text_included` is false, required top-level keys exist, and `FactAssertion` rejects missing source refs.
  QA scenarios (name the exact tool + invocation): happy: instantiate a synthetic graph snapshot and serialize to `.omo/evidence/debtor-context-graph-v0/task-1-schema-happy.json`; failure: attempt a fact assertion with missing/placeholder source ref and assert a validation error, evidence `.omo/evidence/debtor-context-graph-v0/task-1-schema-failure.txt`.
  Commit: Y | `feat(legal-graph): add debtor context graph schema`

- [ ] 2. Implement deterministic OCR page inventory and document assembly builder
  What to do / Must NOT do: Add `trustgraph_legal/document_assembly.py`. Read an OCR root with `manifest.tsv` when available, else natural-sort markdown files. Emit page records with `page_id`, redacted `source_ref`, `source_hash`, `relative_path`, page order, line/char counts, classifier document type, review status, and keyword signal counts. Group pages into `DocumentAssembly` candidates using deterministic v0 rules: contiguous same canonical classifier type forms a document; unknown pages near recognized procedure terms form review bundles; every page belongs to exactly one assembly. Do not include page text or classifier excerpts in output.
  Parallelization: Wave 1 | Blocked by: 1 | Blocks: 5, 6
  References: `.omo/evidence/debtor-context-graph/ocr-corpus-shape.json`; `.omo/evidence/debtor-context-graph/ocr-classifier-coverage.json`; `trustgraph_legal/classifier_types.py:99` warns classifier JSON contains evidence spans, so this builder must aggregate only.
  Acceptance criteria: `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_document_assembly.py -q` passes. Tests assert all pages are assigned once, source hashes are stable, unknown pages are retained as review bundles, and no `excerpt`/raw text appears in output.
  QA scenarios: happy: run builder over a synthetic 5-page OCR fixture and write `.omo/evidence/debtor-context-graph-v0/task-2-assembly-happy.json`; failure: malformed/missing OCR root returns a clear nonzero CLI/API error without partial output, evidence `.omo/evidence/debtor-context-graph-v0/task-2-assembly-failure.txt`.
  Commit: Y | `feat(legal-graph): add OCR document assembly builder`

- [ ] 3. Add minimized OCR assembly fixtures and PII-safe real corpus probe
  What to do / Must NOT do: Add synthetic fixtures under `tests/fixtures/legal-ocr-pages/` that model page-level OCR without real identifiers. Add a test helper or script under `scripts/legal_ontology/` to summarize the real OCR corpus path `/Users/cosmos/dev/ocr/MinerU/work/legal_ocr_20260630` into aggregate evidence only. Do not copy real OCR text into the repo.
  Parallelization: Wave 1 | Blocked by: 1 | Blocks: 5, 15
  References: `.omo/evidence/debtor-context-graph/ocr-corpus-shape.json`; current fixture validator `scripts/legal_ontology/check_fixture_manifest.py`; existing fixtures `tests/fixtures/legal-ocr/manifest.json`.
  Acceptance criteria: `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_document_assembly.py -q` includes synthetic fixture coverage and passes. Real corpus probe writes aggregate counts only.
  QA scenarios: happy: `/opt/homebrew/bin/python3 -m trustgraph_legal.document_assembly --ocr-root /Users/cosmos/dev/ocr/MinerU/work/legal_ocr_20260630 --out .omo/evidence/debtor-context-graph-v0/task-3-real-ocr-assembly-summary.json --summary-only` exits 0; failure: PII scan over the evidence path returns `NO_FINDINGS`, saved at `.omo/evidence/debtor-context-graph-v0/task-3-pii-scan.txt`.
  Commit: Y | `test(legal-graph): add OCR assembly fixtures`

- [ ] 4. Add route and legal rule-source resources with validators
  What to do / Must NOT do: Add `resources/legal_routes/debt_collection_routes_v0.json` from the 18 route candidates in `.omo/evidence/debtor-context-graph/route-manual-summary.json`. Add `resources/legal_rules/debt_collection_route_sources_v0.json` from `.omo/evidence/debtor-context-graph/korean-law-source-map.json`. Add validator script `scripts/legal_ontology/validate_routes.py` or extend a focused validator. Do not perform live law MCP calls in tests.
  Parallelization: Wave 1 | Blocked by: 1 | Blocks: 8, 9
  References: `.omo/evidence/debtor-context-graph/route-manual-summary.json`; `.omo/evidence/debtor-context-graph/korean-law-source-map.json`; `resources/legal_rules/debt_collection_stopgate_v0.json`; `scripts/legal_ontology/validate_ontology.py`.
  Acceptance criteria: `/opt/homebrew/bin/python3 -m json.tool resources/legal_routes/debt_collection_routes_v0.json` passes; `/opt/homebrew/bin/python3 scripts/legal_ontology/validate_routes.py resources/legal_routes/debt_collection_routes_v0.json resources/legal_rules/debt_collection_route_sources_v0.json` reports pass; focused tests verify unknown legal source IDs fail.
  QA scenarios: happy: validator evidence `.omo/evidence/debtor-context-graph-v0/task-4-route-validator-happy.txt`; failure: temp route with missing legal source exits nonzero and evidence `.omo/evidence/debtor-context-graph-v0/task-4-route-validator-failure.txt`.
  Commit: Y | `feat(legal-routes): add route and legal source resources`

- [ ] 5. Expose DocumentAssembly CLI and manifest-to-assembly bridge
  What to do / Must NOT do: Add module entrypoint `python3 -m trustgraph_legal.document_assembly`. It must accept `--ocr-root`, `--manifest-tsv` optional, `--out`, `--summary-only`, and `--limit`. It must also support synthetic fixture page folders. Do not accept arbitrary MCP path input here; this is local CLI only. Output must be deterministic and redacted.
  Parallelization: Wave 1 | Blocked by: 2, 3 | Blocks: 6, 15
  References: CLI style in `trustgraph_legal/case_graph.py:61`; output writing style `trustgraph_legal/case_graph.py:68`; fixture CLI tests in `tests/unit/legal_ontology/test_case_graph_builder.py:76`.
  Acceptance criteria: `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_document_assembly.py -q` passes and direct CLI invocation writes JSON with `schema_version`, `summary.pages`, `summary.assemblies`, and `pii_profile.raw_text_included=false`.
  QA scenarios: happy: CLI over synthetic fixture writes `.omo/evidence/debtor-context-graph-v0/task-5-assembly-cli.json`; failure: `--limit 0` or nonexistent root produces controlled error and `.omo/evidence/debtor-context-graph-v0/task-5-assembly-cli-failure.txt`.
  Commit: Y | `feat(legal-graph): add document assembly CLI`

- [ ] 6. Build DebtorContextGraph from assembly output and existing extractors
  What to do / Must NOT do: Add `trustgraph_legal/debtor_context.py`. It consumes a `DocumentAssembly` payload or path, reuses `classify_text` and `extract_fields` where text is available, creates `FactAssertion`s, resolves `DebtorGraph` identity using identity evidence when available, falls back to source-bundle hash with review item when not, and emits `DebtorGraphPayload`. It may call existing `build_case_graph` for synthetic manifest compatibility, but must not force real OCR into fixture manifest shape.
  Parallelization: Wave 2 | Blocked by: 1, 2, 5 | Blocks: 7, 9, 11
  References: `trustgraph_legal/case_graph.py:50`; `trustgraph_legal/case_graph.py:109`; `trustgraph_legal/case_graph.py:153` identity uncertainty pattern; `tests/unit/legal_ontology/test_case_graph_builder.py:139` no name-only merge behavior.
  Acceptance criteria: `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_debtor_context.py -q` passes. Tests assert stable `debtor_graph_id`, one-or-more `case_packets`, fact source refs, graph snapshot version metadata, and identity-unresolved review on weak identity.
  QA scenarios: happy: synthetic assembled fixture builds `.omo/evidence/debtor-context-graph-v0/task-6-debtor-graph-happy.json`; failure: two similar debtor names with no identity evidence remain separate or unresolved with explicit `identity_unresolved`, evidence `.omo/evidence/debtor-context-graph-v0/task-6-debtor-graph-failure.json`.
  Commit: Y | `feat(legal-graph): build debtor context graphs`

- [ ] 7. Add snapshot replay, diff, and provenance validation
  What to do / Must NOT do: Add snapshot comparison helpers, recommended module `trustgraph_legal/debtor_snapshots.py`. Given two snapshots, report added/removed/changed fact assertions, changed route candidates, and source-bundle hash changes. Validate every non-derived fact has non-placeholder provenance. Do not compare raw text.
  Parallelization: Wave 2 | Blocked by: 6 | Blocks: 10, 15
  References: existing provenance checks in `tests/unit/legal_ontology/test_case_graph_builder.py:35`; StopGate invalid provenance tests in `tests/unit/legal_ontology/test_stop_gates.py:113`; `trustgraph_legal/case_graph.py:252`.
  Acceptance criteria: `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_debtor_snapshots.py -q` passes. Tests assert identical input yields identical snapshot id; changed source hash changes snapshot id; missing provenance fails validation.
  QA scenarios: happy: write `.omo/evidence/debtor-context-graph-v0/task-7-snapshot-diff-happy.json`; failure: mutate source_ref to `missing` and assert validation failure, evidence `.omo/evidence/debtor-context-graph-v0/task-7-snapshot-diff-failure.txt`.
  Commit: Y | `feat(legal-graph): add debtor graph snapshot diffs`

- [ ] 8. Implement route candidate matcher over DebtorContextGraph
  What to do / Must NOT do: Add `trustgraph_legal/route_candidates.py`. Load route resources, normalize route requirements, and evaluate graph facts into route candidate statuses: `possible`, `blocked`, `missing_facts`, `review_required`. Include `required_facts`, `missing_facts`, `blocking_facts`, `legal_source_refs`, `confidence`, and `no_direct_execution=true`. Do not generate legal documents or filing instructions beyond advisory labels.
  Parallelization: Wave 2 | Blocked by: 4 | Blocks: 9, 12
  References: route evidence `.omo/evidence/debtor-context-graph/route-manual-summary.json`; `trustgraph_legal/mcp_handlers.py:121` current placeholder recommendation; `resources/legal_rules/debt_collection_stopgate_v0.json`.
  Acceptance criteria: `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_route_candidates.py -q` passes. Tests assert bank/wage/property routes surface missing facts instead of false possible; insolvency signal blocks/reviews direct collection routes.
  QA scenarios: happy: graph with enforceable title and bank hint yields `bank_account_attachment` not blocked, evidence `.omo/evidence/debtor-context-graph-v0/task-8-routes-happy.json`; failure: graph with insolvency stay makes collection routes `blocked` or `review_required`, evidence `.omo/evidence/debtor-context-graph-v0/task-8-routes-failure.json`.
  Commit: Y | `feat(legal-routes): evaluate debtor route candidates`

- [ ] 9. Integrate StopGate and legal rule-source metadata into graph route evaluation
  What to do / Must NOT do: Ensure route evaluation calls or consumes `evaluate_case_graph` results for each relevant `CasePacket`, propagates StopGate reason codes into route blockers, and attaches curated legal rule-source refs. Add source status checks so draft/deprecated/future-only legal sources cannot clear routes without review. Do not live-fetch law.
  Parallelization: Wave 2 | Blocked by: 4, 6, 8 | Blocks: 10, 12
  References: `trustgraph_legal/stop_gates.py` via tests; `tests/unit/legal_ontology/test_stop_gates.py:29`; `tests/unit/legal_ontology/test_stop_gates.py:137` unapproved rules block; `.omo/evidence/debtor-context-graph/korean-law-source-map.json`.
  Acceptance criteria: `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_route_candidates.py tests/unit/legal_ontology/test_stop_gates.py -q` passes. Tests assert route blockers include StopGate reason codes and legal source refs contain lawId/MST/article.
  QA scenarios: happy: approved legal source route candidate emits law refs, evidence `.omo/evidence/debtor-context-graph-v0/task-9-legal-route-happy.json`; failure: temp legal source with `review_status=draft` yields route `review_required`, evidence `.omo/evidence/debtor-context-graph-v0/task-9-legal-route-failure.json`.
  Commit: Y | `feat(legal-routes): attach stop gates and legal sources`

- [ ] 10. Add end-to-end debtor context CLI
  What to do / Must NOT do: Add module entrypoint `python3 -m trustgraph_legal.debtor_context`. It must accept `--ocr-root` or `--assembly`, `--out`, `--route-resources`, `--legal-sources`, `--summary-only`, and `--limit`. It should write a redacted graph or summary. Do not require remote storage.
  Parallelization: Wave 2 | Blocked by: 6, 7, 8, 9 | Blocks: 11, 15
  References: CLI style `trustgraph_legal/case_graph.py:61`; current real OCR path evidence `.omo/evidence/debtor-context-graph/ocr-corpus-shape.json`; final graph target shape `.omo/research/debtor-context-graph/SYNTHESIS.md`.
  Acceptance criteria: `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_debtor_context.py tests/integration/legal_ontology/test_debtor_context_pipeline.py -q` passes. CLI over synthetic fixtures writes full graph; CLI over real OCR with `--summary-only` writes aggregate summary with no raw PII.
  QA scenarios: happy: real OCR summary command writes `.omo/evidence/debtor-context-graph-v0/task-10-real-ocr-debtor-summary.json`; failure: no pages/classifier all-unknown case emits `review_items` and nonzero `unknown_assemblies`, evidence `.omo/evidence/debtor-context-graph-v0/task-10-unknown-only.json`.
  Commit: Y | `feat(legal-graph): add debtor context CLI`

- [ ] 11. Add additive MCP tools for debtor graph reading and route explanation
  What to do / Must NOT do: Extend `trustgraph_legal/mcp_domain.py` and `trustgraph_legal/mcp_handlers.py` with additive tools. Recommended tools:
  - `assemble_debtor_documents`
  - `build_debtor_context_graph`
  - `get_debtor_graph_snapshot`
  - `list_debtor_route_candidates`
  - `explain_debtor_route_candidate`
  Use group `debtor_graph` with scopes `debtor_graph:assembly`, `debtor_graph:build`, `debtor_graph:read`, `debtor_graph:routes`. MCP path arguments must remain repo-root bounded. Do not add `authorization` tool args.
  Parallelization: Wave 3 | Blocked by: 10 | Blocks: 13, 15
  References: current tool registry `trustgraph_legal/mcp_domain.py:21`; tool definitions `trustgraph_legal/mcp_domain.py:97`; invoke envelope `trustgraph_legal/mcp_domain.py:121`; auth/path contract tests `tests/unit/legal_ontology/test_mcp_domain_tools.py:125`.
  Acceptance criteria: `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_debtor_context_tools.py tests/unit/legal_ontology/test_mcp_domain_tools.py -q` passes. Existing 16 tools remain present and ordered before additive debtor tools unless tests intentionally update expected list.
  QA scenarios: happy: fake MCP/tool call returns redacted route candidates, evidence `.omo/evidence/debtor-context-graph-v0/task-11-mcp-happy.json`; failure: outside-root `assembly_path`/`graph_path` returns `path_outside_repo_root` without leaking path or file content, evidence `.omo/evidence/debtor-context-graph-v0/task-11-mcp-path-failure.json`.
  Commit: Y | `feat(legal-mcp): expose debtor context graph tools`

- [ ] 12. Add governance/review hooks for facts, assemblies, and routes
  What to do / Must NOT do: Extend existing governance concepts or add `trustgraph_legal/debtor_governance.py` to queue review items for unknown assemblies, identity unresolved, conflicting claim amounts, draft/future legal source, blocked routes, and manual fact review decisions. Production ontology/resources must remain read-only in v0.
  Parallelization: Wave 3 | Blocked by: 8, 9 | Blocks: 13, 15
  References: existing governance service-side boundary from `trustgraph_legal/governance.py`; `trustgraph_legal/mcp_handlers.py:133` unknown document governance; `.omo/research/debtor-context-graph/SYNTHESIS.md`.
  Acceptance criteria: `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_debtor_governance.py -q` passes. Review records must be serializable, PII-safe, and must not mutate route/legal/ontology resources.
  QA scenarios: happy: unknown assembly creates review queue item and reprocess suggestion, evidence `.omo/evidence/debtor-context-graph-v0/task-12-governance-happy.json`; failure: attempted promotion without approval metadata is rejected with audit fields, evidence `.omo/evidence/debtor-context-graph-v0/task-12-governance-failure.json`.
  Commit: Y | `feat(legal-governance): add debtor graph review hooks`

- [ ] 13. Add integration and fake-MCP contract tests
  What to do / Must NOT do: Add `tests/integration/legal_ontology/test_debtor_context_pipeline.py` and `tests/unit/legal_ontology/test_mcp_debtor_context_tools.py`. Cover synthetic full pipeline, repo-root path boundaries, redaction, tool schema, stable graph snapshot IDs, and route candidate explanation. Do not require global `mcp` package.
  Parallelization: Wave 3 | Blocked by: 11, 12 | Blocks: 15
  References: existing fake MCP test `tests/unit/legal_ontology/test_mcp_domain_tools.py:33`; integration MCP tests `tests/integration/legal_ontology/test_mcp_tools.py`; current focused MCP evidence `.omo/evidence/debtor-context-graph/focused-mcp-tests.txt`.
  Acceptance criteria: `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_debtor_context_tools.py tests/integration/legal_ontology/test_debtor_context_pipeline.py -q` passes. Existing `test_mcp_domain_tools.py` and `test_mcp_tools.py` also pass after expected tool list updates.
  QA scenarios: happy: fake MCP route candidate call saves `.omo/evidence/debtor-context-graph-v0/task-13-fake-mcp-happy.json`; failure: attempted `authorization` argument or outside-root path is rejected, evidence `.omo/evidence/debtor-context-graph-v0/task-13-fake-mcp-failure.txt`.
  Commit: Y | `test(legal-graph): add debtor context integration tests`

- [ ] 14. Document Debtor Context Graph v0 operator/developer contract
  What to do / Must NOT do: Add docs under `docs/product/debt-collection-ontology/`, recommended `debtor-context-graph-v0.md`. Explain graph model, CLI usage, MCP tools, redaction policy, route candidate status semantics, evidence paths, and known limitations. Do not edit unrelated existing deployment runbooks except to link if necessary.
  Parallelization: Wave 3 | Blocked by: 10, 11 | Blocks: 15
  References: `.omo/research/debtor-context-graph/SYNTHESIS.md`; existing docs in `docs/product/debt-collection-ontology/`; current MCP guide dirty files are out of scope unless deliberately included.
  Acceptance criteria: `rg -n "DebtorContextGraph|assemble_debtor_documents|list_debtor_route_candidates|raw_text_included" docs/product/debt-collection-ontology/debtor-context-graph-v0.md` finds expected sections; PII scan over doc returns no findings.
  QA scenarios: happy: run documented synthetic CLI and save transcript `.omo/evidence/debtor-context-graph-v0/task-14-docs-smoke.txt`; failure: doc check script or `rg` proves no raw OCR path examples include personal identifiers, evidence `.omo/evidence/debtor-context-graph-v0/task-14-docs-pii.txt`.
  Commit: Y | `docs(legal-graph): document debtor context graph v0`

- [ ] 15. Run real OCR eval pack and final evidence generation
  What to do / Must NOT do: Run final pipeline over `/Users/cosmos/dev/ocr/MinerU/work/legal_ocr_20260630` with PII-safe summary output only. Produce final evidence pack under `.omo/evidence/debtor-context-graph-v0/` including assembly summary, debtor graph summary, route candidate summary, MCP tool list, focused tests, PII scan, and dirty worktree scope note. Do not commit raw real OCR outputs containing text/excerpts.
  Parallelization: Wave 3 final | Blocked by: all prior | Blocks: final verification
  References: `.omo/evidence/debtor-context-graph/ocr-corpus-shape.json`; `.omo/evidence/debtor-context-graph/ocr-classifier-coverage.json`; `.omo/evidence/debtor-context-graph/pii-redaction-scan.txt`; final command pattern from this plan.
  Acceptance criteria: final focused pytest command passes; JSON evidence validates; PII scan returns `NO_FINDINGS`; `git diff --check` passes; evidence summary states how many pages, assemblies, snapshots, route candidates, review items, and unknowns were produced.
  QA scenarios: happy: final eval evidence `.omo/evidence/debtor-context-graph-v0/final-real-ocr-eval.json`; failure: final adversarial PII scan `.omo/evidence/debtor-context-graph-v0/final-pii-scan.txt` returns `NO_FINDINGS`, and outside-root MCP path probe rejects without leak in `.omo/evidence/debtor-context-graph-v0/final-mcp-path-failure.json`.
  Commit: Y | `test(legal-graph): add debtor context eval evidence`

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.
- [ ] F1. Plan compliance audit
  - Verify every todo acceptance criterion has corresponding command output or evidence file.
  - Verify no todo touched out-of-scope dirty deployment files unless explicitly approved in a later scope change.
  - Evidence: `.omo/evidence/debtor-context-graph-v0/final-plan-compliance.md`.
- [ ] F2. Code quality review
  - Review changed Python modules for file size, deterministic hashing, no raw text persistence, no broad exception swallowing, and no SDK import creep.
  - Run `/opt/homebrew/bin/python3 -m py_compile` over all changed Python modules/tests.
  - Evidence: `.omo/evidence/debtor-context-graph-v0/final-code-review.md`.
- [ ] F3. Real manual QA
  - Run the final CLI over the real OCR corpus in summary-only mode.
  - Run fake MCP calls for new debtor graph tools against repo-root test fixtures.
  - Run outside-root path rejection probe.
  - Evidence: `.omo/evidence/debtor-context-graph-v0/final-manual-qa.md`.
- [ ] F4. Scope fidelity
  - Confirm no raw OCR text, real personal identifiers, debtor contact action, court filing action, or production storage mutation occurred.
  - Confirm existing 16 MCP tools still work and new tools are additive.
  - Evidence: `.omo/evidence/debtor-context-graph-v0/final-scope-fidelity.md`.

## Commit strategy
- Commit per todo or small dependency pair. Do not squash unrelated waves while work is still moving.
- Preferred commit sequence:
  - `feat(legal-graph): add debtor context graph schema`
  - `feat(legal-graph): add OCR document assembly builder`
  - `test(legal-graph): add OCR assembly fixtures`
  - `feat(legal-routes): add route and legal source resources`
  - `feat(legal-graph): add document assembly CLI`
  - `feat(legal-graph): build debtor context graphs`
  - `feat(legal-graph): add debtor graph snapshot diffs`
  - `feat(legal-routes): evaluate debtor route candidates`
  - `feat(legal-routes): attach stop gates and legal sources`
  - `feat(legal-graph): add debtor context CLI`
  - `feat(legal-mcp): expose debtor context graph tools`
  - `feat(legal-governance): add debtor graph review hooks`
  - `test(legal-graph): add debtor context integration tests`
  - `docs(legal-graph): document debtor context graph v0`
  - `test(legal-graph): add debtor context eval evidence`
- Stage only owned files for each todo. Keep existing unrelated dirty deployment files untouched.
- Do not commit `.pyc` files or real OCR raw text.

## Success criteria
- A real OCR root can be summarized into deterministic redacted `DocumentAssembly` evidence.
- A synthetic fixture can build a full `DebtorContextGraph` with stable `debtor_graph_id`, `graph_snapshot_id`, fact assertions, case packets, stop gates, and route candidates.
- Real OCR summary eval produces page/assembly/graph/route/review counts without raw text or PII leakage.
- Route candidates include required facts, missing facts, blockers, legal source refs, and `no_direct_execution=true`.
- Korean-law source metadata is represented through curated JSON resources with lawId/MST/article/effective date, not live legal lookups during tests.
- MCP exposes additive debtor graph tools through the same redacted envelope and repo-root path boundary.
- Existing 16 MCP tools and focused MCP tests continue to pass.
- Final PII scan returns `NO_FINDINGS`.
- Final `git diff --check` passes.
