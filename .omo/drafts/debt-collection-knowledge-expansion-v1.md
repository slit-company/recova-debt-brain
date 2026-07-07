---
slug: debt-collection-knowledge-expansion-v1
status: goal4-complete-final-eval-pending
intent: clear
pending-action: run G011 docs, final eval, and acceptance review
approach: skip remote deployment/client docs for now; expand the accepted local claim-domain brain with article-level legal-source hardening, rare scenario fixtures, finance-source research plus finance/review regressions, and human-review workflow contracts. User does not want to specify more details; the plan should rely on MCP/web/source research.
---

# Draft: debt-collection-knowledge-expansion-v1

## Components (topology ledger)

| id | outcome | status | evidence path |
| --- | --- | --- | --- |
| legal-source-precision | Remaining review-needed source refs are replaced or explicitly retained as non-article review contracts. | accepted | `.omo/evidence/debt-collection-knowledge-expansion-v1/task-1-*`, `task-3-*` |
| scenario-expansion | Synthetic claim-domain cases cover rare assets, insolvency/recovery, protected-property, inheritance, hidden assets, and finance ambiguity. | accepted | `.omo/evidence/debt-collection-knowledge-expansion-v1/task-2-*`, `task-3-*` |
| finance-review-depth | Ambiguous balances, assignment, surety, subrogation, and payment allocation remain review-safe. | accepted | `.omo/evidence/debt-collection-knowledge-expansion-v1/task-4-finance-review-*` |
| operator-review-workflow | Action packets/governance records have a human-review state contract with audit and forbidden-field gates. | accepted | `.omo/evidence/debt-collection-knowledge-expansion-v1/task-2-*`, `task-4-*` |
| integrated-eval | Domain decision, StopGate, route, finance, docs, and local MCP compatibility remain accepted. | pending | `.omo/evidence/debt-collection-knowledge-expansion-v1/final-*` |
| remote-mcp-deployment | Deploy updated server, remote smoke, and client setup docs. | deferred | Existing recova-mcp-deployment evidence only; out of this plan. |

## Open assumptions (announced defaults)

| assumption | adopted default | rationale | reversible? |
| --- | --- | --- | --- |
| User wants to skip previous Next Work 1-3. | Remote MCP deploy, remote smoke, and client docs are scope OUT. | User said "1-3 건너 뛰고 그다음 단계로 가고 싶은딩." | Yes |
| Next useful wave is knowledge content, not infrastructure. | Plan around legal source precision, rare scenarios, finance/review regressions, and operator review workflow. | Local ontology v1 is accepted; the highest value gap is professional depth. | Yes |
| `recova-privacy-purpose-v0` may not map to a single article. | Replace with article refs where possible, otherwise keep explicit review-required non-article contract metadata. | Current resource says it is a privacy-purpose domain contract, not a single statute article. | Yes |
| Execution remains forbidden. | Human-review workflow models review/approval records only, not filing/contact/payment execution. | Current docs and action packet schemas are non-executing. | Yes |
| User does not want to drive more detailed planning interviews. | Research-first: use Korean-law MCP, repo evidence, official/public web sources, and available MCP discovery. | User said the core is for Codex to investigate carefully rather than ask them to define scenarios. | Yes |
| Finance-specific MCP availability is uncertain. | Inspect tool availability first; if no finance-specific MCP exists, use official/public web sources plus Korean-law MCP and freeze adopted refs. | Current tool discovery surfaces Korean-law MCP and Recova domain MCP, but not a dedicated finance MCP. | Yes |

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
- Korean-law MCP search confirms current law identifiers for `민사집행법`, `채무자 회생 및 파산에 관한 법률`, `채권의 공정한 추심에 관한 법률`, and `이자제한법`.
- Korean-law MCP `discover_tools` did not expose a finance-specific tool for "금융 이자 채권추심 변제충당 법정이율 금융감독원"; it exposed legal categories instead.
- Web/source discovery found official candidates for finance/procedure grounding: 국가법령정보센터/law.go.kr, 대한민국 법원 전자소송/ecfs.scourt.go.kr, 금융감독원/fss.or.kr, and 한국은행/bok.or.kr.

## Decisions (with rationale)

- 2026-07-07: Skip remote deployment and client setup work for this wave. Rationale: user explicitly wants to move past Next Work 1-3 and deepen the brain itself.
- 2026-07-07: Treat legal source precision and scenario expansion as one wave. Rationale: routes, StopGates, finance review, and action packets only become trustworthy when tested together.
- 2026-07-07: Keep Korean-law MCP as a discovery/evidence tool, not a deterministic test dependency. Rationale: this matches the accepted v1 resource-correctness pattern.
- 2026-07-07: Keep execution forbidden. Rationale: current product contract is advisory/human-review only; production boundary decision remains separate.
- 2026-07-07: Do not ask the user to enumerate more practical scenarios unless a true owner decision appears. Rationale: user explicitly prefers Codex-led investigation.
- 2026-07-07: Finance judgment research will not assume a finance MCP exists. Rationale: tool discovery did not reveal one; official/public web and legal MCP are sufficient for the next planning wave, with any adopted source frozen into static resources.
- 2026-07-07: Goal 4 decision/StopGate/finance hardening is accepted and pushed on master through `d2310533`. Rationale: A finance review hardening, B StopGate proof safety, C contract review, 52 focused tests, Python 3.9 compile, basedpyright, MCP order, PII/path, deployment-boundary, and LOC checks all passed.

## Current implementation status

- Complete: G007 legal and finance source research foundation.
- Complete: G008 scenario coverage and human-review contract foundation.
- Complete: G009 resource and fixture expansion.
- Complete: G010 decision, StopGate, finance, and review hardening.
- Remaining: G011 docs, final eval, and acceptance review.

## Next work

1. Update the working log and product docs so they describe the accepted knowledge-expansion state, not the pre-work plan.
2. Run final focused tests, JSON validation, PII/path scan, Python compile/type checks where applicable, and local MCP 25-tool order smoke.
3. Produce a final review artifact that says either ACCEPTED or BLOCKED with reproduced evidence.
4. Keep remote MCP deployment, live remote smoke, and client setup docs out of scope unless the user explicitly brings them back.

## Scope IN

- Legal-source audit and replacement/disposition for review-needed refs.
- Scenario coverage inventory and rare-case synthetic fixture expansion.
- Finance-source research, finance ambiguity, and human-review regression tests.
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
status: goal4-complete-g011-next
