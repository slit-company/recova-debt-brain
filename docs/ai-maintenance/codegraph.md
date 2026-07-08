# Codegraph Maintenance Notes

Codegraph should be the first source-code context layer for this repository.
It lets future AI sessions inspect symbols, call paths, and blast radius
without repeatedly rebuilding the same map from raw file reads.

## Current Local Status

- Local entry: `.codegraph`
- Current shape: `.codegraph` is a symlink into the machine-local codegraph
  project store.
- Current target on this Mac:
  `/Users/slit/.omo/codegraph/projects/recova-debt-brain-ebc6d01c9c699178`
- Git status: `.codegraph` is intentionally ignored by `.git/info/exclude`.
- Database policy: do not commit codegraph databases, WAL files, daemon logs,
  or project-store contents.
- CLI note: the `codegraph` shell command may not be on `PATH` in this desktop
  environment. Use the Codex codegraph MCP tools when available.

Verified on 2026-07-08:

- The repo is indexed through the local `.codegraph` entry.
- A codegraph exploration of the workflow path found the current
  `domain_workflow_integration -> evaluate_workflow_judgment` flow.
- The indexed source included the generic structured support fields
  `evidence_checkpoint`, `finance_bridge`, and `legal_checkpoints`.

## How AI Sessions Should Use It

Use this sequence before touching code:

1. Ask codegraph for the relevant area.
   - Broad flow or architecture: `codegraph_explore`.
   - Specific source file: `codegraph_node(file=...)`.
   - Specific function/class: `codegraph_node(symbol=..., includeCode=true)`.
   - Blast radius: `codegraph_callers`.
2. Read `.omo` project context for the why:
   - working log
   - active plan
   - final evidence for the current workstream
3. Only then patch code or tests.
4. After edits, wait briefly for the watcher and query codegraph again if the
   next decision depends on changed symbols.

Avoid this pattern:

- Grepping first for a symbol that codegraph can resolve.
- Reading many source files one by one when one `codegraph_explore` call can
  show the grouped flow.
- Treating `.codegraph` contents as project artifacts.

## Current Workflow-Judgment Map

Start with these symbols/files for debt-brain workflow work:

- `trustgraph_legal/domain_workflow_integration.py`
  - `build_domain_workflow_output`
  - `DomainWorkflowRequest`
  - `DomainWorkflowOutput`
- `trustgraph_legal/workflow_judgments.py`
  - `WorkflowJudgmentRequest`
  - `evaluate_workflow_judgment`
- `trustgraph_legal/domain_decisions.py`
  - `evaluate_claim_domain_decision`
- `trustgraph_legal/evidence_quality.py`
  - `evaluate_evidence_quality`
- `trustgraph_legal/finance_review_bridge.py`
  - finance review-code to workflow-signal bridge
- `trustgraph_legal/legal_workflow_checkpoints.py`
  - legal StopGate to workflow-checkpoint adapter
- `trustgraph_legal/mcp_claim_domain_handlers.py`
  - MCP forwarding surface for claim-domain tools

For scenario coverage and real-boundary behavior:

- `tests/fixtures/claim-domain-v1/synthetic_claim_states.json`
- `tests/utils/claim_domain_pipeline_support.py`
- `tests/utils/workflow_scenario_expectations.py`
- `tests/unit/legal_ontology/workflow_scenario_requests.py`
- `tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py`

## If Codegraph Is Missing Or Stale

If `.codegraph` is missing in another checkout, initialize or attach codegraph
locally in that environment. Do not copy or commit the database from this
machine.

If a query looks stale:

1. Wait a moment for the file watcher.
2. Query the changed symbol/file again.
3. If the tool explicitly reports no index, fall back to normal repo inspection
   for that turn and record that the local codegraph setup needs repair.

## Maintenance Goal

The target is not just faster search. The target is continuity: future AI
sessions should quickly recover what the collection brain does, where the
workflow decision lives, what depends on it, and which guardrails must not be
broken.
