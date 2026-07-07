# R Debtor Docs Report

Member: R debtor-docs
Branch: `team/debtor-context-graph-v0-20260706/R`
Worktree: `worktrees/R`

## Deliverable

Added product/developer documentation:

- `docs/product/debt-collection-ontology/debtor-context-graph-v0.md`

The doc covers:

- DebtorContextGraph logical model over `DebtorGraphPayload`
- Document assembly and debtor context CLI usage
- additive MCP `debtor_graph` tools, including `assemble_debtor_documents` and `list_debtor_route_candidates`
- governance hooks and record kinds
- route status semantics
- redaction / no raw OCR policy
- task evidence paths
- known limitations and troubleshooting

The real OCR example uses `$RECOVA_REAL_OCR_ROOT` and `<redacted-real-ocr-root>` instead of a local absolute path. Synthetic fixture commands remain concrete and runnable.

## Evidence

Task-14 evidence files:

- `.omo/evidence/debtor-context-graph-v0/task-14-docs-smoke.txt`
- `.omo/evidence/debtor-context-graph-v0/task-14-docs-pii.txt`
- `.omo/evidence/debtor-context-graph-v0/task-14-document-assembly.json`
- `.omo/evidence/debtor-context-graph-v0/task-14-synthetic-from-assembly.json`
- `.omo/evidence/debtor-context-graph-v0/task-14-synthetic-full-graph.json`

Smoke results:

- Document assembly CLI: 5 document pages, 4 assemblies.
- Debtor context CLI from assembly: 18 route candidates.
- Debtor context CLI from OCR root: 18 route candidates.
- MCP debtor graph smoke: `list_debtor_route_candidates` returned 18 routes; `explain_debtor_route_candidate` for `bank_account_attachment` returned `possible`; `raw_text_included` and `source_text_included` were `False`.

Doc acceptance grep passed for:

- `DebtorContextGraph`
- `assemble_debtor_documents`
- `list_debtor_route_candidates`
- `raw_text_included`

PII/path scan:

- `task-14-docs-pii.txt` reports `SCAN: PASS` and `NO_FINDINGS`.
- Checked the doc and task-14 generated evidence for local absolute path prefixes, raw fixture marker text, resident-number shape, and phone-number shape.

## Scope Notes

- Did not edit MCP deployment runbooks.
- Did not add raw real OCR output.
- Did not use the local absolute real OCR corpus path in the doc or task-14 evidence.
- No production ontology, route, legal-source, deployment, or runtime files were edited.
