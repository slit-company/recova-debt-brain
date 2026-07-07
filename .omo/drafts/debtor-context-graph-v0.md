---
slug: debtor-context-graph-v0
status: plan-written
intent: clear
pending-action: start work only after explicit user command, for example `$omo:start-work .omo/plans/debtor-context-graph-v0.md`
approach: Add a real-debtor graph layer in `trustgraph_legal` without replacing existing case graph/MCP primitives: page-level OCR -> document assembly -> debtor graph snapshot -> route candidates -> MCP facade.
---

# Draft: debtor-context-graph-v0

## Components (topology ledger)
<!-- Lock the SHAPE before depth. One row per top-level component that can succeed or fail independently. -->
<!-- id | outcome (one line) | status: active|deferred | evidence path -->
- C1 `DocumentAssembly`: Convert page-level OCR files into grouped legal documents and procedure episodes; active; evidence `.omo/evidence/debtor-context-graph/ocr-corpus-shape.json`, `.omo/evidence/debtor-context-graph/ocr-classifier-coverage.json`.
- C2 `DebtorContextGraph`: Build versioned debtor/case graph snapshots from assembled documents and existing field/classifier output; active; evidence `trustgraph_legal/case_graph.py:50`, `trustgraph_legal/case_graph.py:109`.
- C3 `RouteOntology`: Add route templates and route-candidate matching for long-term debt-collection paths; active; evidence `.omo/evidence/debtor-context-graph/route-manual-summary.json`.
- C4 `LegalRuleSource`: Store law MCP-derived rule-source metadata with lawId/MST/article/effective date and route/check use; active; evidence `.omo/evidence/debtor-context-graph/korean-law-source-map.json`.
- C5 `MCPDebtorTools`: Expose debtor graph read/build/explain surfaces through existing redacted MCP envelope while keeping adapter thin; active; evidence `trustgraph_legal/mcp_domain.py:21`, `trustgraph_legal/mcp_domain.py:97`.
- C6 `EvalHarness`: Prove the system on the real OCR corpus and fixed synthetic failure cases without leaking raw OCR/PII; active; evidence `.omo/evidence/debtor-context-graph/pii-redaction-scan.txt`, `.omo/evidence/debtor-context-graph/focused-mcp-tests.txt`.

## Open assumptions (announced defaults)
<!-- Record any default you adopt instead of asking, so the user can veto it at the gate. -->
<!-- assumption | adopted default | rationale | reversible? -->
- Implementation location | Put domain logic under `trustgraph_legal`, not `trustgraph-mcp`; MCP layer only registers/routs new tools | Existing accepted MCP contract keeps `trustgraph_legal.mcp_domain` as SDK-independent boundary and adapter thin | reversible.
- First build target | Start with local/repo-root deterministic CLI + tests over `/Users/cosmos/dev/ocr/MinerU/work/legal_ocr_20260630`; do not attach production storage in v0 | Current MCP status says production ingest backend is not configured, and OCR evidence is local | reversible.
- Route knowledge split | Create a separate route/rule resource rather than bloating `resources/ontologies/recova-debt-collection.json` first | Existing ontology covers document/case/StopGate basics; route templates change faster and need tuning | reversible.
- Legal source policy | Use curated rule-source JSON from korean-law MCP metadata, not live legal lookup inside every graph build | Deterministic tests need stable law source versions; future versions can be marked for review | reversible.
- Test strategy | TDD for schemas/builders plus focused integration after each todo | Data-shape bugs here are expensive and current suite is already pytest-based | reversible.
- Raw output policy | Graph/MCP outputs stay redacted and source-ref based; raw OCR text is read during local processing but not persisted in evidence or MCP responses | Existing MCP contract and PII scan use this boundary | partly reversible.

## Findings (cited - path:lines)
- Existing `build_case_graph` accepts a manifest, loads documents, classifies/extracts fields, and returns one `CaseGraphPayload`; it is fixture-manifest shaped, not real OCR-bundle shaped: `trustgraph_legal/case_graph.py:50`, `trustgraph_legal/case_graph.py:78`, `trustgraph_legal/case_graph.py:99`.
- Existing case graph already has a useful internal shape to reuse: evidence keys, documents, entities, edges, findings, identity resolution: `trustgraph_legal/case_graph.py:109`, `trustgraph_legal/case_graph.py:119`, `trustgraph_legal/case_graph.py:136`.
- Existing classifier canonical document types cover 9 known buckets plus `unknown`: `trustgraph_legal/classifier_types.py:37`, `trustgraph_legal/classifier_types.py:56`.
- Existing classifier payload includes evidence spans and `pii_profile.raw_text_included=false`, but real OCR analysis must not persist excerpt payloads because OCR can contain personal identifiers: `trustgraph_legal/classifier_types.py:70`, `trustgraph_legal/classifier_types.py:99`.
- Existing MCP facade has 16 tools and redacted output schema, so new debtor graph tools should join this surface rather than create a second MCP system: `trustgraph_legal/mcp_domain.py:21`, `trustgraph_legal/mcp_domain.py:97`, `trustgraph_legal/mcp_domain.py:121`.
- OCR corpus is page-level: 211 files, 208 markdown files, `manifest.tsv` present, and 5,393 markdown lines: `.omo/evidence/debtor-context-graph/ocr-corpus-shape.json`.
- Current classifier coverage on the real OCR corpus is 30 `attachment-collection-order`, 178 `unknown`; this proves `DocumentAssembly` must precede richer route recommendation: `.omo/evidence/debtor-context-graph/ocr-classifier-coverage.json`.
- Route manual extraction produced 18 route candidates and supports modeling routes as templates with required facts/blockers/legal sources: `.omo/evidence/debtor-context-graph/route-manual-summary.json`.
- Korean-law MCP evidence maps 18 legal sources and records lawId/MST/effective dates; legal knowledge should be curated/versioned, not prompt-only memory: `.omo/evidence/debtor-context-graph/korean-law-source-map.json`.
- Existing MCP regression evidence passed 9 focused tests and reports 16 tools: `.omo/evidence/debtor-context-graph/focused-mcp-tests.txt`, `.omo/evidence/debtor-context-graph/recova-mcp-tools.json`.
- Dirty worktree exists outside this planning scope in deployment docs/scripts and deploy artifacts; implementation plan must not touch those paths: `git status --short --branch` current snapshot.

## Decisions (with rationale)
- Plan intent is CLEAR: desired outcome is a per-debtor event/memory graph for one debtor's continuing debt-collection case, not a broad product redesign.
- Planning size is Architecture: touches OCR ingestion, graph schema, ontology/rule resources, MCP facade, tests, and eval evidence.
- Subagents were not spawned for this planning turn because current tool policy requires explicit user request for subagents; local CodeGraph/read-only evidence was sufficient.
- Recommended graph shape is hybrid: `DebtorGraph` as the stable person-level memory container, with one-or-many `CasePacket` children for individual claims/procedures. This is the default unless the user vetoes it.
- Recommended first implementation is not storage/backend integration. It is deterministic local build + schema + MCP read/build facade over repo-root inputs, because the current proof says production ingest backend is not attached.
- User approved recommended defaults: stable debtor-level graph, redacted identity/source-ref output policy, and local deterministic v0 before storage.

## Scope IN
- Add a planning specification for a v0 implementation that creates `DocumentAssembly`, `DebtorContextGraph`, `FactAssertion`, `GraphSnapshot`, and `RouteCandidate` concepts.
- Plan deterministic CLI and pytest coverage over `/Users/cosmos/dev/ocr/MinerU/work/legal_ocr_20260630`.
- Plan route templates from the extracted 18 route candidates and legal-source metadata from korean-law MCP evidence.
- Plan MCP additions that remain redacted, repo-root bounded, and SDK-independent in tests.
- Plan validation artifacts under `.omo/evidence/debtor-context-graph-v0/`.

## Scope OUT (Must NOT have)
- No production code implementation in this planning turn.
- No raw OCR source text or resident-registration-number/phone/account-like identifiers in plan evidence.
- No direct court filing, debtor contact, or automated collection action.
- No mutation of unrelated existing deployment docs/scripts or current untracked deployment artifacts.
- No live Supabase/remote persistence requirement in v0 unless user explicitly chooses it.
- No replacement of existing 16 MCP tools; new tools must be additive or explicitly compatible.

## Open questions
- Q1 Identity boundary: RESOLVED by user approval. v0 creates one stable `DebtorGraph` per natural/legal person with multiple `CasePacket` children, not one graph per claim/case only.
  - Recommended: stable `DebtorGraph` with many `CasePacket`s. Why: the user said "채무자 한 명" and long-term collection needs cross-case memory.
- Q2 PII/raw identity policy: RESOLVED by user approval. v0 stores redacted identity keys plus source refs in graph/MCP outputs; raw OCR stays in source files/vault only.
  - Recommended: redacted graph payload with deterministic identity keys and source refs; raw OCR stays in source files/vault only. Why: it keeps MCP safe while still letting the graph remember the debtor through stable IDs.
- Q3 First implementation boundary: RESOLVED by user approval. v0 stops at local deterministic CLI/tests and additive MCP facade; persistent storage/Supabase is a later plan.
  - Recommended: local deterministic CLI + tests first; storage second. Why: current blocker is document assembly/graph shape, not database persistence.

## Approval gate
status: approved
approved-by-user: "너의 추천 선택대로해줘."
pending-action: plan written at `.omo/plans/debtor-context-graph-v0.md`; start implementation only after explicit user command.
<!-- When exploration is exhausted and unknowns are answered, set status: awaiting-approval. -->
<!-- That durable record is the loop guard: on a later turn read it and resume at the gate instead of re-running exploration. -->
