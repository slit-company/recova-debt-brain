# AI Maintenance Guide

This repository is maintained with AI assistance. Start every non-trivial code
task by building context from the code graph and the current project notes
before editing files.

## Default Entry Routine

1. Check the worktree first: `git status -sb`.
2. Use codegraph before raw file reads for source-code understanding.
   - For architecture, flows, and broad questions, start with
     `codegraph_explore`.
   - For one symbol or one source file, use `codegraph_node`.
   - For blast-radius checks, use `codegraph_callers`.
   - Use `rg` only after codegraph when searching non-indexed files, docs,
     fixtures, or exact text.
3. Read the active project context:
   - `.omo/notes/recova-brain-working-log.md`
   - the relevant `.omo/plans/*.md`
   - the relevant `.omo/evidence/*/final-summary.md`
   - `.omo/start-work/ledger.jsonl` when team/work-plan state matters
4. Identify the smallest verification surface before editing.
5. Preserve unrelated worktree changes. Do not reset, checkout, or delete user
   work unless explicitly requested.

## Codegraph Setup

The repo has a local `.codegraph` symlink that points at the machine-local
codegraph project store. The codegraph database is local state and must not be
committed. See `docs/ai-maintenance/codegraph.md` for the current setup and
operating notes.

On this Mac, use `/Users/slit/.omo/codegraph/bin/codegraph` for local CLI
checks. Do not rely on a raw Node invocation of the Codegraph JavaScript entry;
the system Node version may trip Codegraph's runtime guard even when the
bundled wrapper works.

Current clean baseline, verified on 2026-07-08:

- Codegraph status: 1,248 files, 18,898 nodes, 51,660 edges.
- Supported tracked source parity: Python/YAML/JavaScript missing=0, extra=0,
  indexed_errors=0.
- The first-party
  `trustgraph-vertexai/trustgraph/model/text_completion/vertexai/` provider
  source must remain indexed despite the generic local `vertexai/` ignore rule.

When codegraph appears stale after edits, wait briefly for the watcher to catch
up and query again. If a tool reports that the project is not indexed in a new
environment, initialize/index codegraph locally there rather than committing
the database.

## Current Product Center

The collection brain is centered on workflow judgment: deciding the next
practical collection-work step from structured claim, evidence, legal, finance,
and route signals.

Core surfaces:

- `trustgraph_legal/workflow_judgments.py`
- `trustgraph_legal/domain_workflow_integration.py`
- `trustgraph_legal/domain_decisions.py`
- `trustgraph_legal/evidence_quality.py`
- `trustgraph_legal/finance_review_bridge.py`
- `trustgraph_legal/legal_workflow_checkpoints.py`
- `trustgraph_legal/mcp_claim_domain_handlers.py`
- `tests/fixtures/claim-domain-v1/synthetic_claim_states.json`
- `tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py`

Current documentation anchors:

- `docs/product/debt-collection-ontology/claim-domain-ontology-v1.md`
- `.omo/plans/debt-brain-structural-depth-v1.md`
- `.omo/evidence/debt-brain-structural-depth-v1/final-summary.md`
- `.omo/evidence/codegraph-index-cleanup-20260708/final-summary.md`

## Hard Guardrails

- Advisory-only semantics must remain explicit.
- Do not add debtor contact, court filing, seizure, payment demand, production
  ledger mutation, public admin/write tools, or remote deployment behavior
  unless the user explicitly asks for that separate scope.
- Do not output raw PII, OCR/source text, contact payloads, filing/court
  destinations, local paths, secrets, or authoritative collectable balances.
- Preserve the MCP tool registry order and the 25-tool count unless a task
  explicitly changes the public MCP contract.
- Product code must not branch on test scenario IDs or expected labels. It may
  consume generic structured support fields such as `evidence_checkpoint`,
  `finance_bridge`, and `legal_checkpoints`.

## Verification Defaults

System `python3` on this machine may not have the repo test dependencies. Use
`uv` for pytest/typecheck gates when needed.

Recommended focused gates for workflow/debt-brain work:

```bash
uv run --with pytest --with pydantic --with typing-extensions python -m pytest \
  tests/unit/legal_ontology/test_operator_playbook_v1.py \
  tests/unit/legal_ontology/test_workflow_judgments_v1.py \
  tests/unit/legal_ontology/test_evidence_quality_v1.py \
  tests/unit/legal_ontology/test_finance_claim_model_v1.py \
  tests/unit/legal_ontology/test_domain_decision_engine_v1.py \
  tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py -q
```

Recommended regression gates:

```bash
uv run --with pytest --with pydantic --with typing-extensions python -m pytest \
  tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py \
  tests/unit/legal_ontology/test_stop_gates_domain_v1.py \
  tests/unit/legal_ontology/test_route_decisions_v1.py \
  tests/unit/legal_ontology/test_action_packets_v1.py -q
```

For changed Python files, also run scoped compile, lint, and type checks:

```bash
python3 -m compileall <changed-python-files>
uv run --with ruff ruff check <changed-python-files>
uv run --with basedpyright --with pytest --with pydantic --with typing-extensions basedpyright <changed-python-files>
```
