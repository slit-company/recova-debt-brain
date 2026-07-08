# Claim Domain Ontology v1

Status: operator/developer contract for `debt-collection-domain-ontology-v1`
Updated: 2026-07-08 Asia/Seoul
Primary resources: `resources/ontologies/recova-debt-collection-v1.json`, `resources/legal_rules/debt_collection_domain_sources_v1.json`, `resources/legal_routes/debt_collection_routes_v1.json`, `resources/workflows/debt_collection_workflow_v1.json`, `resources/workflows/debt_collection_operator_playbook_v1.json`, `resources/decision_tables/debt_collection_route_decisions_v1.json`, `resources/action_packets/debt_collection_action_packets_v1.json`
Primary code: `trustgraph_legal.domain_graph_adapter`, `trustgraph_legal.domain_decisions`, `trustgraph_legal.workflow_judgments`, `trustgraph_legal.domain_workflow_integration`, `trustgraph_legal.mcp_claim_domain_handlers`, `trustgraph_legal.mcp_domain`
Evidence roots: `.omo/evidence/debt-collection-domain-ontology-v1/`, `.omo/evidence/debt-collection-knowledge-expansion-v1/`, `.omo/evidence/debt-brain-structural-depth-v1/`

## Purpose

Claim Domain Ontology v1 is Recova's claim-centered debt-collection domain brain. It explains how a source-backed debtor context becomes workflow judgment, advisory route decisions, review items, and draft-only action packet candidates.

The system is non-executing. It does not file court documents, contact debtors, send payment demands, mutate production ledgers, initiate seizure, or treat fixture finance calculations as authoritative balances.

## Mental Model

The three layers have different ownership boundaries:

| Layer | Root | Responsibility |
| --- | --- | --- |
| Domain Ontology v1 | `Claim` / `Receivable` | Defines the professional debt-collection knowledge model: legal sources, finance concepts, workflow states, routes, StopGates, scoring, and action packet schemas. |
| DebtorContextGraph | debtor/packet runtime graph | Records what Recova knows about one debtor or receivables packet at a point in time, including source refs, snapshots, fact handles, and v0 route candidates. |
| MCP tools | tool envelope | Let an agent ask read/explain/evaluate questions without receiving raw OCR text or executable collection instructions. |

`DebtorContextGraph` remains the runtime memory graph. Claim Domain Ontology v1 consumes graph facts through a compatibility adapter; it does not replace debtor identity, graph snapshots, or v0 route matching.

```text
OCR pages or reviewed graph facts
  -> DebtorContextGraph
  -> claim-domain adapter payload
  -> deterministic workflow judgment and route decision engines
  -> advisory route decisions and review items
  -> draft-only action packet candidates for human review
```

## Collection Workflow Judgment Brain

The structural-depth wave makes workflow judgment the center of the product surface. The brain now answers operator questions before route execution questions:

- where the case currently sits in the collection workflow;
- what practical next move is most useful;
- which routes are premature, blocked, low-yield, or ready only for review;
- which missing inputs or support-layer checks must be resolved;
- which remediation loop should happen next.

The output contract is `trustgraph-collection-workflow-judgment/v1`, surfaced as `workflow_judgment` on claim-domain decisions. It includes `current_stage`, `posture`, `next_best_actions`, `premature_actions`, `missing_inputs`, `review_items`, `remediation_loop`, `reasons`, `source_refs`, `pii_profile`, and `non_execution_semantics`.

The real domain/MCP boundary consumes structured workflow support through generic payload fields, not through scenario names or test labels. Semireal fixtures may carry PII-safe `workflow_support`; adapters should project that support into standard `evidence_checkpoint`, `finance_bridge`, and `legal_checkpoints` fields, and `domain_workflow_integration` also accepts the same fields when they remain nested under `workflow_support`. This keeps exact workflow stage, action, posture, and remediation-loop behavior stable at both `evaluate_claim_domain_decision` and the MCP `evaluate_claim_domain_decision` envelope without scenario-id branching.

Legal, evidence, finance, and StopGate layers are support layers for this workflow judgment:

| Support layer | How it supports workflow judgment | What it must not become |
| --- | --- | --- |
| Legal checkpoints | Hold or review limitation, title, service, finality, execution-clause, source-approval, insolvency, and protected-asset states. | A free-form legal advice engine or a way to clear StopGates from memory/web/LLM inference. |
| Evidence quality | Distinguish source-backed, stale, placeholder, derived, low-confidence, and conflicting facts before route escalation. | Raw document analysis, raw OCR output, or a document automation product center. |
| Finance bridge | Turn fixture finance ambiguity into reconciliation, allocation, unsupported-interest, or disputed-balance workflow signals. | An authoritative ledger, collectable balance, or payment-demand engine. |
| Operator playbook | Defines practical stages, next-action types, premature-action reasons, and remediation loops. | A direct execution checklist for filings, contact, seizure, or ledger mutation. |

This keeps the product identity as collection workflow intelligence: legal, evidence, and finance constraints guide the operator judgment, but they do not replace it.

## Resource Map

| Resource | Current contract |
| --- | --- |
| `resources/ontologies/recova-debt-collection-v1.json` | Claim-centered ontology with 22 classes, 20 object properties, and 11 datatype properties. |
| `resources/legal_rules/debt_collection_domain_sources_v1.json` | Frozen domain legal-source map with 21 curated sources, 12 workflow source refs, `evaluation_date`, effective-date metadata, and Korean-law lookup evidence refs. |
| `resources/legal_routes/debt_collection_routes_v1.json` | 32 advisory route templates across 19 route families; `direct_execution_allowed` remains false. |
| `resources/workflows/debt_collection_workflow_v1.json` | 12 canonical states, 23 transitions, and 2 monitoring/blocked loops. Route decision logic is linked but kept out of workflow state definitions. |
| `resources/workflows/debt_collection_operator_playbook_v1.json` | Practical operator stages, next-action types, premature-action reasons, missing-input expectations, checkpoint inputs, and remediation loops for workflow judgment. |
| `resources/decision_tables/debt_collection_route_decisions_v1.json` | Deterministic route scoring/status table for `possible`, `review_required`, `missing_facts`, and `blocked` outcomes. |
| `resources/action_packets/debt_collection_action_packets_v1.json` | Six draft-only packet schemas: evidence request, legal-action review, finance review, contact review, monitoring/retry, and insolvency/recovery review. |
| `resources/finance/claim_finance_model_v1.json` | Fixture-only finance model for principal, interest, late damages, enforcement costs, payments, allocations, remaining balance, assignment/succession, guarantee/surety, and review triggers. |
| `resources/legal_rules/debt_collection_stopgate_domain_v1.json` | Domain StopGate rules for limitation, insolvency/discharge, exempt assets, missing title/service/finality proof, legal-source uncertainty, finance ambiguity, and direct-execution requests. |

## Claim-Centered Identity

Claim Domain Ontology v1 starts from `Claim` / `Receivable`, not from a display name or a debtor profile. A debtor can have multiple claims, and one claim can connect to:

- creditor, assignee, assignor, guarantor, and successor roles;
- case packet and document evidence;
- enforcement title, service, finality, and execution-clause facts;
- limitation and interruption facts;
- ledger and finance facts;
- asset hints and third-party debtor handles;
- workflow state;
- route decisions, StopGates, and governance records.

Do not merge or reason across claims using a person's display name alone. Use source-backed graph IDs, claim refs, source refs, snapshot IDs, and adapter fact handles.

## Legal-Source Curation

Domain v1 legal reasoning uses frozen JSON resources, not live legal search during deterministic tests or tool calls.

Operator rules:

- Every domain legal source must have a stable `source_id`, source metadata, review status, effective-date decision, and route/workflow/StopGate usage.
- The current resource carries `evaluation_date: 2026-07-07` and `rule_source_version: recova-debt-collection-domain-sources@v1.0.0`.
- Korean-law MCP discovery evidence is kept as execution evidence, then curated into `resources/legal_rules/debt_collection_domain_sources_v1.json`.
- If a law, article, or effective date is ambiguous, record it as review-needed rather than inventing authority.
- Agents must not clear StopGates from memory, web search, or free-form LLM analysis. Add a reviewed source or create a governance/review item.

To add legal knowledge safely:

1. Add or update the curated source record.
2. Update any route, workflow, decision-table, or StopGate references to the stable `source_id`.
3. Run the relevant validator and focused tests.
4. Record happy/failure evidence and a PII/path scan.
5. Keep deterministic tests independent of live Korean-law MCP.

Current knowledge-expansion state:

- Remaining review-needed legal-source records have explicit conservative dispositions and supporting/replacement refs where available.
- Korean-law MCP and public/official source discovery were used as evidence-gathering surfaces; adopted references are frozen into repo-local resources and evidence.
- Deterministic tests and local MCP calls do not depend on live Korean-law MCP or web access.
- Any unresolved source ambiguity remains a human/legal-review reason; it must not be converted into a route-ready decision by memory, web search, or agent inference.

## Finance Boundary

The finance model is a contract for decision support, not a production ledger.

Allowed:

- represent principal, interest, late damages, enforcement/legal costs, payments, payment allocation, remaining balance, assignment/succession, guarantee/surety, and reimbursement/subrogation candidates;
- run deterministic fixture calculations when amount, rate, period, payment date, and allocation rule are explicit;
- emit finance review items when the model sees ambiguity, unsupported statutory calculation, dispute, missing source evidence, or conflicting payments.

Not allowed:

- mutate a ledger;
- claim an authoritative balance;
- demand payment;
- hide finance ambiguity inside a route score;
- use production account or payment identifiers in docs, evidence, or MCP responses.

Finance payloads and action candidates keep `raw_text_included: false` and `source_text_included: false`.

Knowledge-expansion hardening keeps finance decisions review-safe when any of these are present:

- unsupported or conflicting payment allocation inputs;
- disputed amount facts or placeholder source refs;
- stale finance model source versions;
- assignment/succession, guarantee/surety, subrogation, reimbursement, enforcement-cost, or balance evidence ambiguity.

Those conditions may produce review items or advisory packet candidates, but they do not produce an authoritative balance, a payment demand, or a ledger mutation.

## Workflow And Route Decisions

Workflow judgment is evaluated before an operator treats any route as ready. It uses the operator playbook, route decisions, evidence quality, finance review signals, legal checkpoints, and the claim-domain adapter payload to explain the case stage and next operational loop.

For semireal coverage, exact workflow outcomes are asserted at both the direct domain decision surface and the MCP decision surface. The boundary preserves exact behavior when structured support appears either as top-level `evidence_checkpoint`, `finance_bridge`, and `legal_checkpoints` fields or as the same fields nested under `workflow_support`. If all structured support is absent, deterministic fallback logic remains conservative and review-safe.

The canonical workflow states are:

```text
intake
identity_evidence_package
limitation_review
title_acquisition
service_finality_execution_clause
voluntary_recovery
provisional_remedy
asset_discovery
execution_route_selection
insolvency_discharge_review
monitoring_retry
closure
```

Route decisions are deterministic. The decision table links routes to required fact handles, missing handles, blocking handles, workflow preconditions, finance review codes, legal source review status, StopGate blockers, scoring components, and next-step action packet type.

Status semantics:

| Status | Meaning | Operator behavior |
| --- | --- | --- |
| `possible` | Required handles are present, workflow preconditions hold, sources are approved, and no StopGate blocker is active. | Prepare an advisory review packet only. Preserve source refs. |
| `missing_facts` | Required facts are absent. | Request evidence, re-run graph extraction, or add reviewed facts. |
| `review_required` | Legal source, workflow, finance, or StopGate state needs human/service review. | Stop recommendation until review or reprocessing clears it. |
| `blocked` | A blocking handle or StopGate reason prevents the route. | Do not recommend the route except as a remediation/review item. |

The score components are named and traceable: required facts present, workflow precondition met, no StopGate blockers, legal sources approved, finance review clear, and asset signal present.

The expanded scenario fixture set now exercises rare and high-risk collection situations including protected income/property, stale or disputed finance data, partial payments, insolvency/bankruptcy signals, service/finality uncertainty, identity uncertainty, business receivables, movable assets, inheritance, and monitoring/retry cases. The expected status mix intentionally includes `possible`, `review_required`, `missing_facts`, and `blocked`; a broader `possible` count is not a success metric if it weakens StopGates.

## Action Packet Non-Execution Boundary

Action packets are schemas for human review, not commands. Every packet candidate remains non-executing with `non_execution_semantics: advisory_only_human_review_required` and `direct_execution_allowed: false`.

Forbidden packet fields include:

- `filing_destination`
- `filing_destination_court`
- `court_filing_endpoint`
- `submission_endpoint`
- `debtor_contact_payload`
- `debtor_contact_channel`
- `debtor_phone`
- `debtor_email`
- `payment_request_payload`
- `executable_instruction`
- `collection_execution_command`

If an operator needs an actual filing, contact, demand, seizure, settlement, or payment workflow, that must happen outside this ontology contract and only through a separately approved human/legal process.

Human-review workflow artifacts are still review/governance records only. An operator approval may record review status, rationale, source refs, and audit fields; it does not flip `direct_execution_allowed` to true and must not add debtor-contact, court-filing, payment-request, seizure, ledger-write, or production-storage payloads.

## MCP Surface

The MCP facade remains importable without the global MCP SDK:

```python
from trustgraph_legal.mcp_domain import invoke_tool, list_tools
```

Current tool count is 25:

- the original 16 debt-collection tools remain first;
- five `debtor_graph` tools remain appended after the original 16;
- four claim-domain tools are appended after the existing 21.

The claim-domain tools are:

| Tool | Use |
| --- | --- |
| `list_claim_domain_routes` | List advisory v1 route summaries, optionally by route family. |
| `explain_collection_workflow_state` | Explain a workflow state's purpose, preconditions, exit conditions, evidence, review states, and source refs. |
| `evaluate_claim_domain_decision` | Evaluate deterministic claim-domain workflow judgment and route decisions from an adapter payload and frozen v1 resources. |
| `explain_claim_action_packet` | Explain an advisory packet schema and its forbidden execution/contact fields. |

Example read-only smoke:

```bash
python3 - <<'PY'
from pathlib import Path
from trustgraph_legal.mcp_domain import invoke_tool, list_tools

root = Path.cwd()
print(len(list_tools()))
print([tool["tool_name"] for tool in list_tools()[-4:]])
print(invoke_tool("list_claim_domain_routes", {"family": "financial_asset_execution"}, root)["result"]["route_count"])
print(invoke_tool("explain_collection_workflow_state", {"state_id": "execution_route_selection"}, root)["result"]["non_execution_semantics"])
print(invoke_tool("explain_claim_action_packet", {"packet_type": "legal_action_review"}, root)["result"]["direct_execution_allowed"])
PY
```

Public MCP arguments must not include `authorization`, `token`, or `bearer`. Auth is context-only through the MCP adapter. Path arguments are bounded to the repository root, and outside-root failures must not echo the attempted path.

Every envelope keeps:

```json
{
  "pii_profile": {
    "raw_text_included": false,
    "source_text_included": false
  },
  "redaction": {
    "default": "redacted",
    "raw_text_included": false,
    "source_text_included": false
  }
}
```

## Agent Use Pattern

An agent should ask the domain brain questions in this order:

1. Build or load a `DebtorContextGraph` from redacted OCR pages or reviewed graph facts.
2. Adapt the graph into `trustgraph-claim-domain-adapter/v1`.
3. Ask `list_claim_domain_routes` to inspect the route families available for the claim state.
4. Ask `explain_collection_workflow_state` for the current workflow state and evidence requirements.
5. Ask `evaluate_claim_domain_decision` with the adapter payload, workflow state, candidate route IDs, and any finance review codes.
6. Read `workflow_judgment` first: it is the operator-facing center for stage, posture, next best actions, premature actions, missing inputs, and remediation loop.
7. If the adapter has structured workflow support, keep it in the standard `evidence_checkpoint`, `finance_bridge`, and `legal_checkpoints` fields, or preserve the same fields under `workflow_support` for the domain boundary to normalize. Do not branch on `scenario_id`, expected-test labels, or fixture-only names.
8. Ask `explain_claim_action_packet` only to understand the schema for a candidate packet. Do not turn it into a filing, contact, or payment instruction.

If the MCP response disagrees with the agent's memory, prefer the MCP response when it has source refs and resource versions. If newer evidence exists, ingest it or create a reviewed fact/governance item instead of overriding the graph locally.

## Adding New Knowledge

Use the smallest resource boundary that matches the change:

| Change | Primary file |
| --- | --- |
| New domain class/property | `resources/ontologies/recova-debt-collection-v1.json` |
| New or revised legal source | `resources/legal_rules/debt_collection_domain_sources_v1.json` |
| New route family/template | `resources/legal_routes/debt_collection_routes_v1.json` |
| Workflow state or transition | `resources/workflows/debt_collection_workflow_v1.json` |
| Eligibility/scoring/reason changes | `resources/decision_tables/debt_collection_route_decisions_v1.json` |
| Human-review packet schema | `resources/action_packets/debt_collection_action_packets_v1.json` |
| Finance concept/review trigger | `resources/finance/claim_finance_model_v1.json` |
| Legal/compliance blocker | `resources/legal_rules/debt_collection_stopgate_domain_v1.json` |

Safe-change checklist:

- update the resource and validator together;
- update focused tests and happy/failure evidence;
- preserve `Claim` / `Receivable` as the ontology root;
- preserve `DebtorContextGraph` identity and snapshot semantics;
- keep `direct_execution_allowed: false`;
- keep `raw_text_included: false` and avoid source text or local paths in evidence;
- run JSON validation, focused pytest, PII/path scan, and `git diff --check`;
- avoid Recova MCP deployment runbooks unless a link target must be corrected.

## Evidence For This Contract

Todo 14 evidence lives under `.omo/evidence/debt-collection-domain-ontology-v1/`:

- `task-14-docs-smoke.txt`
- `task-14-docs-pii.txt`

The team handoff report is `artifacts/T-domain-docs-report.md`.

The follow-on knowledge-expansion wave lives under `.omo/evidence/debt-collection-knowledge-expansion-v1/`:

- Goal 1/2 evidence: legal-source audit, finance-source channel audit, scenario gap inventory, human-review workflow contract, and local MCP 25-tool order smoke.
- Goal 3 evidence: source dispositions, expanded synthetic scenarios, JSON validation, local MCP order smoke, and accepted Goal 3 review.
- Goal 4 evidence: finance/review hardening, StopGate/domain decision hardening, 52 focused tests, Python compile/type checks, JSON validation, local MCP order smoke, PII/path scan, deployment-boundary scan, and accepted Goal 4 review.
- Goal 5/G011 evidence: final docs smoke, final focused eval, final PII/path scan, final local MCP order smoke, and final contract review.

Deployment remains intentionally out of scope for this wave: no remote MCP deploy, no remote live smoke, and no client-facing remote setup docs update unless that work is explicitly reopened.

The structural-depth wave lives under `.omo/evidence/debt-brain-structural-depth-v1/`:

- Task evidence documents the operator playbook, workflow judgment engine, evidence quality checkpoint, finance bridge, legal workflow checkpoints, domain/MCP integration, and eight semireal workflow scenarios.
- Final readiness evidence is recorded in `final-*` files under that evidence root.
- This wave proves local deploy-readiness only. It does not perform or claim remote MCP deployment, remote live smoke, client setup changes, public admin/write tools, debtor contact, filing, seizure, payment demand, production ledger mutation, or authoritative balance output.
