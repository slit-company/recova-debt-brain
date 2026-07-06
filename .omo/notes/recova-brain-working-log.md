# Recova Debt Brain Working Log

Updated: 2026-07-07 Asia/Seoul

## Purpose

This file is the running product/engineering memory for the Recova debt-collection brain work.
Keep it updated whenever planning, interview decisions, ontology scope, implementation status, or major tradeoffs change.

## Current Stage

We have completed the deterministic debtor-context graph v0 and are now planning the next major axis:

`debt-collection-domain-ontology-v1`

The next axis should integrate legal rules, finance concepts, collection workflow, route decision logic, evidence requirements, and compliance StopGates into one coherent domain ontology. It should not become a disconnected law database or a generic finance glossary.

## Completed Work

### 1. Debt Collection Ontology / MCP Foundation

Completed earlier v0 foundation for Recova debt collection knowledge:

- Debt-collection ontology resource.
- Legal OCR fixture manifest and validator.
- OCR markdown registry loader.
- Prompt semantics aligned to ontology IDs.
- Document classifier and field extractors.
- Case graph and StopGate engine.
- Governance/candidate promotion workflow.
- MCP domain tools and security contract.

The MCP surface originally exposed 16 debt-collection tools.

### 2. Debtor Context Graph v0

Completed plan: `.omo/plans/debtor-context-graph-v0.md`

Latest closeout commit:

- `8b8e3a1d docs(legal-graph): close debtor context graph plan`

Key integrated capabilities:

- Deterministic OCR page/document assembly.
- Synthetic OCR page fixtures and real OCR summary probe.
- Route/legal source resources.
- DebtorContextGraph schema and builder.
- Graph snapshots and diff/provenance validation.
- Route candidate matcher.
- StopGate and legal source integration.
- Debtor-context CLI.
- Additive MCP debtor graph tools.
- Debtor graph governance/review records.
- Integration/fake-MCP tests.
- Operator/developer documentation.
- Final real OCR eval evidence.
- Final contract review accepted.

Final verification evidence:

- Focused tests: `51 passed`.
- MCP tool count: `21`.
- Existing 16 MCP tools remain first.
- Five additive debtor graph tools:
  - `assemble_debtor_documents`
  - `build_debtor_context_graph`
  - `get_debtor_graph_snapshot`
  - `list_debtor_route_candidates`
  - `explain_debtor_route_candidate`
- Real OCR summary eval:
  - pages: 208
  - assemblies: 1
  - route candidates: 18
  - review items: 1
  - unknown assemblies: 1
- Final JSON evidence validates.
- Final PII/path scan has no findings.
- T final contract review: `FINAL VERDICT ACCEPTED`.

### 3. Current Domain Knowledge Input

New user-provided source:

- `/Users/cosmos/Downloads/채권추심_장기채권_법조치_루트_총정리_v2_실무확장판 (1).md`

Observed structure:

- legal baseline
- first-case intake checklist
- limitation analysis
- information-source routes
- voluntary repayment / debt acknowledgment / notarial deed routes
- title acquisition routes
- provisional remedies
- bank/financial asset execution
- wage/income execution
- lease/housing routes
- business revenue and settlement routes
- real estate routes
- vehicle/movable/business asset routes
- insurance/refund/deposit routes
- tax/deposit/distribution/compensation routes
- inheritance/family-property routes
- fraudulent transfer / hidden asset routes
- special property rights
- welfare/public benefit distinction
- property disclosure/inquiry/default registry
- rehabilitation/bankruptcy/discharge filter
- operational scenarios
- Recova recommendation engine fields, rules, scoring
- route catalog
- common practitioner mistakes
- legal-source checklist
- operating principles

## Working Product Interpretation

The next system should treat legal knowledge, finance knowledge, and collection workflow as one connected domain ontology.

The correct shape is not:

```text
law database + finance glossary + workflow checklist
```

The correct shape is:

```text
Debt Collection Domain Ontology v1
├─ Legal layer
├─ Finance layer
├─ Workflow layer
├─ Evidence layer
├─ Route layer
└─ StopGate / compliance layer
```

Each route must connect:

- the practical collection route,
- the required legal status,
- the required financial/debtor asset signal,
- the evidence/documents needed,
- the applicable law/source refs,
- blockers and StopGates,
- next-step recommendations,
- and what the agent must not claim or execute.

## Planning Direction

Planned artifact slug:

- `debt-collection-domain-ontology-v1`

Created planning files:

- `.omo/drafts/debt-collection-domain-ontology-v1.md`
- `.omo/plans/debt-collection-domain-ontology-v1.md`

Primary goal:

Build a decision-ready Recova domain brain that lets an agent interpret a debtor context graph using a richer debt-collection domain ontology.

Expected resource families:

- `resources/ontologies/recova-debt-collection-v1.json`
- `resources/legal_rules/debt_collection_domain_sources_v1.json`
- `resources/legal_routes/debt_collection_routes_v1.json`
- `resources/workflows/debt_collection_workflow_v1.json`
- `resources/decision_tables/debt_collection_route_decisions_v1.json`

Exact filenames may change during planning if existing repo conventions require a different shape.

## Current Recommendation

Proceed with an integrated ontology plan.

Do not split legal, finance, and workflow into unrelated projects. Plan them together, but implement them as separate resource layers with cross references.

## Decision Log

### 2026-07-07 - Choose the bold integrated direction

User direction:

- Go bold.
- Treat this as a creditor/claim-centered debt-collection domain ontology, not merely a narrow route recommendation module.
- Legal knowledge, finance knowledge, and collection workflow should be designed together because their links are the actual product intelligence.

Updated recommendation:

- Build `debt-collection-domain-ontology-v1` as a claim-centered Recova domain brain.
- The ontology should model the collection domain around the claim/receivable first, then connect debtor identity, case packets, documents, assets, legal status, financial ledger facts, workflow stages, and route decisions.
- v1 should include route recommendation, evidence requirements, legal/financial blockers, workflow state transitions, risk/priority scoring, and draftable action packet schemas for later human approval.
- v1 should still remain non-executing: no actual court filing, debtor contact, payment demand, or production collection action.

Working distinction:

```text
Domain Ontology v1 = what Recova knows about debt collection as a professional domain
DebtorContextGraph = what Recova knows about one debtor/claim packet at a point in time
MCP tools = how an agent asks the brain questions
```

This means the next plan should be more ambitious than a route catalog. It should create a connected ontology of:

- claim / receivable lifecycle,
- legal enforceability,
- limitation and interruption,
- financial balance and payment facts,
- evidence package requirements,
- debtor identity and third-party debtor hints,
- collection workflow stages,
- route eligibility and blockers,
- compliance StopGates,
- scoring and next-best-action recommendations,
- and review/action packet boundaries.

Recommended first implementation wave:

1. Parse and structure the v2 manual into candidate route/workflow/fact/legal-source entries.
2. Expand legal source map using Korean-law MCP evidence, then freeze it into curated versioned JSON resources.
3. Expand finance and claim/accounting ontology concepts.
4. Expand route catalog and route requirements.
5. Build route decision table v1.
6. Connect debtor-context graph facts to the new domain ontology handles.
7. Add tests, validators, and PII-safe evidence.

## Open Product Questions

These are user-owned questions that affect product shape:

1. Should v1 be optimized first for legal-execution route recommendation, or for full end-to-end collection operating workflow?
2. Should high-risk actions remain advisory-only in v1, or should the ontology already model draftable action packets for later human review?
3. Should financial accounting be lightweight in v1, or should v1 include full principal/interest/late-damages/payment-allocation logic?

Current default recommendation after the bold-direction decision:

- optimize v1 for a claim-centered domain brain, not just route recommendation;
- include end-to-end workflow states from intake through monitoring;
- include action packet schemas for later human review, but keep execution disabled;
- include finance/accounting entities and calculation contracts, with deterministic validation fixtures where feasible;
- keep all real-world court filing, debtor contact, payment demand, and production mutation out of scope.

## Working Rules For Future Updates

- Update this file whenever the user answers an interview question.
- Keep decisions short and date-stamped.
- Put detailed execution plans in `.omo/plans/`.
- Put planning drafts and ambiguity ledgers in `.omo/drafts/`.
- Do not mix deployment/MCP hosting dirty files into ontology planning unless the user explicitly changes scope.
