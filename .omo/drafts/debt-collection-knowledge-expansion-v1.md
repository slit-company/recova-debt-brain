---
slug: debt-collection-knowledge-expansion-v1
status: awaiting-start-work
intent: clear
pending-action: run start-work on .omo/plans/debt-collection-knowledge-expansion-v1.md
approach: skip remote deployment/client docs for now; expand the accepted local claim-domain brain with article-level legal-source hardening, rare scenario fixtures, finance/review regressions, and human-review workflow contracts.
---

# Draft: debt-collection-knowledge-expansion-v1

## Components (topology ledger)

| id | outcome | status | evidence path |
| --- | --- | --- | --- |
| legal-source-precision | Remaining review-needed source refs are replaced or explicitly retained as non-article review contracts. | active | `.omo/evidence/debt-collection-knowledge-expansion-v1/task-1-*`, `task-4-*` |
| scenario-expansion | Synthetic claim-domain cases cover rare assets, insolvency/recovery, protected-property, inheritance, hidden assets, and finance ambiguity. | active | `.omo/evidence/debt-collection-knowledge-expansion-v1/task-2-*`, `task-5-*` |
| finance-review-depth | Ambiguous balances, assignment, surety, subrogation, and payment allocation remain review-safe. | active | `.omo/evidence/debt-collection-knowledge-expansion-v1/task-6-*` |
| operator-review-workflow | Action packets/governance records have a human-review state contract with audit and forbidden-field gates. | active | `.omo/evidence/debt-collection-knowledge-expansion-v1/task-3-*`, `task-8-*` |
| integrated-eval | Domain decision, StopGate, route, finance, docs, and local MCP compatibility remain accepted. | active | `.omo/evidence/debt-collection-knowledge-expansion-v1/final-*` |
| remote-mcp-deployment | Deploy updated server, remote smoke, and client setup docs. | deferred | Existing recova-mcp-deployment evidence only; out of this plan. |

## Open assumptions (announced defaults)

| assumption | adopted default | rationale | reversible? |
| --- | --- | --- | --- |
| User wants to skip previous Next Work 1-3. | Remote MCP deploy, remote smoke, and client docs are scope OUT. | User said "1-3 건너 뛰고 그다음 단계로 가고 싶은딩." | Yes |
| Next useful wave is knowledge content, not infrastructure. | Plan around legal source precision, rare scenarios, finance/review regressions, and operator review workflow. | Local ontology v1 is accepted; the highest value gap is professional depth. | Yes |
| `recova-privacy-purpose-v0` may not map to a single article. | Replace with article refs where possible, otherwise keep explicit review-required non-article contract metadata. | Current resource says it is a privacy-purpose domain contract, not a single statute article. | Yes |
| Execution remains forbidden. | Human-review workflow models review/approval records only, not filing/contact/payment execution. | Current docs and action packet schemas are non-executing. | Yes |

## Findings (cited - path:lines)

- `.omo/notes/recova-brain-working-log.md:362` records the skipped deployment step.
- `.omo/notes/recova-brain-working-log.md:363` records the skipped live remote smoke step.
- `.omo/notes/recova-brain-working-log.md:369` records the skipped client docs update.
- `.omo/notes/recova-brain-working-log.md:370` identifies the next knowledge expansion wave.
- `.omo/notes/recova-brain-working-log.md:374` keeps production execution boundary deferred.
- `resources/legal_rules/debt_collection_domain_sources_v1.json:426` shows `kr-civil-execution-act-v0`.
- `resources/legal_rules/debt_collection_domain_sources_v1.json:443` shows `kr-debtor-rehabilitation-act-v0`.
- `resources/legal_rules/debt_collection_domain_sources_v1.json:460` shows `recova-privacy-purpose-v0`.
- `tests/fixtures/claim-domain-v1/synthetic_claim_states.json:13` shows the current scenario list starts with only the minimized synthetic scenarios.
- `docs/product/debt-collection-ontology/claim-domain-ontology-v1.md:226` defines where new knowledge should be added.
- `docs/product/debt-collection-ontology/claim-domain-ontology-v1.md:241` defines the safe-change checklist.

## Decisions (with rationale)

- 2026-07-07: Skip remote deployment and client setup work for this wave. Rationale: user explicitly wants to move past Next Work 1-3 and deepen the brain itself.
- 2026-07-07: Treat legal source precision and scenario expansion as one wave. Rationale: routes, StopGates, finance review, and action packets only become trustworthy when tested together.
- 2026-07-07: Keep Korean-law MCP as a discovery/evidence tool, not a deterministic test dependency. Rationale: this matches the accepted v1 resource-correctness pattern.
- 2026-07-07: Keep execution forbidden. Rationale: current product contract is advisory/human-review only; production boundary decision remains separate.

## Scope IN

- Legal-source audit and replacement/disposition for review-needed refs.
- Scenario coverage inventory and rare-case synthetic fixture expansion.
- Finance ambiguity and human-review regression tests.
- Domain decision and StopGate regression strengthening.
- Operator review workflow contract for action packets/governance records.
- Working log and product docs updates for this knowledge expansion.
- Final integrated evidence and contract review.

## Scope OUT (Must NOT have)

- Remote MCP deploy.
- Remote live smoke.
- Client-facing remote setup docs update.
- Cloudflare, Vercel, Supabase, VPS, or production hosting work.
- Real collection execution or debtor contact.
- Raw OCR/source text/local path/PII exposure.

## Open questions

- None blocking. If the user later wants a UI prototype rather than a workflow contract, that should become a separate frontend/product-design plan.

## Approval gate
status: approved-by-user-skip-1-3-awaiting-start-work
