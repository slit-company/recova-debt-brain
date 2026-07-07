# debt-collection-knowledge-expansion-v1 - Work Plan

## TL;DR (For humans)
Recova의 채권추심 두뇌를 한 단계 더 깊게 만드는 계획이다. 이미 만든 `DebtorContextGraph`와 `Claim Domain Ontology v1`은 작동한다. 이번에는 그 위에 법령 근거를 더 정밀하게 붙이고, 특수 재산/회생/파산/상속/은닉재산 같은 실무 케이스를 더 많이 먹여서 에이전트가 "왜 이 루트가 가능/보류/불가인지"를 더 전문가처럼 설명하게 만든다.

**What you'll get:** 남아 있는 법령 리뷰 포인트를 기사 단위 근거로 정리하고, 장기채권 실무에서 자주 터지는 희귀 케이스 fixture와 회귀 테스트를 추가한다. 마지막에는 사람 검토자가 action packet과 governance record를 어떻게 보고 승인/반려해야 하는지도 문서와 계약으로 남긴다.

**Why this approach:** 배포나 클라이언트 연결은 잠깐 미뤄도 된다. 지금 더 큰 가치는 두뇌의 내용물이다. 법률, 금융, 업무 플로우, 시나리오를 따로 벌리면 판단 연결고리가 끊기므로, 이번 웨이브에서는 법령 정밀화와 실무 시나리오 확장을 한 번에 묶는다.

**What it will NOT do:** 원격 MCP 배포, live smoke, 클라이언트 연결 문서 업데이트는 하지 않는다. 실제 추심 실행, 법원 제출, 채무자 연락, 송금/변제 요구도 하지 않는다. 원문 OCR, 실명, 전화번호, 계좌형 문자열, 로컬 민감 경로는 출력하지 않는다.

**Effort:** Large
**Risk:** Medium - 이미 검증된 v1 위의 확장이지만, 법령 근거와 route/StopGate/decision table이 동시에 맞아야 하므로 통합 검증이 중요하다.
**Decisions to sanity-check:** 사용자가 Next Work 1-3, 즉 원격 MCP 배포/remote smoke/client docs를 이번 웨이브에서 건너뛰기로 했다. 이번 계획은 지식 확장만 다루며 execution boundary는 계속 non-executing으로 둔다.

Your next move: start execution with `$omo:start-work .omo/plans/debt-collection-knowledge-expansion-v1.md`, preferably with team mode. Full execution detail follows below.

---

> TL;DR (machine): Large/Medium risk. Extend the accepted claim-domain v1 with article-level legal-source hardening, rare-case scenario fixtures, finance/workflow/route decision regressions, and human-review workflow contracts while skipping deployment/client-doc tasks.

## Scope
### Must have
- Explicitly skip the previous working-log Next Work items 1-3:
  - no updated Recova MCP server deployment;
  - no remote MCP `tool_count=25` smoke;
  - no client-facing setup docs update for remote users.
- Keep the accepted baseline intact:
  - 25 MCP tools total in local source, existing 21 first and four claim-domain tools appended;
  - `DebtorContextGraph` remains the runtime memory graph;
  - `Claim` / `Receivable` remains the domain ontology root;
  - action packets remain advisory-only and non-executing.
- Replace or disposition the three remaining `needs_legal_review` source records in `resources/legal_rules/debt_collection_domain_sources_v1.json`:
  - `kr-civil-execution-act-v0`;
  - `kr-debtor-rehabilitation-act-v0`;
  - `recova-privacy-purpose-v0`.
- Use Korean-law MCP during source-discovery evidence where helpful, then freeze results into curated resource JSON. Deterministic tests must not depend on live Korean-law MCP.
- Expand synthetic scenario coverage beyond the current nine minimized claim-domain scenarios, especially:
  - real estate auction / mortgage or priority review;
  - vehicle and movable/business asset execution;
  - lease deposit and housing-related execution;
  - business receivable, card/PG/platform settlement;
  - insurance refund or claim, tax refund, public receivable, compensation/distribution;
  - inheritance and family property;
  - fraudulent transfer, hidden assets, property disclosure/inquiry/default registry;
  - insolvency, rehabilitation, bankruptcy stay/discharge, credit-recovery review;
  - welfare/public-benefit and protected-property exclusion.
- Strengthen route/decision/StopGate regressions so the new source/scenario coverage affects outputs deterministically.
- Add finance-review depth where current routes require it:
  - disputed balance;
  - payment allocation conflict;
  - legal/enforcement cost review;
  - assignment/succession;
  - guarantee/surety;
  - subrogation/reimbursement candidate.
- Design a human-review operator workflow contract for action packets and governance records:
  - queue/review/approve/reject statuses;
  - operator-visible fields;
  - source_refs/evidence_refs only;
  - forbidden debtor contact payload and filing destination fields;
  - audit fields;
  - PII profile.
- Update the working log and relevant product docs to record the new planning decision and resulting knowledge-expansion status.

### Must NOT have (guardrails, anti-slop, scope boundaries)
- Do not deploy MCP, Cloudflare, Vercel, Supabase, VPS, or any remote service in this plan.
- Do not edit Recova MCP deployment runbooks or scripts unless a later explicit user instruction changes scope.
- Do not implement real execution. No court filing, no debtor contact, no demand sending, no seizure initiation, no ledger mutation, no production storage mutation.
- Do not call Korean-law MCP from deterministic tests.
- Do not leave broad legacy source bundles silently treated as approved article-level legal authority.
- Do not expose raw OCR text, real personal identifiers, phone numbers, resident-registration-number patterns, account-like identifiers, source text, or local source paths in evidence/docs/MCP outputs.
- Do not break existing local MCP tool order or existing 25-tool local source contract.
- Do not rewrite debtor identity merge rules, graph snapshot semantics, or v0 route candidate behavior in this knowledge-expansion wave.

## Verification strategy
> Zero human intervention - all verification is agent-executed. Any later user approval is a release/declaration gate, not part of technical verification.
- Test decision: TDD for validators, route/decision/StopGate regressions, action/governance workflow contracts, and MCP contract changes if any. Tests-after is acceptable only for data-entry-heavy JSON resources, but every changed resource family needs a validator and failure case.
- Main Python: `/opt/homebrew/bin/python3`.
- Compatibility floor: new lightweight production modules should avoid Python 3.12-only syntax and should pass `/usr/bin/python3 -m py_compile` where feasible.
- Evidence directory: `.omo/evidence/debt-collection-knowledge-expansion-v1/`.
- Required recurring gates:
  - `python3 -m json.tool` over every changed/new JSON resource and evidence file.
  - Focused pytest for each todo's resource/validator/module changes.
  - PII/path scan over changed source/tests/resources/evidence/docs with no matched source lines.
  - `git diff --check` and `git diff --cached --check` before commit.
  - Size gate for new Python modules; split before crossing local limits.
  - If any MCP tool changes, fake-MCP tests must prove auth is not a tool argument and path failure is redacted.
- Final focused suite target:
  - `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_domain_sources_v1.py tests/unit/legal_ontology/test_stop_gates_domain_v1.py tests/unit/legal_ontology/test_route_decisions_v1.py tests/unit/legal_ontology/test_domain_decision_engine_v1.py tests/unit/legal_ontology/test_finance_claim_model_v1.py tests/unit/legal_ontology/test_action_packets_v1.py tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py -q`
- Final evidence expected:
  - `.omo/evidence/debt-collection-knowledge-expansion-v1/final-knowledge-expansion-eval.json`
  - `.omo/evidence/debt-collection-knowledge-expansion-v1/final-legal-source-delta.json`
  - `.omo/evidence/debt-collection-knowledge-expansion-v1/final-scenario-coverage.json`
  - `.omo/evidence/debt-collection-knowledge-expansion-v1/final-pii-path-scan.txt`
  - `.omo/evidence/debt-collection-knowledge-expansion-v1/final-contract-review.md`

## Execution strategy
### Parallel execution waves
> Target 5-8 todos per wave. Fewer than 3 (except the final) means you under-split.
- Wave 1: legal-source precision, scenario inventory, and review-workflow contract. These can run in parallel because write scopes are mostly disjoint.
- Wave 2: scenario fixtures, finance/route/StopGate regression, and operator workflow tests.
- Wave 3: integration docs/evidence and final review.

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1. Legal-source precision audit | none | 4, 5, 7, 9 | 2, 3 |
| 2. Scenario gap inventory | none | 4, 5, 6, 7 | 1, 3 |
| 3. Human-review workflow contract | none | 6, 7, 8 | 1, 2 |
| 4. Replace/disposition remaining review legal sources | 1 | 5, 7, 9 | 6 |
| 5. Expand synthetic rare-case scenario fixtures | 2, 4 | 7, 9 | 6 |
| 6. Extend finance and operator-review regressions | 2, 3 | 7, 8, 9 | 4, 5 |
| 7. Strengthen domain decision and StopGate regressions | 4, 5, 6 | 9 | 8 |
| 8. Update docs and working log | 3, 6 | 9 | 7 |
| 9. Final eval and contract review | all prior | final verification | none |

## Todos
> Implementation + Test = ONE todo. Never separate.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->
- [ ] 1. Audit remaining review-needed legal sources and exact article targets
  What to do / Must NOT do: Produce a PII-safe audit of remaining `needs_legal_review` source records and every decision/StopGate use site that still depends on those IDs. Use Korean-law MCP only for discovery/verification evidence, then summarize findings into static evidence. Do not update production resources in this todo except a report/evidence artifact.
  Parallelization: Wave 1 | Blocked by: none | Blocks: 4, 5, 7, 9
  References (executor has NO interview context - be exhaustive): `.omo/notes/recova-brain-working-log.md:358`; `resources/legal_rules/debt_collection_domain_sources_v1.json:426`; `resources/legal_rules/debt_collection_domain_sources_v1.json:443`; `resources/legal_rules/debt_collection_domain_sources_v1.json:460`; `resources/decision_tables/debt_collection_route_decisions_v1.json`; `resources/legal_rules/debt_collection_stopgate_domain_v1.json`.
  Acceptance criteria (agent-executable): `/opt/homebrew/bin/python3 -m json.tool .omo/evidence/debt-collection-knowledge-expansion-v1/task-1-legal-source-audit.json` passes; evidence lists all remaining review-needed source IDs, linked article candidates, impacted route/workflow/StopGate/decision records, and whether each can be replaced or must remain a non-article contract source.
  QA scenarios (name the exact tool + invocation): happy: run the audit script or one-off verifier and write `.omo/evidence/debt-collection-knowledge-expansion-v1/task-1-legal-source-audit.json`; failure: include a controlled unknown-source probe written to `.omo/evidence/debt-collection-knowledge-expansion-v1/task-1-legal-source-audit-failure.txt`.
  Commit: Y | `test(legal-domain): audit review-needed legal sources`

- [ ] 2. Inventory scenario coverage gaps against the 32 route catalog
  What to do / Must NOT do: Add or update a small coverage script/test that compares `tests/fixtures/claim-domain-v1/synthetic_claim_states.json` against the 32 v1 routes, 19 route families, six action packet types, and required review/blocked/missing/possible statuses. This todo is an inventory and test guard; it should not bulk-add all new scenarios yet.
  Parallelization: Wave 1 | Blocked by: none | Blocks: 4, 5, 6, 7
  References (executor has NO interview context - be exhaustive): `resources/legal_routes/debt_collection_routes_v1.json`; `resources/action_packets/debt_collection_action_packets_v1.json`; `tests/fixtures/claim-domain-v1/synthetic_claim_states.json:13`; `docs/product/debt-collection-ontology/claim-domain-ontology-v1.md:226`.
  Acceptance criteria (agent-executable): `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_claim_domain_scenario_coverage.py -q` passes and evidence reports current baseline of 9 scenarios, 5 covered route IDs, and missing route-family clusters.
  QA scenarios (name the exact tool + invocation): happy: write `.omo/evidence/debt-collection-knowledge-expansion-v1/task-2-scenario-coverage.json`; failure: temp fixture with duplicate scenario id or unknown route id fails with evidence `.omo/evidence/debt-collection-knowledge-expansion-v1/task-2-scenario-coverage-failure.txt`.
  Commit: Y | `test(legal-domain): inventory claim scenario coverage gaps`

- [ ] 3. Define human-review operator workflow contract
  What to do / Must NOT do: Add a contract resource or doc that describes how action packet candidates and governance records move through human review: queued, assigned, reviewed, approved_for_operator_review, rejected, needs_more_evidence, superseded. Include operator-visible fields, audit fields, source_refs/evidence_refs, pii_profile, and forbidden fields. Do not build a frontend UI or execution button in this wave.
  Parallelization: Wave 1 | Blocked by: none | Blocks: 6, 7, 8
  References (executor has NO interview context - be exhaustive): `resources/action_packets/debt_collection_action_packets_v1.json`; `trustgraph_legal/debtor_governance.py`; `docs/product/debt-collection-ontology/claim-domain-ontology-v1.md:136`; `docs/product/debt-collection-ontology/claim-domain-ontology-v1.md:241`.
  Acceptance criteria (agent-executable): focused pytest or validator proves every review workflow state is valid, every terminal decision has audit fields, every action packet remains `direct_execution_allowed: false`, and no forbidden fields are present.
  QA scenarios (name the exact tool + invocation): happy: validate the review workflow and write `.omo/evidence/debt-collection-knowledge-expansion-v1/task-3-human-review-workflow.txt`; failure: temp workflow with `filing_destination` or debtor contact payload fails and writes `.omo/evidence/debt-collection-knowledge-expansion-v1/task-3-human-review-workflow-failure.txt`.
  Commit: Y | `feat(legal-domain): define operator review workflow contract`

- [ ] 4. Replace or formally disposition remaining review-needed source records
  What to do / Must NOT do: Update `debt_collection_domain_sources_v1.json` and related validators/tests using Todo 1 evidence. Replace broad legacy bundles with exact article-level source refs where possible. If a record is intentionally not a single statute article, keep it review-required but make the reason explicit and ensure ordinary route decisions do not treat it as approved legal authority. Do not silently mark privacy/domain-contract records approved.
  Parallelization: Wave 2 | Blocked by: 1 | Blocks: 5, 7, 9
  References (executor has NO interview context - be exhaustive): `resources/legal_rules/debt_collection_domain_sources_v1.json:426`; `resources/legal_rules/debt_collection_domain_sources_v1.json:443`; `resources/legal_rules/debt_collection_domain_sources_v1.json:460`; `scripts/legal_ontology/validate_domain_sources_v1.py`; `tests/unit/legal_ontology/test_domain_sources_v1.py`.
  Acceptance criteria (agent-executable): `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_domain_sources_v1.py tests/unit/legal_ontology/test_route_decisions_v1.py tests/unit/legal_ontology/test_stop_gates_domain_v1.py -q` passes; validator evidence states which review-needed sources were replaced and which remain explicit non-article contracts.
  QA scenarios (name the exact tool + invocation): happy: write `.omo/evidence/debt-collection-knowledge-expansion-v1/task-4-legal-source-happy.json`; failure: temp decision table using a review-needed source as approved fails and writes `.omo/evidence/debt-collection-knowledge-expansion-v1/task-4-legal-source-failure.txt`.
  Commit: Y | `feat(legal-domain): harden legal source review boundaries`

- [ ] 5. Expand rare-case claim-domain synthetic fixtures
  What to do / Must NOT do: Extend `tests/fixtures/claim-domain-v1/synthetic_claim_states.json` and integration tests with rare but important scenario clusters: real estate, vehicle, lease deposit, business receivable/PG settlement, insurance/refund/deposit, tax refund/public receivable, inheritance/family property, fraudulent transfer/hidden assets, special property rights, protected welfare/public benefit, and insolvency/recovery. Keep fixtures minimized and synthetic; do not include real names/contact/account strings.
  Parallelization: Wave 2 | Blocked by: 2, 4 | Blocks: 7, 9
  References (executor has NO interview context - be exhaustive): `tests/fixtures/claim-domain-v1/synthetic_claim_states.json:13`; `tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py`; `resources/legal_routes/debt_collection_routes_v1.json`; `resources/decision_tables/debt_collection_route_decisions_v1.json`.
  Acceptance criteria (agent-executable): `/opt/homebrew/bin/python3 -m pytest tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py tests/unit/legal_ontology/test_domain_decision_engine_v1.py -q` passes; scenario coverage evidence shows materially broader route-family and packet-type coverage than the current 9-scenario baseline.
  QA scenarios (name the exact tool + invocation): happy: write `.omo/evidence/debt-collection-knowledge-expansion-v1/task-5-expanded-scenarios-happy.json`; failure: fixture with an unapproved source or missing required fact yields deterministic blocked/review evidence `.omo/evidence/debt-collection-knowledge-expansion-v1/task-5-expanded-scenarios-failure.json`.
  Commit: Y | `test(legal-domain): expand rare claim scenario fixtures`

- [ ] 6. Extend finance and human-review regression coverage
  What to do / Must NOT do: Add deterministic tests/evidence for finance and review outcomes that agents commonly over-assume: disputed balances, payment allocation conflicts, enforcement cost review, assignment/succession, guarantee/surety, subrogation/reimbursement candidate, and operator review rejection/needs-more-evidence flows. Do not turn fixture calculations into authoritative production accounting.
  Parallelization: Wave 2 | Blocked by: 2, 3 | Blocks: 7, 8, 9
  References (executor has NO interview context - be exhaustive): `resources/finance/claim_finance_model_v1.json`; `trustgraph_legal/finance_claims.py`; `tests/unit/legal_ontology/test_finance_claim_model_v1.py`; `resources/action_packets/debt_collection_action_packets_v1.json`; `trustgraph_legal/debtor_governance.py`.
  Acceptance criteria (agent-executable): `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_finance_claim_model_v1.py tests/unit/legal_ontology/test_action_packets_v1.py tests/unit/legal_ontology/test_debtor_governance.py -q` passes; evidence proves ambiguous finance and rejected review records remain review-required.
  QA scenarios (name the exact tool + invocation): happy: write `.omo/evidence/debt-collection-knowledge-expansion-v1/task-6-finance-review-happy.json`; failure: conflicting balance or missing audit metadata writes `.omo/evidence/debt-collection-knowledge-expansion-v1/task-6-finance-review-failure.json`.
  Commit: Y | `test(legal-domain): strengthen finance and review regressions`

- [ ] 7. Strengthen domain decision and StopGate integration for expanded knowledge
  What to do / Must NOT do: Update decision/StopGate tests and, if necessary, narrow engine logic so new scenarios produce stable `possible`, `review_required`, `blocked`, or `missing_facts` outputs with traceable reasons. Preserve non-execution semantics and source-ref-only evidence. Do not loosen blockers merely to make scenarios possible.
  Parallelization: Wave 2 | Blocked by: 4, 5, 6 | Blocks: 9
  References (executor has NO interview context - be exhaustive): `trustgraph_legal/domain_decisions.py`; `trustgraph_legal/stop_gates_domain_v1.py`; `resources/legal_rules/debt_collection_stopgate_domain_v1.json`; `resources/decision_tables/debt_collection_route_decisions_v1.json`; `tests/unit/legal_ontology/test_domain_decision_engine_v1.py`; `tests/unit/legal_ontology/test_stop_gates_domain_v1.py`.
  Acceptance criteria (agent-executable): `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_domain_decision_engine_v1.py tests/unit/legal_ontology/test_stop_gates_domain_v1.py tests/unit/legal_ontology/test_route_decisions_v1.py -q` passes; expanded scenarios produce traceable source_refs and no raw text.
  QA scenarios (name the exact tool + invocation): happy: write `.omo/evidence/debt-collection-knowledge-expansion-v1/task-7-domain-decision-happy.json`; failure: stale source version, review-needed source, or protected-property blocker writes `.omo/evidence/debt-collection-knowledge-expansion-v1/task-7-domain-decision-failure.json`.
  Commit: Y | `test(legal-domain): verify expanded domain decisions`

- [ ] 8. Update operator docs and working log for knowledge expansion
  What to do / Must NOT do: Update the living working log and product docs to explain the new knowledge expansion: which deployment steps were skipped, which legal sources were replaced or retained as review-needed, which rare scenario classes were added, and how human review should treat action packets/governance records. Do not update remote MCP client setup docs unless this plan explicitly changes remote deployment, which it should not.
  Parallelization: Wave 3 | Blocked by: 3, 6 | Blocks: 9
  References (executor has NO interview context - be exhaustive): `.omo/notes/recova-brain-working-log.md:358`; `docs/product/debt-collection-ontology/claim-domain-ontology-v1.md:226`; `.omo/plans/debt-collection-knowledge-expansion-v1.md`.
  Acceptance criteria (agent-executable): `rg -n "knowledge expansion|needs_legal_review|human-review|non-executing|raw_text_included" .omo/notes/recova-brain-working-log.md docs/product/debt-collection-ontology/claim-domain-ontology-v1.md` finds expected sections; PII/path scan has no findings.
  QA scenarios (name the exact tool + invocation): happy: write `.omo/evidence/debt-collection-knowledge-expansion-v1/task-8-docs-smoke.txt`; failure: PII/path scan over docs/log writes `.omo/evidence/debt-collection-knowledge-expansion-v1/task-8-docs-pii.txt`.
  Commit: Y | `docs(legal-domain): document knowledge expansion status`

- [ ] 9. Final knowledge expansion eval and contract review
  What to do / Must NOT do: Run final integrated checks across changed legal-source resources, rare-case fixtures, finance/review regressions, decision engine, StopGate, docs, and local MCP tool order. Produce a final review artifact with accepted/rejected verdict. Do not declare complete until final review accepts the integrated state.
  Parallelization: Wave 3 | Blocked by: all prior | Blocks: final verification
  References (executor has NO interview context - be exhaustive): all task evidence under `.omo/evidence/debt-collection-knowledge-expansion-v1/`; `.omo/teams/team-8953292e/artifacts/V-final-contract-review.md`; final accepted v1 resources; this plan.
  Acceptance criteria (agent-executable): final focused suite passes; all JSON evidence validates; final PII/path scan returns `NO_FINDINGS`; final artifact records no deployment/runbook mutations and confirms execution remains forbidden.
  QA scenarios (name the exact tool + invocation): happy: write `.omo/evidence/debt-collection-knowledge-expansion-v1/final-knowledge-expansion-eval.json`; failure: known negative fixture writes `.omo/evidence/debt-collection-knowledge-expansion-v1/final-negative-eval.json`; review writes `.omo/evidence/debt-collection-knowledge-expansion-v1/final-contract-review.md`.
  Commit: Y | `test(legal-domain): add knowledge expansion final eval`

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.
- [ ] F1. Plan compliance audit
- [ ] F2. Code quality review
- [ ] F3. Legal/source and scenario QA
- [ ] F4. Scope fidelity and non-execution review

## Commit strategy
- Commit each todo as a narrow, reviewable slice.
- Do not stage unrelated MCP deployment/runbook dirty files.
- Keep generated evidence under `.omo/evidence/debt-collection-knowledge-expansion-v1/` when it is part of the todo acceptance.
- Shared team review artifacts may live under `.omo/teams/.../artifacts/` and should be mentioned in reports.
- Push only after the integrated branch/master state is accepted or when the user explicitly asks for an intermediate push.

## Success criteria
- Remaining broad legal-source review debt is either replaced with exact article-level refs or explicitly retained as non-article review-required contract metadata.
- Synthetic scenario coverage is meaningfully broader than the current 9-scenario baseline and covers rare asset classes plus insolvency/recovery/protected-property cases.
- Route decisions and StopGates remain deterministic, source-ref-backed, and non-executing.
- Finance ambiguity and operator review outcomes remain review-required rather than silently possible.
- Product docs and the working log explain the new state in plain language.
- Final review accepts the integrated state with focused tests, JSON validation, PII/path scan, and diff checks passing.
