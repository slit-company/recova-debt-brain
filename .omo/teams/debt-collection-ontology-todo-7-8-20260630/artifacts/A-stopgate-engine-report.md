# A StopGate Engine Report

Member: A / stopgate-engine
Worktree: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debt-collection-ontology-todo-7-8-20260630/worktrees/A`
Branch: `team/debt-collection-ontology-todo-7-8-20260630/A`

## Deliverable

Implemented Todo 7 deterministic legal StopGate engine with:

- static curated v0 rule source at `resources/legal_rules/debt_collection_stopgate_v0.json`
- engine API in `trustgraph_legal.stop_gates`
- rule loading and typed payload models in `trustgraph_legal.stopgate_rules` and `trustgraph_legal.stopgate_types`
- CLI surface: `python3 -m trustgraph_legal.check --case <case-graph.json>`
- focused tests in `tests/unit/legal_ontology/test_stop_gates.py`

## Decisions

- Decision labels are deterministic Korean labels: `가능`, `불가능`, `보류`.
- v0 rules are static curated JSON, versioned as `recova-debt-collection-stopgate@v0.1.0`, and marked `static-curated-v0-no-live-updates`.
- Output uses source pointers only: `document_id`, `source_ref`, `chunk_id`, `line_start`, `line_end`, `fact_id`, `fact_type`, and confidence. It does not emit raw source text or excerpts.
- Facts with absent provenance or placeholder provenance such as `"missing"` produce `invalid_fact_without_provenance` and cannot clear StopGates.
- Draft, reviewed-only, deprecated, superseded, or otherwise unapproved rule-source state produces `보류` with `rule-source-unapproved`.
- Current `payment-order` evidence is not treated as enough by itself for execution-title clearance. The engine still requires source-backed service/finality/execution-clause evidence; missing proof returns `missing_execution_clause`.
- Broader v0 contract types from member C were handled explicitly. Supported StopGate-relevant types include `attachment-collection-application`, `judgment-or-decision`, `attachment-target-priority`, and `legal-rule-source`. Unknown or unsupported types return review StopGates rather than allowing false `가능`.

## Coverage

Focused tests cover red/green behavior for:

- `discharge_proceeding_detected`
- `missing_execution_clause`
- `limitation_risk`
- `exempt_claim_targeted`
- `assignment_chain_broken`
- `amount_mismatch`
- `identity_uncertain`

Additional contract tests cover:

- `invalid_fact_without_provenance`
- placeholder `"missing"` provenance
- `rule-source-unapproved`
- broader v0 document type support/review behavior
- pointer-only source refs
- CLI output contract

## Verification

Passed:

- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_stop_gates.py -q`
- `/usr/bin/python3 -m py_compile trustgraph_legal/stop_gates.py trustgraph_legal/stopgate_types.py trustgraph_legal/stopgate_rules.py trustgraph_legal/check.py tests/unit/legal_ontology/test_stop_gates.py`
- happy QA: `/opt/homebrew/bin/python3 -m trustgraph_legal.check --case /Users/cosmos/dev/ontology/trustgraph/.omo/evidence/debt-collection-ontology/task-6-case-graph.json --out .omo/evidence/debt-collection-ontology/task-7-stopgates.json`
- happy QA result: `보류` with `amount_mismatch`, `discharge_proceeding_detected`, `exempt_claim_targeted`, and `limitation_risk`
- failure QA: temp graph with removed source span returned `보류` and included `invalid_fact_without_provenance`
- sensitive scan over changed code, tests, rule source, and generated evidence found no resident-id, phone, or account-like patterns
- post-write size check: changed Python files are below the 250 pure-LOC ceiling except the test file warning band at 237 pure LOC

Generated QA evidence:

- worktree-only generated file: `.omo/evidence/debt-collection-ontology/task-7-stopgates.json`
- this generated evidence is intentionally not staged for commit

## Commit

`dd7aeb46 feat(legal-check): add debt collection stop gate engine`
