---
slug: debt-brain-structural-depth-v1
status: local-readiness-gate-in-progress
intent: execute approved structural-depth wave
pending-action: complete Todo 8 validation and final evidence
approach: repo-local structural brain deepening before remote deployment; preserve advisory-only/non-execution semantics while adding deterministic reasoning depth, evidence quality, and gap-audit fixtures
---

# Draft: debt-brain-structural-depth-v1

## Components (topology ledger)
<!-- Lock the SHAPE before depth. One row per top-level component that can succeed or fail independently. -->
<!-- id | outcome (one line) | status: active|deferred | evidence path -->
| case-type-reasoning-depth | Add more granular claim/case type interpretation so routes are not just candidate IDs but explainable legal/workflow families. | active | .omo/evidence/debt-brain-structural-depth-v1/ |
| evidence-strength-conflict-model | Represent evidence sufficiency, conflict, source freshness, confidence, and missing proof as first-class decision inputs. | active | .omo/evidence/debt-brain-structural-depth-v1/ |
| limitation-title-service-finality-reasoning | Deepen 시효, 집행권원, 송달, 확정, 집행문 reasoning without allowing free-form inference to clear StopGates. | active | .omo/evidence/debt-brain-structural-depth-v1/ |
| finance-review-depth | Expand fixture-only finance review into a clearer balance/accounting risk model while keeping it non-authoritative. | active | .omo/evidence/debt-brain-structural-depth-v1/ |
| stopgate-explainability-hardening | Make blocked/review decisions easier to inspect by linking reason, fact, source, packet, and next remediation. | active | .omo/evidence/debt-brain-structural-depth-v1/ |
| semireal-case-gap-audit | Compare existing synthetic coverage against practical debt-collection scenarios and add deterministic gap fixtures. | active | .omo/evidence/debt-brain-structural-depth-v1/ |

## Open assumptions (announced defaults)
<!-- Intent is UNCLEAR: research resolves ambiguity, defaults are adopted (not asked), and each is surfaced in the plan's human TL;DR for veto. -->
<!-- assumption | adopted default | rationale | reversible? -->
| deployment scope | No remote MCP deployment, remote smoke, or client-facing remote setup docs in this plan. | User asked to develop the brain first; current working log says deployment was deferred. | yes |
| legal posture | Advisory-only, human-review-required semantics remain mandatory everywhere. | Existing route, decision, action packet, and finance layers all encode non-execution constraints. | no |
| data posture | Use versioned repo resources, curated source refs, synthetic/semireal fixtures, and PII-safe evidence only. | Current fixtures and final eval explicitly avoid raw text/contact/court destination payloads. | no |
| source research | If law/finance facts need refresh, research is frozen back into static reviewed resources before engine use. | Docs say StopGates must not be cleared from memory, web search, or free-form LLM analysis. | no |
| finance posture | Finance remains decision-support only, never an authoritative ledger or collectable balance engine. | Current finance model says fixture-only/non-authoritative and emits review items for ambiguity. | no |
| implementation style | Prefer resource/schema/test expansion around existing engines before introducing new service surfaces. | Current architecture already has route decision, adapter, StopGate, finance, workflow, and MCP explanation seams. | yes |
| MCP surface | Preserve the local 25-tool surface and existing tool order unless a later explicit migration says otherwise. | Current accepted state is 25 tools; older docs may mention legacy counts and should not drive this wave. | no |
| admin/public surface | Do not add public admin tools or public mutation capabilities. | Contract notes conflict around admin language; safest default is repo-local/governance-only. | no |
| deploy boundary | Stop at local deploy-readiness evidence, not actual remote deploy. | User asked brain development first; deployment remains a separate explicit task. | yes |

## Findings (cited - path:lines)
- Current domain decision output already composes adapter payload, route decisions, review items, action packet candidates, source refs, resource versions, PII profile, and advisory-only semantics. See `trustgraph_legal/domain_decisions.py:74-117`.
- Route status is currently determined by blocking facts, missing facts/workflow, legal review, and finance review. Priority scoring is deterministic but shallow: named triggers include required facts, workflow, no blockers, legal source approval, finance clear, and asset signal. See `trustgraph_legal/route_decisions.py:126-164` and `trustgraph_legal/route_decisions.py:218-247`.
- The adapter already projects debtor graph data into claim roots, fact handles, route candidates, governance records, a case graph, source refs, and PII-safe metadata. See `trustgraph_legal/domain_graph_adapter.py:46-92`.
- Fact handles carry provenance, confidence, review status, and derived flags, but there is not yet a richer evidence-packet or conflict model feeding route decisions. See `trustgraph_legal/domain_graph_adapter_handles.py:82-105`.
- Domain StopGate v1 already evaluates legal-source approval, service/finality/execution proof, finance ambiguity, unsupported route execution, and route legal-source uncertainty. See `trustgraph_legal/stop_gates_domain_v1.py:98-116` and `trustgraph_legal/stop_gates_domain_v1.py:207-230`.
- Action-packet explanation already exposes purpose, review status, no-direct-execution, required inputs, permitted next states, route linkage, forbidden fields, PII profile, and advisory semantics. See `trustgraph_legal/mcp_claim_domain_handlers.py:110-131`.
- Finance calculation is fixture-only and intentionally returns review-needed instead of balance when source refs, statutory/complex rates, allocation conflicts, or disputed amounts appear. See `trustgraph_legal/finance_claims.py:175-238`.
- Current static surface is substantial but finite: 32 routes, 32 route decisions, 14 domain StopGate rules, 12 workflow states, 6 action-packet schemas, and 26 synthetic scenarios.
- Product docs state the system must not file, contact, mutate ledgers, initiate seizure, or treat fixture finance calculations as authoritative balances. See `docs/product/debt-collection-ontology/claim-domain-ontology-v1.md:13`.
- Product docs state agents must not clear StopGates from memory, web search, or free-form LLM analysis. See `docs/product/debt-collection-ontology/claim-domain-ontology-v1.md:70-74`.
- Working log confirms the accepted local brain state and that remote MCP deployment/client docs were deferred. See `.omo/notes/recova-brain-working-log.md:17` and `.omo/notes/recova-brain-working-log.md:356-370`.
- Read-only architecture review confirmed several high-value seams for this wave: finance is adjacent rather than formally bridged into decisions, the generated case graph is flat and relationship-light, the stopgate resource version is surfaced more than it is used in decision policy, and multi-root claim data is projected but mostly collapsed downstream.
- Pre-plan critique found guardrails to carry into the full plan: preserve 25-tool local MCP order, avoid public admin surfaces, separate deploy-readiness from remote deployment, keep ambiguous law/finance/evidence/conflict states in review/hold, and make PII/path scan plus JSON/type/test evidence mandatory.

## Decisions (with rationale)
- Plan this as a structural-depth wave, not productization. Rationale: the user explicitly wants to develop the brain before the next work, and current deployment work is deferred.
- Use six top-level workstreams: case-type reasoning, evidence quality/conflict, legal precondition depth, finance review depth, StopGate/explainability, and semireal gap audit. Rationale: these are separable enough to test, but together they deepen the actual reasoning loop.
- Treat evidence quality as the central new connective tissue. Rationale: the current system already has facts, confidence, source refs, review status, decisions, and StopGates, but route decisions mostly consume fact-handle presence rather than evidence sufficiency/conflict.
- Keep every new output deterministic and PII-safe. Rationale: existing acceptance evidence and docs make this a hard product contract.
- Require tests/evidence per workstream plus final plan compliance review before execution is called complete. Rationale: this is architecture-sensitive and can accidentally weaken StopGates if only happy paths are tested.
- Put finance-into-decision and evidence-into-route evaluation early in the eventual plan. Rationale: these are the two places where the current brain is most clearly under-connected rather than merely under-populated.
- Treat user approval as a planning/release gate, not an automated verification step. Rationale: verification remains agent-executed, but plan mode must pause before filling the executable plan.
- Explicitly separate StopGate decision semantics from route decision status semantics in tests. Rationale: conflating `possible/missing_facts/review_required/blocked` with StopGate clear/hold/block would weaken safety.

## Scope IN
- Repo-local resource/schema/code/test changes that deepen the debt-collection domain brain.
- Deterministic adapters or engines for evidence packet scoring, conflict handling, legal precondition state, finance review items, and recommendation explanations.
- Static resource updates for routes, decision tables, StopGate rules, finance model, workflow/action packets, and fixtures when required.
- Synthetic and semireal no-PII case fixtures that expose practical gaps.
- Focused unit/integration tests, JSON validation, type/compile checks, local MCP/tool-order smoke if surfaces change, and evidence artifacts under `.omo/evidence/debt-brain-structural-depth-v1/`.
- Local deploy-readiness checks that prove the brain remains ready to redeploy later, without actually deploying.

## Scope OUT (Must NOT have)
- No remote deployment, remote live smoke, production service changes, or client-facing remote setup docs.
- No direct execution of collection actions, court filings, debtor contact, seizure, payment demand, or production ledger mutation.
- No raw PII, raw OCR text, debtor contact payloads, filing destinations, or court destination payloads in evidence or action candidates.
- No free-form LLM/legal-web inference that directly clears StopGates; reviewed/static resources must carry adopted facts.
- No authoritative balance calculation; finance remains fixture/review support only.
- No public admin MCP tools, no public write/mutation tool surface, and no change that reorders or removes the accepted local MCP tools.
- No claim that remote deployment happened; this plan may only say deploy-ready if local checks prove it.

## Open questions
- None blocking. Adopted defaults above should be surfaced for user veto before writing the full plan.

## Interview log

### Round 1 - Evidence strength/conflict model
- User preference: develop through interview rounds, and update this Markdown memo on every round.
- User question: What does component 2, `evidence-strength-conflict-model`, mean?
- Working explanation: Component 2 means the brain should stop treating evidence as merely "fact handle exists / does not exist" and instead evaluate whether the evidence is strong enough, current enough, source-backed enough, and internally consistent enough to support a route recommendation.
- Practical meaning: A route should not become stronger just because a field exists. The system should ask: which document proves it, how direct is the proof, is it stale, is it contradicted by another document, does it prove the exact legal prerequisite, and should ambiguity create `review_required` or `blocked`?
- Initial design direction: evidence quality should feed both route decisions and StopGate/review items. Strong, source-backed, non-conflicting evidence can support advisory recommendation; conflicting, stale, missing, placeholder, or indirect evidence should create explicit review items and may block clearance depending on legal materiality.

### Round 2 - Reframe around collection workflow know-how
- User correction: The main value should not be lawyer-like legal document handling. The bigger direction is embedding debt-collection workflow know-how: given a case situation, the brain should understand what judgment the operator should make next across the broader collection workflow.
- Revised interpretation: Evidence quality is not the product center. It is a support layer for workflow judgment. The core brain should model collection-stage diagnosis, next-best judgment, route sequencing, operational timing, review/remediation loops, and practical collection strategy.
- Direction change: Reframe this plan from "deeper legal/evidence reasoning first" to "collection workflow intelligence first, with legal/evidence/finance as guardrails and inputs."
- Practical examples of desired intelligence:
  - identify whether the case is still in intake, evidence completion, title acquisition, execution route selection, asset discovery, enforcement, monitoring, settlement, insolvency review, or closure;
  - decide whether the next useful move is evidence collection, debtor/asset enrichment, limitation review, payment-order/title route, attachment route, finance reconciliation, legal review, or monitoring;
  - distinguish "cannot proceed because legally blocked" from "can proceed, but the best operational move is not litigation yet";
  - explain why a route is premature, low-yield, high-risk, or operationally inefficient;
  - preserve legal safety without making the system feel like a statute-only lawyer bot.
- Planning implication: The eventual executable plan should likely reorder components so `workflow-judgment-model` or `collection-operator-playbook` becomes the first-class center. `evidence-strength-conflict-model` remains necessary, but as a checkpoint/input model inside the workflow rather than the main identity of the brain.

### Round 3 - Confirm intended ontology/debtor graph architecture
- User check: Confirm whether the assistant understands the intended structure behind the ontology and debtor graph.
- Current understanding: The architecture is not just a legal ontology or document QA layer. It is a structured debt-collection brain where a debtor/case graph holds facts, entities, evidence, claims, routes, workflow state, governance/review records, and source provenance; then a claim-domain ontology projects that graph into professional collection judgment.
- Intended shape:
  - Debtor graph / case graph: memory substrate containing debtor, claim, documents, facts, assets, payments, events, source refs, confidence, and review markers.
  - Domain ontology: typed interpretation layer that turns raw graph facts into collection concepts such as claim status, title status, service/finality status, limitation risk, finance review, asset signal, route candidate, and workflow stage.
  - Decision brain: deterministic/review-safe layer that decides route readiness, next-best operational move, blockers, missing inputs, review items, and action-packet candidates.
  - StopGate/governance: safety layer that prevents the system from treating ambiguous legal/finance/evidence states as cleared.
  - MCP/tool surface: external answer layer that exposes this brain as structured, source-backed, non-executing advisory tools.
- Important correction from user direction: The debtor graph is not being built merely to store legal facts. It should support collection workflow intelligence: where the case is, what is worth doing next, what is premature, what is risky, and what operational loop should happen before escalation.

### Round 4 - Approval to continue plan
- User approval: Continue building the plan.
- Planning decision: Fill the executable plan now, using the user's correction as the center of gravity.
- Updated plan center: `collection-workflow-judgment-brain` comes first. Legal/evidence/finance/StopGate layers are necessary support layers, but they should serve practical collection workflow judgment rather than dominate the product identity.
- Planning goal: The final plan should tell executors how to make Recova answer: "Where is this case in the collection workflow, what is the next best operational judgment, why is it not yet ready or ready, and what review/remediation loop should happen?"

### Round 5 - Executable plan reviewed
- Plan written: `.omo/plans/debt-brain-structural-depth-v1.md`
- Review outcome: high-accuracy plan review passed with `OKAY` after two iterations.
- Fixes made during review:
  - Removed Todo 4/5 dependency on workflow judgment tests that are created later by Todo 2.
  - Added concrete commands for JSON validation, PII/path scan, MCP 25-tool order smoke, manual QA, and scope-fidelity checks.
  - Added an explicit F4 command requiring docs and sample workflow output to prove the final product story remains collection workflow intelligence first.
- Current next action: wait for explicit execution start, likely `$start-work`, before changing product code.

### Round 6 - Teammode execution question
- User question: What about teammode?
- Answer direction: Teammode is appropriate for the implementation phase, not for the interview/planning phase that just completed.
- Reason: The written plan has independent Wave 1 slices: operator playbook, evidence quality checkpoint, finance workflow bridge, and legal workflow checkpoints. These can be developed in parallel, but they touch related concepts and need coordination, which is exactly the teammode use case.
- Proposed team split for execution:
  - Member A: operator playbook resource and validation.
  - Member B: evidence quality/conflict checkpoint.
  - Member C: finance review bridge.
  - Member D: legal precondition workflow checkpoints.
  - Leader/main thread: coordination, integration, review, and final verification.
- Wave 2 should begin only after Wave 1 reports: workflow judgment engine, domain/MCP integration, scenario expansion, and docs/evidence.
- Important teammode rule: members should be real Codex threads with durable team state, not ephemeral subagents. If file ownership overlaps, members should use separate worktrees and integrate through the leader.

## Approval gate
status: execution-approved
approval-needed: none for local Todo 8 validation
<!-- When exploration is exhausted and unknowns are answered, set status: awaiting-approval. -->
<!-- That durable record is the loop guard: on a later turn read it and resume at the gate instead of re-running exploration. -->

## Execution update

### 2026-07-08 - Todo 8 docs/readiness gate
- Todos 1 through 7 are recorded as complete in the plan and evidence ledger.
- Product docs now frame the structural-depth result as collection workflow judgment first.
- Legal, evidence, finance, and StopGate layers remain support layers and guardrails.
- Todo 8 validation is local only: final evidence may prove local deploy-readiness, but must not claim remote MCP deployment, remote smoke, client-facing setup changes, public admin/write surfaces, contact, filing, seizure, payment demand, ledger mutation, or authoritative balance output.

### 2026-07-08 - Todo 8 real-boundary refresh
- Todo 8 was reopened after Todo 6/7 global review found the real domain/MCP boundary collapsed the eight semireal scenarios to the same stage.
- The approved refresh state is stricter: fixture `workflow_support` is projected into generic `evidence_checkpoint`, `finance_bridge`, and `legal_checkpoints` payload fields, then consumed by `domain_workflow_integration` before fallback logic.
- Final docs and evidence should state exact stage/action/posture/remediation-loop assertions now pass at both direct domain and MCP surfaces without scenario-id or expected-label branching.
