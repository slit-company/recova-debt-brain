# A Finance Review Hardening Report

Status: DONE
Member: A finance-review-hardening
Goal: G010-decision-stopgate-finance-and-review C001
Commit: `b7668289 test(legal-domain): harden finance review decisions`
Reviewer gate: UNCONDITIONAL APPROVAL

## Scope

Changed A-owned finance/domain behavior plus one discovered compatibility dependency on the same domain execution path:

- `trustgraph_legal/finance_claims.py`
- `trustgraph_legal/domain_decisions.py`
- `trustgraph_legal/route_decisions.py` (Python 3.9 compatibility-only import/dataclass decorator change reached by `domain_decisions.py`)
- `tests/unit/legal_ontology/test_finance_claim_model_v1.py`
- `tests/unit/legal_ontology/test_domain_decision_engine_v1.py`
- `.omo/evidence/debt-collection-knowledge-expansion-v1/task-4-finance-review-*`

No B-owned StopGate files, deployment/runbook files, client remote MCP docs, production storage, ledger mutation, filing, debtor contact, payment demand, seizure initiation, or execution behavior were changed.

## Behavior

- Unsupported payment allocation component names now return `needs_finance_review` instead of being silently ignored by fixture balance calculation.
- Disputed amounts with placeholder source refs preserve the disputed source ref and also emit `missing_source_ref`.
- Claim-domain decisions reject stale finance model resources as `stale_finance_model_version`, distinct from stale legal-source version.
- Manual finance review triggers keep route decisions `review_required`, preserve source refs, and keep action packet candidates advisory/non-executing.
- Local MCP order remains 25 tools with the claim-domain tail unchanged.

## Evidence

- RED proof: `.omo/evidence/debt-collection-knowledge-expansion-v1/task-4-finance-review-red-pytest.txt` (`3 failed, 8 passed`, intended failures)
- GREEN proof: `.omo/evidence/debt-collection-knowledge-expansion-v1/task-4-finance-review-green-pytest.txt` (`11 passed`)
- Regression: `.omo/evidence/debt-collection-knowledge-expansion-v1/task-4-finance-review-regression-pytest.txt` (`17 passed`)
- `/usr/bin/python3` version: `.omo/evidence/debt-collection-knowledge-expansion-v1/task-4-finance-review-python-version.txt`
- `/usr/bin/python3` compile: `.omo/evidence/debt-collection-knowledge-expansion-v1/task-4-finance-review-pycompile.txt`
- `/usr/bin/python3` import: `.omo/evidence/debt-collection-knowledge-expansion-v1/task-4-finance-review-python39-import.txt`
- Real-surface data proof: `.omo/evidence/debt-collection-knowledge-expansion-v1/task-4-finance-review-surface.json`
- MCP order proof: `.omo/evidence/debt-collection-knowledge-expansion-v1/task-4-finance-review-mcp-order.json`
- Pure LOC: `.omo/evidence/debt-collection-knowledge-expansion-v1/task-4-finance-review-pure-loc.txt`
- Diff check: `.omo/evidence/debt-collection-knowledge-expansion-v1/task-4-finance-review-diff-check.txt`
- LSP diagnostics: `.omo/evidence/debt-collection-knowledge-expansion-v1/task-4-finance-review-lsp.txt`
- PII/path scan: `.omo/evidence/debt-collection-knowledge-expansion-v1/task-4-finance-review-pii-path-scan.txt` (`NO_FINDINGS`)

## Notes

`/usr/bin/python3` finance/domain surface was proven without importing the broader MCP/governance stack. Importing `trustgraph_legal.mcp_domain` under `/usr/bin/python3` still reaches pre-existing 3.9-incompatible type aliases in governance modules outside this A slice; no MCP/governance files were edited. MCP order was verified with the repo's normal `python3`.

The member thread was still waiting on its internal reviewer after the verified gates completed. The leader performed a scoped rescue commit from the A worktree after rerunning the focused pytest, `/usr/bin/python3` py_compile, JSON evidence parsing, basedpyright error check, pure LOC check, diff check, and PII/path scan. Member C should treat commit `b7668289` as the review surface.

Reviewer returned unconditional approval with no blockers, including acceptance of RED->GREEN evidence, regression evidence, Python 3.9 finance/domain compatibility, LSP diagnostics, MCP order 25, pure LOC under 250, and unchanged B/deployment/runbook/client remote MCP scope.
