# M Domain Graph Adapter Report

Member: M / domain-graph-adapter
Thread: codex://threads/019f38a5-83f5-70d0-a553-4cfbc98fc572
Branch: `team/team-8953292e/M`
Commit: `8ddbe37e`

## Scope

Implemented Todo 10 only: a narrow DebtorContextGraph to claim-domain v1 compatibility adapter. No Todo 8 action-packet files, MCP tools, debtor identity merge logic, graph snapshot generation, or v0 route candidate generation were edited.

## Deliverables

- `trustgraph_legal/domain_graph_adapter.py`: public adapter surface and payload wrapper.
- `trustgraph_legal/domain_graph_adapter_shared.py`: JSON helpers and typed adapter error.
- `trustgraph_legal/domain_graph_adapter_handles.py`: claim, fact, route, governance, snapshot handle normalization.
- `trustgraph_legal/domain_graph_adapter_case_graph.py`: domain StopGate-compatible case graph projection.
- `tests/unit/legal_ontology/test_domain_graph_adapter_v1.py`: red/green coverage for happy mapping, v1 route/source projection, missing source refs, unsupported claim identity, and v0 graph preservation.
- `.omo/evidence/debt-collection-domain-ontology-v1/task-10-graph-adapter-happy.json`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-10-graph-adapter-failure.json`

## Contract Notes

- Adapter output includes `claim_root`, `source_bundle_hash`, `graph_snapshot_id`, `debtor_graph_id`, source refs, fact handles, route handles, governance handles, non-execution semantics, and PII profile.
- Existing v0 route candidates are preserved in the adapter payload by legacy route id. The domain case graph projection adds `domain_route_id` and v1 legal-source refs for v1-compatible downstream StopGate/domain use.
- Failure evidence covers both required failure modes: missing fact `source_ref` and unsupported explicit claim identity.

## Verification

- PASS: red test first failed on missing `trustgraph_legal.domain_graph_adapter`.
- PASS: `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_domain_graph_adapter_v1.py tests/unit/legal_ontology/test_debtor_context.py -q --no-header --no-summary`
- PASS: `basedpyright trustgraph_legal/domain_graph_adapter.py trustgraph_legal/domain_graph_adapter_shared.py trustgraph_legal/domain_graph_adapter_handles.py trustgraph_legal/domain_graph_adapter_case_graph.py tests/unit/legal_ontology/test_domain_graph_adapter_v1.py`
- PASS: `/opt/homebrew/bin/python3 -m py_compile ...`
- PASS: `git diff --check`
- PASS: JSON tool validation for happy/failure evidence.
- PASS: size gate, all changed Python files under 250 pure LOC.
- PASS: final PII/path scan returned `NO_FINDINGS`.
