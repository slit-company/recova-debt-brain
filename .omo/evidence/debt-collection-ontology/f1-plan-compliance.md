# F1 Plan Compliance Audit

Date: 2026-06-30

## Result

APPROVE.

All 10 implementation todos in `.omo/plans/debt-collection-ontology.md` are complete in the working plan and implemented on `master`.

## Must Have Coverage

| Requirement | Evidence |
| --- | --- |
| v0 domain contract | `docs/product/debt-collection-ontology/domain-contract.md` |
| TrustGraph ontology config | `resources/ontologies/recova-debt-collection.json` |
| OCR markdown ingest lane | `trustgraph_legal/ingest.py`, `load_registry_records_to_trustgraph`, `scripts/legal_ontology/check_fixture_manifest.py`, task 4 evidence |
| document registry metadata | `trustgraph_legal/registry.py`, task 4 dry-run evidence, `tests/unit/legal_ontology/test_ingest.py` text-load lane coverage |
| classifier and field extraction | `trustgraph_legal/classifier.py`, `trustgraph_legal/classifier_types.py`, `trustgraph_legal/classifier_rules.py`, `trustgraph_legal/classifier_manifest.py`, `trustgraph_legal/fields.py`, task 5 evidence |
| hybrid case graph | `trustgraph_legal/case_graph.py`, task 6 graph evidence |
| deterministic StopGate engine | `trustgraph_legal/stop_gates.py`, `resources/legal_rules/debt_collection_stopgate_v0.json`, task 7 evidence |
| ontology governance workflow | `trustgraph_legal/governance*.py`, task 8 evidence |
| single agent-agnostic MCP domain tools | `trustgraph_legal/mcp_domain.py`, `trustgraph_legal/mcp_handlers.py`, `trustgraph_legal/mcp_envelope.py`, `trustgraph_legal/mcp_inputs.py`, `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py`, `trustgraph-mcp/trustgraph/mcp_server/auth.py`, task 9 evidence |
| MCP server contract and eval runbook | `docs/product/debt-collection-ontology/mcp-domain-server-contract.md`, `scripts/legal_ontology/evaluate_packet.py`, task 10 evidence |

## Must Not Coverage

| Boundary | Evidence |
| --- | --- |
| no final legal advice or execution | `recommend_next_action` returns preconditions and `no_direct_filing_contact_or_collection`; direct execution probe returns `unknown_tool` |
| no raw sensitive output by default | task 9/task 10 scans and final changed-file sensitive-shape scan returned no findings |
| no client native memory as source of truth | MCP contract document includes memory-conflict policy |
| no Hermes-specific runtime dependency | MCP contract is generic and agent-agnostic |
| no multiple physical MCP services | tools register into existing `trustgraph-mcp` FastMCP server |
| no name-only case merge | case graph identity model uses `case_packet_id` plus hybrid evidence keys |
| no unreviewed live statute updates | curated v0 rule source and governance promotion workflow |
| no provenance bypass | registry records include `service/text-load` provenance, case graph and StopGate evidence include source refs |

## Commands

- `test -f` checks for core files: passed.
- `python3 scripts/legal_ontology/evaluate_packet.py --fixtures tests/fixtures/legal-ocr/manifest.json --out .omo/evidence/debt-collection-ontology/task-10-eval.json`: passed.
- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology -q`: 39 passed.
- `/opt/homebrew/bin/python3 -m pytest tests/integration/legal_ontology/test_mcp_tools.py -q`: 3 passed.
- Actual MCP gateway-backed HTTP smoke with temporary venv and streamable HTTP client: passed; bad token rejected, gateway `whoami` identity validation succeeded, public WebSocket `iam/authorise-many` was not used, the internal scope-authorizer seam made debt-tool decisions, reader token was rejected for governance scope, debt tool listed, token not echoed.
