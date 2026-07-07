# debt-collection-domain-ontology-v1 - Work Plan

## TL;DR (For humans)
Recova에 "채권추심 전문 두뇌"를 하나 더 얹는 계획이다. 이미 만든 채무자별 기억 그래프는 한 사건의 현재 상태를 기억하고, 이번 도메인 온톨로지 v1은 그 상태를 보고 "어떤 법률/금융/업무 판단을 해야 하는지"를 알려주는 지식 체계가 된다.

**What you'll get:** 채권, 채무자, 집행권원, 시효, 이자/변제/비용, 재산 단서, 법조치 루트, 업무 단계, 금지/보류 조건, 다음 조치 후보를 하나의 연결된 도메인 모델로 다룰 수 있다. 에이전트는 MCP로 이 두뇌를 읽어 "왜 이 루트가 가능/보류/불가인지"와 "무엇을 더 확인해야 하는지"를 설명받게 된다.

**Why this approach:** 채권추심 실무 판단은 법률만으로도, 금융 계산만으로도, 체크리스트만으로도 안 된다. 실제 판단은 "채권 상태 + 법적 요건 + 증거 + 재산 단서 + 업무 단계 + StopGate"가 같이 맞아야 하므로, 하나의 claim-centered ontology로 설계하되 JSON 리소스와 검증기로 레이어를 나눠 안전하게 만든다.

**What it will NOT do:** 실제 법원 제출, 채무자 연락, 변제 요구, 압류 실행은 하지 않는다. 원문 OCR, 실명, 주민등록번호형 문자열, 전화번호, 계좌번호, 로컬 민감 경로를 출력하지 않는다. 법령 MCP를 테스트 중 실시간 의존성으로 삼지 않고, 확인한 법령 근거는 versioned JSON으로 고정한다.

**Effort:** XL
**Risk:** High - 범위가 넓고 법률/금융/업무 연결이 핵심이라 잘게 검증하지 않으면 "그럴듯하지만 실행자가 못 믿는 지식 그래프"가 될 위험이 크다.
**Decisions to sanity-check:** 새 도메인 온톨로지의 루트는 `Claim`/`Receivable`이고, 기존 `DebtorContextGraph`는 런타임 기억 그래프로 유지한다. 법률, 금융, 워크플로우는 한 계획 안에서 같이 설계한다. v1은 과감하게 action packet schema까지 모델링하지만 실행은 막는다.

Your next move: start execution with `$omo:start-work .omo/plans/debt-collection-domain-ontology-v1.md`, preferably with team mode. Full execution detail follows below.

---

> TL;DR (machine): XL/High risk. Build a claim-centered debt-collection domain ontology v1 with curated legal sources, finance facts, workflow states, route decisions, action packet schemas, validators, tests, docs, and MCP-compatible read/explain surfaces while preserving existing debtor graph v0 and 21 MCP tools.

## Scope
### Must have
- A claim-centered Recova domain ontology v1. The main conceptual root is `Claim` / `Receivable`, not `Debtor`. A debtor may have one or more claims; a claim connects to case packets, documents, evidence, legal status, ledger facts, asset hints, workflow state, route decisions, and governance/review records.
- The existing debtor-context graph v0 stays intact. This plan extends domain knowledge that consumes graph facts; it does not replace graph identity or snapshot machinery.
- Root boundary: `Claim` / `Receivable` is the v1 ontology root; `DebtorContextGraph` remains the runtime memory root. A compatibility adapter maps graph facts into claim-domain handles. No todo may change debtor identity merge rules unless it is a separate explicitly accepted migration.
- Versioned resource families:
  - `resources/ontologies/recova-debt-collection-v1.json`
  - `resources/legal_rules/debt_collection_domain_sources_v1.json`
  - `resources/legal_routes/debt_collection_routes_v1.json`
  - `resources/workflows/debt_collection_workflow_v1.json`
  - `resources/decision_tables/debt_collection_route_decisions_v1.json`
  - `resources/action_packets/debt_collection_action_packets_v1.json`
- Versioning rule: v1 creates new resource files. Existing v0 resources are read-only inputs, compatibility fixtures, and regression references unless a todo explicitly says to add a backwards-compatible loader.
- A PII-safe extraction/evidence pass over the user-provided v2 practical manual:
  - `/Users/cosmos/Downloads/채권추심_장기채권_법조치_루트_총정리_v2_실무확장판 (1).md`
- Korean-law MCP assisted legal-source discovery and verification, captured into `.omo/evidence/debt-collection-domain-ontology-v1/` and then frozen into curated JSON resources. Deterministic tests must use frozen resources, not live MCP calls.
- Legal temporal policy: every v1 legal-source/resource evaluation must carry an explicit `evaluation_date` and effective-date decision. Do not add a new hard-coded current date without a resource-level/version-level field and tests.
- Finance/claim accounting concepts needed for reasoning:
  - principal
  - interest
  - late damages
  - enforcement/legal costs
  - payments
  - payment allocation
  - remaining balance
  - assignment/succession
  - guarantee/surety
  - subrogation/reimbursement candidates where the manual supports them
- Practical workflow state model:
  - `intake`
  - `identity_evidence_package`
  - `limitation_review`
  - `title_acquisition`
  - `service_finality_execution_clause`
  - `voluntary_recovery`
  - `provisional_remedy`
  - `asset_discovery`
  - `execution_route_selection`
  - `insolvency_discharge_review`
  - `monitoring_retry`
  - `closure`
- Route catalog v1 grounded in the v2 manual, expanded beyond the current 18 route candidates.
- Route decision table v1 that links each route to:
  - required graph fact handles
  - missing fact handles
  - blocking fact handles
  - legal source refs
  - finance/ledger refs
  - evidence/document refs
  - StopGate/compliance refs
  - workflow preconditions
  - scoring/priority metadata
  - advisory next-step/action packet type
  - explicit non-execution semantics
- Action packet schemas for future human review:
  - evidence-request packet
  - legal-action-review packet
  - finance-review packet
  - contact-review packet
  - monitoring/retry packet
  - insolvency/recovery-review packet
  These schemas must be descriptive artifacts only; no tool may submit, send, file, or demand anything. Each packet must use explicit statuses such as `draft_only`, `human_review_required`, `execution_forbidden`, `approved_for_operator_review`, and `rejected`.
- Validators and focused tests for every new resource family.
- Integration with existing `DebtorContextGraph` facts and route candidates through stable handles. No breaking of existing graph snapshot, route matcher, governance, or MCP contracts.
- Additive MCP read/explain tools after the existing 21 tools, preserving the accepted order of the existing tool surface.
- Documentation for operators/developers explaining:
  - domain ontology vs debtor context graph
  - claim-centered identity
  - legal-source curation policy
  - finance calculation boundaries
  - action packet non-execution boundary
  - how an agent should use the MCP surface
- Final evidence pack with synthetic and real-manual summary-only proof.

### Must NOT have (guardrails, anti-slop, scope boundaries)
- Do not implement actual debt collection execution.
- Do not file court documents, contact debtors, send payment demands, initiate account seizure, or mutate production systems.
- Do not expose raw OCR text, real personal identifiers, phone numbers, resident-registration-number patterns, account-like identifiers, or sensitive source paths in evidence, reports, docs, or MCP responses.
- Do not call Korean-law MCP from deterministic tests. Use live Korean-law MCP only for source-discovery evidence during execution, then commit curated/versioned JSON.
- Do not silently invent legal authority. Every legal source included in v1 must have retrieval/review metadata or be marked as a candidate requiring review.
- Do not break the existing 21 MCP tools. Existing 16 debt-collection tools must remain first; five debtor_graph tools must remain appended in their accepted order.
- Do not remove or rewrite debtor-context graph v0. Todo 10 may add a compatibility adapter, but not a schema migration.
- Do not mutate unrelated deployment/runbook dirty files, including Recova MCP hosting docs or scripts, unless the user explicitly changes scope.
- Do not add remote Supabase, Cloudflare, Vercel, or production MCP deployment work to this plan.
- Do not turn the finance model into an authoritative production accounting ledger. v1 may calculate deterministic fixture examples and validate schema/contracts; production ledger mutation is out of scope.
- Do not create one huge unvalidated JSON blob. Every resource family needs a validator and focused test coverage.

## Verification strategy
> Zero human intervention - all verification is agent-executed. Any later user approval is a release/declaration gate, not part of technical verification.
- Test decision: TDD for validators/adapters/decision logic; resource JSON may be tests-after when it is data-entry heavy, but every resource family must have a failing/positive validator case before acceptance.
- Main Python: `/opt/homebrew/bin/python3`.
- Compatibility floor: any production module touched by this plan must either import under `/usr/bin/python3` where currently feasible or record the pre-existing blocker explicitly. New lightweight modules should avoid Python 3.12-only syntax.
- Evidence directory: `.omo/evidence/debt-collection-domain-ontology-v1/`.
- Required recurring gates:
  - `python3 -m json.tool` over every new JSON resource and evidence file.
  - Focused pytest for each todo's changed module/resource validator.
  - PII/path scan over changed source/tests/resources/evidence/docs with a no-matched-lines evidence file.
  - `git diff --check` before every commit.
  - Size/complexity check for new Python modules; split before crossing local size rules.
  - For any MCP change: fake-MCP test must prove auth is not a tool argument and outside-root paths are redacted.
- Final focused suite target:
  - `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_domain_ontology_v1.py tests/unit/legal_ontology/test_domain_sources_v1.py tests/unit/legal_ontology/test_finance_claim_model_v1.py tests/unit/legal_ontology/test_workflow_v1.py tests/unit/legal_ontology/test_route_decisions_v1.py tests/unit/legal_ontology/test_action_packets_v1.py tests/unit/legal_ontology/test_domain_decision_engine_v1.py tests/unit/legal_ontology/test_mcp_debtor_context_tools.py tests/integration/legal_ontology/test_debtor_context_pipeline.py -q`
- Final evidence expected:
  - `.omo/evidence/debt-collection-domain-ontology-v1/final-domain-eval.json`
  - `.omo/evidence/debt-collection-domain-ontology-v1/final-tool-list.json` if MCP tools are added
  - `.omo/evidence/debt-collection-domain-ontology-v1/final-pii-scan.txt`
  - `.omo/evidence/debt-collection-domain-ontology-v1/final-real-manual-summary.json`
  - `.omo/evidence/debt-collection-domain-ontology-v1/final-contract-review.md`

## Execution strategy
### Parallel execution waves
> Target 5-8 todos per wave. Fewer than 3 (except the final) means you under-split.
- Wave 1: source inventory, claim-centered schema contract, and legal-source expansion. These can run in parallel as long as write scopes are disjoint.
- Wave 2: finance model, workflow model, route catalog, and decision table. These depend on Wave 1 IDs and source conventions.
- Wave 3: action packets, StopGate/compliance expansion, domain decision engine, debtor-graph integration, and optional MCP exposure.
- Wave 4: docs, integration tests, real/manual eval, and final review.

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1. v2 manual inventory and candidate extraction | none | 4, 5, 6, 7 | 2, 3 |
| 2. Claim-centered ontology contract v1 | none | 4, 5, 8, 10, 11 | 1, 3 |
| 3. Korean-law source discovery and curation | none | 6, 7, 9 | 1, 2 |
| 4. Finance and claim accounting model | 1, 2 | 7, 8, 10 | 5, 6 |
| 5. Workflow state resource v1 | 1, 2 | 7, 8, 12 | 4, 6 |
| 6. Legal route catalog v1 | 1, 2, 3 | 7, 8, 9, 10 | 4, 5 |
| 7. Route decision table and scoring v1 | 4, 5, 6 | 8, 10, 11, 12 | 9 |
| 8. Action packet schema v1 | 4, 5, 7 | 11, 12, 13 | 9 |
| 9. StopGate/compliance expansion | 3, 6 | 10, 11, 12 | 7, 8 |
| 10. DebtorContextGraph compatibility adapter | 2, 4, 6, 7, 9 | 11, 13, 15 | 8 |
| 11. Domain decision engine | 7, 8, 9, 10 | 12, 13, 15 | none |
| 12. Additive MCP read/explain surface | 5, 8, 11 | 13, 14, 15 | none |
| 13. Integration fixtures and end-to-end tests | 10, 11, 12 | 15 | 14 |
| 14. Operator/developer docs and working-log closeout | 11, 12 | 15 | 13 |
| 15. Final eval pack and contract review | all prior | final verification | none |

## Todos
> Implementation + Test = ONE todo. Never separate.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->
- [x] 1. Build PII-safe v2 manual inventory and candidate extractor
  What to do / Must NOT do: Add a small extractor under `scripts/legal_ontology/` that reads `/Users/cosmos/Downloads/채권추심_장기채권_법조치_루트_총정리_v2_실무확장판 (1).md` and emits a summary-only candidate inventory: headings, route candidates, workflow candidates, fact handles, risk/blocker candidates, legal-source names/articles if present, finance/accounting candidates, scoring fields, and action-packet candidates. The output must not include full prose bodies, raw personal data, or local source paths. Keep the original manual outside committed resources unless a minimized/redacted fixture is deliberately created.
  Parallelization: Wave 1 | Blocked by: none | Blocks: 4, 5, 6, 7
  References (executor has NO interview context - be exhaustive): `/Users/cosmos/Downloads/채권추심_장기채권_법조치_루트_총정리_v2_실무확장판 (1).md`; `.omo/notes/recova-brain-working-log.md`; existing summary patterns in `scripts/legal_ontology/summarize_ocr_corpus.py`; evidence conventions in `.omo/evidence/debtor-context-graph-v0/`.
  Acceptance criteria (agent-executable): `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_domain_manual_inventory.py -q` passes; `python3 -m json.tool .omo/evidence/debt-collection-domain-ontology-v1/task-1-manual-inventory.json` passes; inventory includes counts for route/workflow/legal/finance/action candidates and no full body text field.
  QA scenarios (name the exact tool + invocation): happy: run the extractor on the v2 manual and write `.omo/evidence/debt-collection-domain-ontology-v1/task-1-manual-inventory.json`; failure: run on a temp invalid/nonexistent manual path and require a controlled error in `.omo/evidence/debt-collection-domain-ontology-v1/task-1-manual-inventory-failure.txt`.
  Commit: Y | `test(legal-domain): inventory collection manual candidates`

- [x] 2. Define claim-centered ontology v1 resource and validator
  What to do / Must NOT do: Add `resources/ontologies/recova-debt-collection-v1.json` and `scripts/legal_ontology/validate_domain_ontology_v1.py` or extend the existing validator if the shape remains compatible. The ontology must explicitly model `Claim`/`Receivable` as root, connected to debtor identity, creditor/assignee, guarantee/surety, case packet, document assembly, enforcement title, service/finality/execution clause, limitation, ledger facts, asset hints, route candidates, workflow states, StopGates, action packets, and governance records. Preserve links to existing `recova-debt-collection` IDs where possible; do not silently rename existing public IDs without alias metadata.
  Parallelization: Wave 1 | Blocked by: none | Blocks: 4, 5, 8, 10, 11
  References (executor has NO interview context - be exhaustive): `resources/ontologies/recova-debt-collection.json`; `scripts/legal_ontology/validate_ontology.py`; `tests/unit/legal_ontology/test_validate_ontology.py`; `.omo/plans/debtor-context-graph-v0.md`; `.omo/teams/debtor-context-graph-v0-20260706/artifacts/T-final-contract-review.md`.
  Acceptance criteria (agent-executable): `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_domain_ontology_v1.py -q` passes; validator prints a PASS line with class/property counts and confirms required root/edge IDs; temp-copy failure for missing `Claim` root exits nonzero.
  QA scenarios (name the exact tool + invocation): happy: `python3 scripts/legal_ontology/validate_domain_ontology_v1.py resources/ontologies/recova-debt-collection-v1.json` writes `.omo/evidence/debt-collection-domain-ontology-v1/task-2-ontology-validator.txt`; failure: remove a required class in a temp copy and write `.omo/evidence/debt-collection-domain-ontology-v1/task-2-ontology-validator-failure.txt`.
  Commit: Y | `feat(legal-domain): add claim-centered ontology v1`

- [x] 3. Expand Korean-law source map into curated domain source v1
  What to do / Must NOT do: Use the Korean-law MCP to discover/verify law and article refs needed by the v2 manual and existing route/StopGate resources. Add `resources/legal_rules/debt_collection_domain_sources_v1.json` and a validator. Each source record must include stable source_id, law name, law_id/mst/article when available, effective date, retrieved_at, retrieval_status, review_status, source axis, route/workflow/StopGate usage, and source_ref. If the MCP is unavailable or a source is ambiguous, record a candidate with `review_status: needs_legal_review` and evidence of the failed lookup; do not guess.
  Parallelization: Wave 1 | Blocked by: none | Blocks: 6, 7, 9
  References (executor has NO interview context - be exhaustive): `resources/legal_rules/debt_collection_route_sources_v0.json`; `resources/legal_rules/debt_collection_stopgate_v0.json`; `resources/legal_routes/debt_collection_routes_v0.json`; v2 manual legal-source checklist; Korean-law MCP tools available in this Codex environment.
  Acceptance criteria (agent-executable): `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_domain_sources_v1.py -q` passes; `python3 -m json.tool resources/legal_rules/debt_collection_domain_sources_v1.json` passes; validator proves no route/workflow/StopGate legal source ref points to a missing source_id.
  QA scenarios (name the exact tool + invocation): happy: Korean-law lookup evidence summarized in `.omo/evidence/debt-collection-domain-ontology-v1/task-3-korean-law-source-map.json` and validator output in `task-3-source-validator.txt`; failure: temp-copy route source ref to unknown source_id and write `task-3-source-validator-failure.txt`.
  Commit: Y | `feat(legal-domain): curate domain legal sources v1`

- [x] 4. Add finance and claim accounting model v1
  What to do / Must NOT do: Add finance/ledger concepts and a deterministic schema/contract for claim balance reasoning. Cover principal, interest, late damages, enforcement costs, payments, payment allocation, remaining balance, assignment/succession, guarantee/surety, reimbursement/subrogation candidate, and disputed amount. Include a minimal deterministic fixture calculator for cases where amount, rate, period, payment date, and allocation rule are explicit. Complex statutory interest or disputed facts must return `needs_finance_review`. Do not mutate ledgers or present fixture calculations as authoritative balances.
  Parallelization: Wave 2 | Blocked by: 1, 2 | Blocks: 7, 8, 10
  References (executor has NO interview context - be exhaustive): `resources/ontologies/recova-debt-collection-v1.json`; existing amount/interest classes in `resources/ontologies/recova-debt-collection.json`; v2 manual sections on 채권 원금/이자/비용/변제/상계/시효; current field extraction and debtor context fact models under `trustgraph_legal/fields.py`, `trustgraph_legal/debtor_context_types.py`.
  Acceptance criteria (agent-executable): `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_finance_claim_model_v1.py -q` passes; tests prove schema serialization, payment-allocation fixture behavior if implemented, and missing-source/ambiguous-balance review behavior.
  QA scenarios (name the exact tool + invocation): happy: write a synthetic claim ledger fixture and output `.omo/evidence/debt-collection-domain-ontology-v1/task-4-finance-happy.json`; failure: conflicting payment/allocation fixture produces review item evidence `.omo/evidence/debt-collection-domain-ontology-v1/task-4-finance-failure.json`.
  Commit: Y | `feat(legal-domain): add claim finance model`

- [x] 5. Add collection workflow state resource v1
  What to do / Must NOT do: Add `resources/workflows/debt_collection_workflow_v1.json` and validator. Model canonical state IDs, transitions, preconditions, exit conditions, required evidence, review states, and blocked/monitoring loops. The required v1 state IDs are `intake`, `identity_evidence_package`, `limitation_review`, `title_acquisition`, `service_finality_execution_clause`, `voluntary_recovery`, `provisional_remedy`, `asset_discovery`, `execution_route_selection`, `insolvency_discharge_review`, `monitoring_retry`, and `closure`. Do not encode route decision logic here; keep workflow state and route eligibility linked but separable.
  Parallelization: Wave 2 | Blocked by: 1, 2 | Blocks: 7, 8, 12
  References (executor has NO interview context - be exhaustive): v2 manual headings and operational scenarios; `.omo/notes/recova-brain-working-log.md`; current route candidate statuses in `trustgraph_legal/route_candidates.py`; governance review statuses in `trustgraph_legal/debtor_governance.py`.
  Acceptance criteria (agent-executable): `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_workflow_v1.py -q` passes; validator confirms every transition points to valid states and every state has evidence/review semantics.
  QA scenarios (name the exact tool + invocation): happy: validate workflow resource and write `.omo/evidence/debt-collection-domain-ontology-v1/task-5-workflow-validator.txt`; failure: temp-copy invalid transition target writes `task-5-workflow-validator-failure.txt`.
  Commit: Y | `feat(legal-domain): add collection workflow states`

- [x] 6. Expand legal route catalog v1 from manual and curated sources
  What to do / Must NOT do: Add `resources/legal_routes/debt_collection_routes_v1.json` and validator. Expand beyond the current 18 route candidates using v2 manual route families: voluntary repayment, debt acknowledgment/notarial deed, title acquisition, provisional attachment, bank/financial asset execution, wage/income, lease/housing, business receivables/settlement, real estate, vehicle/movable/business assets, insurance/refund/deposit, tax/refund/distribution/compensation, inheritance/family property, fraudulent transfer/hidden assets, special property rights, welfare/public-benefit exclusions, property disclosure/inquiry/default registry, insolvency/recovery routes, monitoring/retry. Preserve advisory-only/no-direct-execution semantics.
  Parallelization: Wave 2 | Blocked by: 1, 2, 3 | Blocks: 7, 8, 9, 10
  References (executor has NO interview context - be exhaustive): `resources/legal_routes/debt_collection_routes_v0.json`; `scripts/legal_ontology/validate_routes.py`; `tests/unit/legal_ontology/test_validate_routes.py`; v2 manual route catalog and legal-source checklist; `resources/legal_rules/debt_collection_domain_sources_v1.json`.
  Acceptance criteria (agent-executable): `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_routes_v1.py -q` passes; validator confirms route ids are unique, legal refs exist, required/missing/blocking handles are valid, and every route has `direct_execution_allowed: false`.
  QA scenarios (name the exact tool + invocation): happy: `python3 scripts/legal_ontology/validate_routes.py resources/legal_routes/debt_collection_routes_v1.json resources/legal_rules/debt_collection_domain_sources_v1.json` writes `task-6-route-validator.txt`; failure: unknown legal source ref writes `task-6-route-validator-failure.txt`.
  Commit: Y | `feat(legal-routes): expand debt collection route catalog v1`

- [x] 7. Add route decision table and priority scoring v1
  What to do / Must NOT do: Add `resources/decision_tables/debt_collection_route_decisions_v1.json` plus a validator and lightweight evaluator module if needed. Encode route decision predicates: required fact handles, missing fact handles, blocking handles, workflow preconditions, finance preconditions, legal-source review status, StopGate blockers, priority score components, explainable reasons, and next-step action packet type. Priority scoring must be deterministic rule weights with named components, capped score ranges, tie-breaker order, and source refs. Do not collapse complex legal judgment into a single opaque score; every score/reason must be traceable.
  Parallelization: Wave 2 | Blocked by: 4, 5, 6 | Blocks: 8, 10, 11, 12
  References (executor has NO interview context - be exhaustive): `trustgraph_legal/route_candidates.py`; `resources/legal_routes/debt_collection_routes_v1.json`; `resources/workflows/debt_collection_workflow_v1.json`; `resources/decision_tables` conventions if present; v2 manual recommendation engine fields/rules/scoring section.
  Acceptance criteria (agent-executable): `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_route_decisions_v1.py -q` passes; evaluator returns deterministic `possible`, `review_required`, `blocked`, or `missing_facts` statuses with traceable reason codes.
  QA scenarios (name the exact tool + invocation): happy: evaluate a synthetic claim graph fixture and write `.omo/evidence/debt-collection-domain-ontology-v1/task-7-route-decision-happy.json`; failure: missing legal-source review status or StopGate blocker writes `task-7-route-decision-failure.json`.
  Commit: Y | `feat(legal-domain): add route decision table v1`

- [x] 8. Add advisory action packet schemas
  What to do / Must NOT do: Add `resources/action_packets/debt_collection_action_packets_v1.json` and validator. Define schemas for evidence-request, legal-action-review, finance-review, contact-review, monitoring/retry, and insolvency/recovery-review packets. Each schema must specify required inputs, source_refs, pii_profile, review_status, non_execution_semantics, and forbidden fields. No packet may include actual filing destination, debtor contact channel payload, or executable instruction.
  Parallelization: Wave 3 | Blocked by: 4, 5, 7 | Blocks: 11, 12, 13
  References (executor has NO interview context - be exhaustive): current MCP non-execution envelope in `trustgraph_legal/mcp_domain.py`; governance record style in `trustgraph_legal/debtor_governance.py`; v2 manual operational scenarios and Recova recommendation fields.
  Acceptance criteria (agent-executable): `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_action_packets_v1.py -q` passes; validator rejects any packet schema with direct execution semantics or debtor-contact payload fields.
  QA scenarios (name the exact tool + invocation): happy: validate all packet schemas and write `task-8-action-packets-validator.txt`; failure: temp-copy packet with `direct_execution_allowed: true` writes `task-8-action-packets-failure.txt`.
  Commit: Y | `feat(legal-domain): add advisory action packet schemas`

- [x] 9. Expand StopGate and compliance rule coverage for domain v1
  What to do / Must NOT do: Extend or add a v1 StopGate/compliance resource to cover domain-level blockers from the v2 manual: limitation risk, insolvency/discharge, exempt claim/property, welfare/public benefit protection, unapproved legal-source status, missing title/service/finality/execution-clause proof, excessive/ambiguous balance, unsupported contact/recovery route, and route-specific legal source uncertainty. Keep the engine advisory and review-safe.
  Parallelization: Wave 3 | Blocked by: 3, 6 | Blocks: 10, 11, 12
  References (executor has NO interview context - be exhaustive): `resources/legal_rules/debt_collection_stopgate_v0.json`; `trustgraph_legal/stop_gates.py`; `tests/unit/legal_ontology/test_stop_gates.py`; `resources/legal_rules/debt_collection_domain_sources_v1.json`; v2 manual common mistakes and legal baseline.
  Acceptance criteria (agent-executable): `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_stop_gates_domain_v1.py tests/unit/legal_ontology/test_stop_gates.py -q` passes; existing StopGate tests remain green.
  QA scenarios (name the exact tool + invocation): happy: evaluate a synthetic graph with known blockers and write `.omo/evidence/debt-collection-domain-ontology-v1/task-9-stopgate-happy.json`; failure: unapproved legal source or placeholder source ref writes `task-9-stopgate-failure.json`.
  Commit: Y | `feat(legal-check): expand domain stop gates v1`

- [x] 10. Add DebtorContextGraph to domain-v1 compatibility adapter
  What to do / Must NOT do: Add a narrow adapter module that maps existing `DebtorContextGraph` fact assertions, route candidates, governance records, and snapshots into the new claim-centered domain handles. The adapter must preserve existing graph IDs and source refs. It must not change debtor identity merge behavior, graph snapshot generation, or route candidate v0 outputs.
  Parallelization: Wave 3 | Blocked by: 2, 4, 6, 7, 9 | Blocks: 11, 13, 15
  References (executor has NO interview context - be exhaustive): `trustgraph_legal/debtor_context.py`; `trustgraph_legal/debtor_context_builder.py`; `trustgraph_legal/debtor_context_types.py`; `trustgraph_legal/debtor_snapshots.py`; `trustgraph_legal/route_candidates.py`; final accepted evidence in `.omo/evidence/debtor-context-graph-v0/final-real-ocr-eval.json`.
  Acceptance criteria (agent-executable): `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_domain_graph_adapter_v1.py tests/unit/legal_ontology/test_debtor_context.py -q` passes; adapter output has claim root, source_bundle_hash, graph_snapshot_id, and no raw OCR text.
  QA scenarios (name the exact tool + invocation): happy: adapt the synthetic debtor graph fixture and write `task-10-graph-adapter-happy.json`; failure: graph fact with missing source_ref or unsupported claim identity writes `task-10-graph-adapter-failure.json`.
  Commit: Y | `feat(legal-domain): map debtor graphs to claim domain`

- [x] 11. Implement domain decision engine v1
  What to do / Must NOT do: Add a deterministic engine that consumes the claim-domain adapter output plus workflow, route, decision-table, action-packet, legal-source, finance, and StopGate resources. It returns an advisory domain decision payload with candidate routes, reasons, blockers, missing facts, workflow stage, finance review items, action packet candidates, and source refs. Do not call LLMs, live law MCP, external services, or production systems.
  Parallelization: Wave 3 | Blocked by: 7, 8, 9, 10 | Blocks: 12, 13, 15
  References (executor has NO interview context - be exhaustive): `trustgraph_legal/route_candidates.py`; `trustgraph_legal/stop_gates.py`; `trustgraph_legal/debtor_governance.py`; all v1 resources added above.
  Acceptance criteria (agent-executable): `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_domain_decision_engine_v1.py -q` passes; output schema includes `schema_version`, `claim_ref`, `workflow_state`, `route_decisions`, `review_items`, `action_packet_candidates`, `source_refs`, `pii_profile`, and `non_execution_semantics`.
  QA scenarios (name the exact tool + invocation): happy: run decision engine on synthetic possible/missing/blocked cases and write `.omo/evidence/debt-collection-domain-ontology-v1/task-11-domain-decision-happy.json`; failure: unknown route id or stale legal-source version writes `task-11-domain-decision-failure.json`.
  Commit: Y | `feat(legal-domain): evaluate claim domain decisions`

- [x] 12. Add additive MCP read/explain tools for domain ontology v1
  What to do / Must NOT do: Add read-only MCP tools after the existing 21 tools: `list_claim_domain_routes`, `explain_collection_workflow_state`, `evaluate_claim_domain_decision`, and `explain_claim_action_packet`. Keep auth out of public tool arguments, preserve repo-root path bounds, use redacted envelopes, and preserve existing 21 tool order. If a security reviewer rejects a tool, replace it with an explicit deferral record and preserve the remaining compatible tools.
  Parallelization: Wave 3 | Blocked by: 5, 8, 11 | Blocks: 13, 14, 15
  References (executor has NO interview context - be exhaustive): `trustgraph_legal/mcp_domain.py`; `trustgraph_legal/mcp_handlers.py`; `trustgraph_legal/mcp_debtor_handlers.py`; `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py`; `tests/unit/legal_ontology/test_mcp_domain_tools.py`; `tests/unit/legal_ontology/test_mcp_debtor_context_tools.py`; `tests/integration/legal_ontology/test_mcp_tools.py`.
  Acceptance criteria (agent-executable): `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py -q` passes; tool list evidence proves existing 21 tools remain first and the four new claim-domain tools are appended.
  QA scenarios (name the exact tool + invocation): happy: fake-MCP calls for each new read/explain tool write `.omo/evidence/debt-collection-domain-ontology-v1/task-12-mcp-happy.json`; failure: outside-root path and missing auth resolver write `task-12-mcp-failure.json` with no token/path leak.
  Commit: Y | `feat(legal-mcp): expose claim domain ontology tools`

- [x] 13. Add integration fixtures and end-to-end domain tests
  What to do / Must NOT do: Add synthetic minimized fixtures that represent common claim states from the v2 manual: clean title route, missing service/finality proof, limitation risk, wage route with missing employer signal, bank route with missing account hint, insolvency blocker, exempt/public-benefit risk, voluntary repayment/acknowledgment path, and finance ambiguity. Use these fixtures to exercise manual inventory, ontology, legal sources, finance, workflow, routes, decision table, action packets, adapter, decision engine, and MCP if present. Do not use real PII or raw OCR bodies.
  Parallelization: Wave 4 | Blocked by: 10, 11, 12 | Blocks: 15
  References (executor has NO interview context - be exhaustive): `tests/fixtures/legal-ocr/`; `tests/fixtures/legal-ocr-pages/`; `tests/unit/legal_ontology/`; `tests/integration/legal_ontology/test_debtor_context_pipeline.py`; v2 manual operational scenarios.
  Acceptance criteria (agent-executable): `/opt/homebrew/bin/python3 -m pytest tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py tests/unit/legal_ontology/test_domain_decision_engine_v1.py -q` passes; integration outputs include route status diversity and action packet candidates without execution fields.
  QA scenarios (name the exact tool + invocation): happy: run all synthetic integration fixtures and write `.omo/evidence/debt-collection-domain-ontology-v1/task-13-integration-happy.json`; failure: fixture with raw/unsafe field or unknown legal source writes `task-13-integration-failure.json`.
  Commit: Y | `test(legal-domain): add claim domain integration fixtures`

- [x] 14. Write operator/developer docs and update working log
  What to do / Must NOT do: Add or update docs under `docs/product/debt-collection-ontology/`, recommended `claim-domain-ontology-v1.md`, and update `.omo/notes/recova-brain-working-log.md`. Explain how Domain Ontology v1, DebtorContextGraph, and MCP tools work together; how legal-source curation works; how finance calculations are bounded; how action packet schemas remain non-executing; how an agent should ask questions; and how to add new law/route/finance/workflow knowledge safely. Do not edit Recova MCP deployment runbooks unless directly needed for links.
  Parallelization: Wave 4 | Blocked by: 11, 12 | Blocks: 15
  References (executor has NO interview context - be exhaustive): `docs/product/debt-collection-ontology/debtor-context-graph-v0.md`; `.omo/notes/recova-brain-working-log.md`; this plan; final v1 resource files.
  Acceptance criteria (agent-executable): `rg -n "Claim-centered|DebtorContextGraph|evaluate_claim_domain_decision|non-executing|raw_text_included" docs/product/debt-collection-ontology/claim-domain-ontology-v1.md` passes with expected hits; focused pytest for MCP/domain docs examples passes if examples are executable.
  QA scenarios (name the exact tool + invocation): happy: docs smoke writes `.omo/evidence/debt-collection-domain-ontology-v1/task-14-docs-smoke.txt`; failure: path/PII scan over docs and evidence writes `task-14-docs-pii.txt` with `NO_FINDINGS`.
  Commit: Y | `docs(legal-domain): document claim ontology v1`

- [x] 15. Build final eval pack and final contract review
  What to do / Must NOT do: Run the full final focused suite, validate every JSON resource/evidence file, run final PII/path scans, run real v2 manual summary-only eval, and produce final contract review. If MCP tools were added, prove final tool count/order and fake-MCP behavior. Do not mark complete from self-report only; the final review artifact must cite the exact commands and outcomes.
  Parallelization: Wave 4 | Blocked by: all prior | Blocks: final verification
  References (executor has NO interview context - be exhaustive): all resources/tests/docs/evidence added above; `.omo/evidence/debtor-context-graph-v0/final-real-ocr-eval.json`; `.omo/teams/debtor-context-graph-v0-20260706/artifacts/T-final-contract-review.md`.
  Acceptance criteria (agent-executable): final focused suite passes; every resource JSON validates; final PII/path scan has no findings; final eval JSON reports resource counts, route counts, workflow states, legal source counts, action packet types, synthetic scenario results, and manual inventory counts.
  QA scenarios (name the exact tool + invocation): happy: write `.omo/evidence/debt-collection-domain-ontology-v1/final-domain-eval.json`; failure: run a negative fixture bundle and write `.omo/evidence/debt-collection-domain-ontology-v1/final-negative-eval.json` proving unsafe/missing-source cases are blocked or review-required.
  Commit: Y | `test(legal-domain): add domain ontology final eval`

## Final verification wave
> Runs in parallel after ALL todos. ALL technical verification is agent-executed. The later user okay is only a release/declaration checkpoint.
- [x] F1. Plan compliance audit
  - Verify every Must Have has an implemented artifact or a documented accepted deferral.
  - Verify every Must NOT Have is tested or scanned.
  - Evidence: `.omo/evidence/debt-collection-domain-ontology-v1/final-plan-compliance.md`.
- [x] F2. Code quality review
  - Review validators, engines, adapters, and MCP additions for size, dependency, import-floor, and duplicated-logic risks.
  - Run focused pytest, py_compile, basedpyright if available, and `git diff --check`.
  - Evidence: `.omo/evidence/debt-collection-domain-ontology-v1/final-code-quality.md`.
- [x] F3. Real manual QA
  - Run the manual inventory and domain decision smoke on summary-only data from the v2 manual.
  - Prove no raw prose, local path, or sensitive personal data appears.
  - Evidence: `.omo/evidence/debt-collection-domain-ontology-v1/final-real-manual-summary.json`.
- [x] F4. Scope fidelity and MCP contract review
  - Verify existing 21 MCP tools are preserved.
  - Verify any new MCP tools are additive, read-only, auth-safe, repo-root bounded, and redacted.
  - Verify no deployment, Supabase, Cloudflare, Vercel, or production mutation work snuck in.
  - Evidence: `.omo/evidence/debt-collection-domain-ontology-v1/final-contract-review.md`.

## Commit strategy
- Use small conventional commits per todo. Prefer one commit per completed todo unless two tightly coupled todos must land together.
- Suggested commit order:
  1. `test(legal-domain): inventory collection manual candidates`
  2. `feat(legal-domain): add claim-centered ontology v1`
  3. `feat(legal-domain): curate domain legal sources v1`
  4. `feat(legal-domain): add claim finance model`
  5. `feat(legal-domain): add collection workflow states`
  6. `feat(legal-routes): expand debt collection route catalog v1`
  7. `feat(legal-domain): add route decision table v1`
  8. `feat(legal-domain): add advisory action packet schemas`
  9. `feat(legal-check): expand domain stop gates v1`
  10. `feat(legal-domain): map debtor graphs to claim domain`
  11. `feat(legal-domain): evaluate claim domain decisions`
  12. `feat(legal-mcp): expose claim domain ontology tools` only if MCP tools are added
  13. `test(legal-domain): add claim domain integration fixtures`
  14. `docs(legal-domain): document claim ontology v1`
  15. `test(legal-domain): add domain ontology final eval`
- Keep unrelated dirty files out of every commit. Before staging, run:
  - `git status --short`
  - `git diff --check`
  - `git status --short -- <owned paths>`
- Evidence artifacts under `.omo/evidence/debt-collection-domain-ontology-v1/` may be committed when they are part of the todo acceptance, but raw/manual source material must not be committed.

## Success criteria
- Recova has a claim-centered debt-collection domain ontology v1 that connects legal, finance, workflow, evidence, routes, StopGates, scoring, and advisory action packets.
- Existing debtor-context graph v0 remains compatible and accepted.
- Existing 21 MCP tools still work and remain ordered as accepted; any new domain tools are additive and read-only.
- The v2 practical manual has been converted into PII-safe structured candidates/evidence, not copied as raw prose.
- Legal sources are curated/versioned with Korean-law MCP evidence or explicit review-needed status.
- Route decisions can explain:
  - why a route is possible;
  - what is missing;
  - what blocks it;
  - which legal/finance/workflow facts support it;
  - which advisory action packet would be prepared for human review.
- Finance/accounting reasoning is represented clearly enough for route decisions without claiming production-grade balance authority.
- All new resources have validators and focused tests.
- Final evidence proves no raw PII/path leakage, no execution behavior, no live law-MCP dependency in tests, and no unrelated deployment mutation.
