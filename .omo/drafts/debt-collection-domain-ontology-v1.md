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
| ontology shape | Plan one integrated, claim-centered domain ontology with separate cross-linked layers: legal, finance, workflow, evidence, route, StopGate/compliance, scoring, and action packet schemas. | User explicitly chose a bold integrated direction; v2 manual is structured as an integrated practice workflow. | reversible before implementation |
| Korean-law MCP role | Use Korean-law MCP for source discovery/verification, then commit curated JSON sources; do not make deterministic tests call live law MCP. | Keeps judgments reproducible and matches current resource pattern. | reversible only with broader runtime-dependency decision |
| execution boundary | Model draftable action packet schemas for future human review, but keep v1 non-executing: no court filing, debtor contact, payment demand, or direct collection action. | User wants the bold direction; action packet shape is useful for future agents, but execution would exceed the safe v1 boundary. | reversible in later product phase |
| first depth target | Optimize v1 for a claim-centered domain brain: route decisions, end-to-end workflow states, evidence requirements, legal/financial blockers, priority scoring, and next-best-action guidance. | This matches the user's "채권 중심 도메인" framing and the v2 manual's practical scope. | reversible |
| accounting depth | Include finance/accounting entities, calculation contracts, and deterministic validation fixtures where feasible; defer production-grade ledger reconciliation unless the plan review proves it is small enough. | Bold enough to shape the ontology correctly without hiding a full accounting engine inside a route-resource task. | reversible |

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
- User chose the bold direction: v1 should be a claim-centered Recova domain brain, not merely a narrow route recommendation expansion.
- Include action packet schemas as modeled future review artifacts, but do not execute them.
- Include finance/accounting calculation contracts and fixtures where feasible, but keep production ledger mutation out of scope.

## Scope IN
- Integrated debt-collection domain ontology v1.
- Claim-centered ontology model: claim/receivable lifecycle as the main organizing axis, connected to debtors, documents, evidence, legal status, assets, workflows, routes, and review decisions.
- Legal source expansion with Korean-law MCP evidence captured into curated JSON.
- Finance/claim/accounting concepts needed for route judgment.
- Finance/accounting calculation contracts for principal, interest, late damages, costs, payments, allocation, and remaining balance where feasible.
- Practical workflow states and first-case intake classification.
- Route catalog expansion from the v2 manual.
- Route decision table with required facts, missing facts, blockers, StopGates, legal refs, evidence refs, and priority/scoring metadata.
- Draftable action packet schemas for later human review, including legal-action packet, evidence-request packet, contact-review packet, and monitoring packet concepts.
- DebtorContextGraph integration through stable fact handles and route handles.
- Validators, tests, PII-safe evidence, and docs.

## Scope OUT (Must NOT have)
- No actual court filing, debtor contact, payment demand, direct execution, or production collection action.
- No raw OCR text, real personal identifiers, phone numbers, resident-registration-number patterns, account numbers, or sensitive source paths in evidence.
- No live Korean-law MCP calls in deterministic tests.
- No Supabase/remote storage/deployment work unless the user explicitly changes scope.
- No breaking or removing existing 21 MCP tools.
- No unrelated deployment/runbook dirty-file edits.
- No production-grade accounting ledger mutation or authoritative balance recalculation unless explicitly scoped as a separate execution task.

## Open questions
Resolved by user direction:

- Primary optimization target: bold claim-centered domain brain, including route decisions and end-to-end workflow states.
- High-risk action modeling: include draftable action packet schemas for future human review, but keep execution disabled.
- Accounting depth: include finance/accounting entities and calculation contracts; decide during plan review whether to implement a minimal deterministic calculator in v1 or leave it as schema/validator only.

Remaining interview question:

1. Claim-centered identity boundary:
   - Recommended: model `Claim` / `Receivable` as the primary root, with Debtor, CasePacket, DocumentAssembly, LegalStatus, LedgerFacts, AssetHints, WorkflowState, and RouteCandidates as connected children.
   - Alternative: keep `DebtorGraph` as the root and attach one or more Claim nodes under it.
   - Why it matters: this affects IDs, graph merge rules, MCP query shape, and how Recova handles one debtor with multiple claims.

## Approval gate
status: interviewing
<!-- When exploration is exhausted and unknowns are answered, set status: awaiting-approval. -->
<!-- That durable record is the loop guard: on a later turn read it and resume at the gate instead of re-running exploration. -->
