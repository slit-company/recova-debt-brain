---
slug: debt-collection-domain-ontology-v1
status: drafting
intent: clear
pending-action: write .omo/plans/debt-collection-domain-ontology-v1.md
approach: integrated legal + finance + workflow domain ontology v1, grounded in the v2 practical manual and Korean-law MCP curated source evidence
---

# Draft: debt-collection-domain-ontology-v1

## Components (topology ledger)
<!-- Lock the SHAPE before depth. One row per top-level component that can succeed or fail independently. -->
<!-- id | outcome (one line) | status: active|deferred | evidence path -->
| domain-source-ingest | Convert the user's v2 practical manual into route, workflow, fact, evidence, and compliance candidates without raw PII. | active | `/Users/cosmos/Downloads/채권추심_장기채권_법조치_루트_총정리_v2_실무확장판 (1).md` |
| legal-source-map | Expand and verify law/article/source metadata through Korean-law MCP, then freeze curated versioned resources. | active | `resources/legal_rules/debt_collection_route_sources_v0.json` |
| finance-claim-model | Add finance/accounting concepts needed for collection reasoning: principal, interest, late damages, costs, payments, allocation, assignment, guarantee. | active | `resources/ontologies/recova-debt-collection.json` |
| workflow-decision-model | Model intake, evidence checks, route selection, failure fallback, review queues, and next-step recommendations. | active | `.omo/notes/recova-brain-working-log.md` |
| route-decision-table | Expand route catalog and encode required facts, blockers, legal sources, priority scoring, and advisory-only semantics. | active | `resources/legal_routes/debt_collection_routes_v0.json` |
| graph-integration | Connect DebtorContextGraph facts/snapshots/governance to the new domain ontology handles without breaking existing MCP tools. | active | `.omo/plans/debtor-context-graph-v0.md` |
| validation-evidence | Add validators, focused tests, final PII/path scans, and evidence reports for all new resources and decisions. | active | `.omo/evidence/debtor-context-graph-v0/final-real-ocr-eval.json` |

## Open assumptions (announced defaults)
<!-- Record any default you adopt instead of asking, so the user can veto it at the gate. -->
<!-- assumption | adopted default | rationale | reversible? -->
| ontology shape | Plan one integrated domain ontology with separate cross-linked layers: legal, finance, workflow, evidence, route, StopGate/compliance. | User explicitly noted these are connected; v2 manual is structured as an integrated practice workflow. | reversible before implementation |
| Korean-law MCP role | Use Korean-law MCP for source discovery/verification, then commit curated JSON sources; do not make deterministic tests call live law MCP. | Keeps judgments reproducible and matches current resource pattern. | reversible only with broader runtime-dependency decision |
| execution boundary | Keep v1 advisory-only: no court filing, debtor contact, payment demand, or direct collection execution. | Existing v0 MCP and route contracts enforce no direct execution; safer and compatible. | reversible in later product phase |
| first depth target | Optimize v1 for route recommendation, evidence requirements, legal/financial blockers, and next-step guidance; defer full automation. | Highest leverage for agent "brain" quality. | reversible |
| accounting depth | Include finance concepts and validation hooks, but defer full ledger-calculation engine unless user explicitly prioritizes it. | Full accounting engine is a large separate subsystem. | reversible |

## Findings (cited - path:lines)
- The v2 manual is 2,125 lines and covers end-to-end long-term debt collection practice, from legal baseline through route catalog and Recova recommendation engine fields.
- The v2 manual's top-level structure includes legal baseline, first intake, limitation, information sources, voluntary recovery, title acquisition, provisional remedies, bank/wage/housing/business/real-estate/vehicle/insurance/tax/inheritance/fraudulent-transfer/special-asset routes, welfare exclusions, property disclosure/inquiry/default registry, insolvency filters, operating scenarios, recommendation rules, scoring, mistakes, and legal checklist.
- Existing route resources are already advisory-only and reference curated legal source IDs: `resources/legal_routes/debt_collection_routes_v0.json`.
- Existing legal route sources already store law name, lawId, MST, article, effective date, retrieval status, review status, graph use, route use, and source refs: `resources/legal_rules/debt_collection_route_sources_v0.json`.
- Debtor Context Graph v0 is complete and accepted with 21 MCP tools, 208-page real OCR summary eval, final PII/path scan, and T final review accepted: `.omo/plans/debtor-context-graph-v0.md`, `.omo/evidence/debtor-context-graph-v0/final-real-ocr-eval.json`, `.omo/teams/debtor-context-graph-v0-20260706/artifacts/T-final-contract-review.md`.

## Decisions (with rationale)
- Treat legal, finance, and workflow as one integrated ontology planning scope, not three separate plans.
- Keep implementation resources layered and cross-linked so each layer can be validated independently.
- Use the v2 manual as the practical workflow seed and Korean-law MCP as the legal source verification tool.
- Keep all outputs PII-safe and advisory-only in v1.
- Preserve existing DebtorContextGraph and MCP contracts; v1 should extend domain reasoning without breaking the 21-tool surface.

## Scope IN
- Integrated debt-collection domain ontology v1.
- Legal source expansion with Korean-law MCP evidence captured into curated JSON.
- Finance/claim/accounting concepts needed for route judgment.
- Practical workflow states and first-case intake classification.
- Route catalog expansion from the v2 manual.
- Route decision table with required facts, missing facts, blockers, StopGates, legal refs, evidence refs, and priority/scoring metadata.
- DebtorContextGraph integration through stable fact handles and route handles.
- Validators, tests, PII-safe evidence, and docs.

## Scope OUT (Must NOT have)
- No actual court filing, debtor contact, payment demand, direct execution, or production collection action.
- No raw OCR text, real personal identifiers, phone numbers, resident-registration-number patterns, account numbers, or sensitive source paths in evidence.
- No live Korean-law MCP calls in deterministic tests.
- No Supabase/remote storage/deployment work unless the user explicitly changes scope.
- No breaking or removing existing 21 MCP tools.
- No unrelated deployment/runbook dirty-file edits.

## Open questions
1. Primary optimization target for v1:
   - Recommended: route recommendation + evidence requirements + legal/financial blockers.
   - Alternative: full end-to-end collector operating workflow from intake to monitoring.
   - Why it matters: this decides whether v1 prioritizes decision tables and route eligibility, or broader work-queue/orchestration states.
2. High-risk action modeling:
   - Recommended: advisory-only route/action candidates with human-review notes.
   - Alternative: model draftable action packets for future human review, while still not executing.
   - Why it matters: this affects schemas for future documents, court packets, contact packets, and approval workflow.
3. Accounting depth:
   - Recommended: finance concepts and evidence validation hooks only in v1.
   - Alternative: include a full calculation engine for principal, interest, late damages, costs, payments, allocation, and remaining balance.
   - Why it matters: full calculations require different tests, fixtures, and legal/financial edge-case coverage.

## Approval gate
status: interviewing
<!-- When exploration is exhausted and unknowns are answered, set status: awaiting-approval. -->
<!-- That durable record is the loop guard: on a later turn read it and resume at the gate instead of re-running exploration. -->
