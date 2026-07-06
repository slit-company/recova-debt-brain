---
slug: debt-collection-domain-ontology-v1
status: plan-written
intent: clear
pending-action: write .omo/plans/debt-collection-domain-ontology-v1.md
approach: claim-centered integrated legal + finance + workflow domain ontology v1, grounded in the v2 practical manual and Korean-law MCP curated source evidence
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
| root boundary | `Claim` / `Receivable` is the v1 ontology root; `DebtorContextGraph` remains the runtime memory graph root. | Preserves completed debtor-context graph v0 while making the new domain brain claim-centered. | reversible only through explicit migration plan |
| Korean-law MCP role | Use Korean-law MCP for source discovery/verification, then commit curated JSON sources; do not make deterministic tests call live law MCP. | Keeps judgments reproducible and matches current resource pattern. | reversible only with broader runtime-dependency decision |
| execution boundary | Model draftable action packet schemas for future human review, but keep v1 non-executing: no court filing, debtor contact, payment demand, or direct collection action. | User wants the bold direction; action packet shape is useful for future agents, but execution would exceed the safe v1 boundary. | reversible in later product phase |
| first depth target | Optimize v1 for a claim-centered domain brain: route decisions, end-to-end workflow states, evidence requirements, legal/financial blockers, priority scoring, and next-best-action guidance. | This matches the user's "채권 중심 도메인" framing and the v2 manual's practical scope. | reversible |
| accounting depth | Include finance/accounting entities, calculation contracts, deterministic validation fixtures, and a minimal fixture calculator for explicit amount/rate/period/payment/allocation cases. | Bold enough to shape the ontology correctly without hiding production ledger mutation inside route-resource work. | reversible |
| v1 resource versioning | Create new v1 resource files; treat v0 resources as read-only inputs, compatibility fixtures, and regression references. | Prevents accidental breakage of accepted debtor graph and MCP surfaces. | reversible only with migration plan |

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
- Root boundary is resolved: `Claim` / `Receivable` is the ontology root, while `DebtorContextGraph` remains the runtime graph root. The implementation must add a compatibility adapter instead of rewriting debtor identity/snapshot behavior.
- Include action packet schemas as modeled future review artifacts, but do not execute them.
- Include finance/accounting calculation contracts, fixtures, and minimal deterministic calculations for explicit test cases, but keep production ledger mutation out of scope.
- Add four read-only MCP tools for claim-domain reasoning after the existing 21 tools unless a security review blocks one with an explicit deferral.

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
Resolved by user direction and adopted recommendation:

- Primary optimization target: bold claim-centered domain brain, including route decisions and end-to-end workflow states.
- High-risk action modeling: include draftable action packet schemas for future human review, but keep execution disabled.
- Accounting depth: include finance/accounting entities, calculation contracts, fixtures, and a minimal deterministic fixture calculator; production ledger mutation remains out of scope.
- Claim-centered identity boundary: model `Claim` / `Receivable` as the v1 ontology root, with Debtor, CasePacket, DocumentAssembly, LegalStatus, LedgerFacts, AssetHints, WorkflowState, and RouteCandidates as connected children. Keep `DebtorContextGraph` as the runtime memory graph root and add an adapter.
- MCP exposure: add read-only claim-domain tools after the existing 21 tools, with the existing tool order preserved.

No blocking product questions remain for the plan.

## Approval gate
status: plan-written
plan: `.omo/plans/debt-collection-domain-ontology-v1.md`
metis-review: completed; required fixes folded into plan and draft.
