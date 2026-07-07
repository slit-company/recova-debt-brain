# B StopGate Safety Hardening Report

## Status

- Member: B `stopgate-safety-hardening`
- Branch: `team/team-2f31dc5f/B`
- ULW: `G010-decision-stopgate-finance-and-review`, criterion C002
- Commit: `9c3c046ae02248d8a12b61a01ee77b7b0c78c61a`
- Reviewer verdict: approved after round 2 recheck

## Summary

Hardened domain-v1 StopGate service/finality/execution-clause proof parsing so negated values such as `not granted`, `not served`, and `not final` remain conservative and hold the case at `보류`, while existing positive proof vocabulary such as `grant`, `service`, and `final` still clears. Added focused route-decision regressions proving protected-property, insolvency, service-finality, and execution-clause blocker fact handles produce `blocked` decisions with human-review-only, advisory action candidates.

## Changed Paths

- `trustgraph_legal/stop_gates_domain_v1.py`
- `trustgraph_legal/stopgate_proof_text.py`
- `tests/unit/legal_ontology/test_stop_gates_domain_v1.py`
- `tests/unit/legal_ontology/test_domain_decision_engine_v1.py`
- `.omo/evidence/debt-collection-knowledge-expansion-v1/task-4-stopgate-domain-*`

No deployment/runbook/client remote MCP docs changed. `trustgraph_legal/domain_decisions.py` and A-owned `trustgraph_legal/finance_claims.py` were not edited.

## Evidence

- RED: `.omo/evidence/debt-collection-knowledge-expansion-v1/task-4-stopgate-domain-red.txt`
- GREEN: `.omo/evidence/debt-collection-knowledge-expansion-v1/task-4-stopgate-domain-green.txt`
- Python 3.9 compile: `.omo/evidence/debt-collection-knowledge-expansion-v1/task-4-stopgate-domain-py39-compile.txt`
- MCP/order regression: `.omo/evidence/debt-collection-knowledge-expansion-v1/task-4-stopgate-domain-mcp-regression.txt`
- Real-surface probe: `.omo/evidence/debt-collection-knowledge-expansion-v1/task-4-stopgate-domain-real-surface.json`
- PII/path scan: `.omo/evidence/debt-collection-knowledge-expansion-v1/task-4-stopgate-domain-pii-path-scan.txt`
- Reviewer approval: `.omo/evidence/debt-collection-knowledge-expansion-v1/task-4-stopgate-domain-review.txt`
- Running notepad: `.omo/evidence/debt-collection-knowledge-expansion-v1/task-4-stopgate-domain-notepad.md`

## Verification Results

- `python3 -m pytest tests/unit/legal_ontology/test_stop_gates_domain_v1.py tests/unit/legal_ontology/test_domain_decision_engine_v1.py -q`: RED first, then GREEN with 13 passed.
- `/usr/bin/python3 -m py_compile trustgraph_legal/stop_gates_domain_v1.py trustgraph_legal/stopgate_proof_text.py`: exit 0.
- `python3 -m pytest tests/unit/legal_ontology/test_mcp_domain_tools.py tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py tests/integration/legal_ontology/test_mcp_tools.py -q`: 13 passed.
- Real-surface probe: `tool_count` 25, claim-domain tail unchanged, negated StopGate decision `보류`, positive `grant/service/final` StopGate decision `가능`, protected-property and insolvency route decisions `blocked`, no filing/contact payloads, `direct_execution_allowed` false.
- LSP diagnostics: no error diagnostics for touched Python files.
- Pure LOC: touched production file remains 250; new helper 19.
- PII/path: context-aware scan found no blockers.

## Reviewer Notes

- Round 1 read-only reviewer rejected the first implementation because it weakened positive proof vocabulary (`grant`, `service`).
- The fix restored those positive spellings, updated the clear-case regression to cover them directly, and reran all gates.
- Round 2 read-only reviewer approved the fixed surface with no remaining blockers.
