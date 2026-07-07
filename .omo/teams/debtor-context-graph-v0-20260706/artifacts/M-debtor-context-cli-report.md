# M debtor-context-cli report

## Scope

Implemented Todo 10 in the M worktree only.

- `trustgraph_legal/debtor_context.py`
- `trustgraph_legal/debtor_context_cli.py`
- `tests/integration/legal_ontology/test_debtor_context_pipeline.py`
- `.omo/evidence/debtor-context-graph-v0/task-10-*`

Commit: `36633df6` (`feat(legal-graph): add debtor context CLI`)

M was synced with latest master after K compatibility merge `0fc37242`.

## Behavior

- `python3 -m trustgraph_legal.debtor_context` now accepts `--ocr-root` or `--assembly`, `--out`, `--route-resources`, `--legal-sources`, `--summary-only`, and `--limit`.
- CLI writes either a full redacted debtor context graph or a summary-only aggregate payload.
- Full graph path builds from full `DocumentAssembly` JSON, attaches route candidates from caller-selected route/legal-source resources, and updates graph snapshot route ids.
- OCR-root path builds via the existing DocumentAssembly materialization, supports bounded `--limit`, and writes no raw OCR text.
- Summary output includes aggregate counts, route status counts, replay snapshot id, provenance validation status, unknown assemblies, and review item count.
- Controlled input/resource errors return exit code 2 and do not write partial output.

## Verification

- Synced master proof: `/usr/bin/python3 -c 'import trustgraph_legal.route_candidates; print("import-ok")'` -> `import-ok`
- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_debtor_context.py tests/integration/legal_ontology/test_debtor_context_pipeline.py -q` -> 7 passed
- `/Users/cosmos/.local/bin/basedpyright --level error trustgraph_legal/debtor_context.py trustgraph_legal/debtor_context_cli.py tests/integration/legal_ontology/test_debtor_context_pipeline.py` -> 0 errors
- `/opt/homebrew/bin/python3 -m py_compile trustgraph_legal/debtor_context.py trustgraph_legal/debtor_context_cli.py tests/integration/legal_ontology/test_debtor_context_pipeline.py` -> passed
- `python3 -m json.tool` over task-10 JSON evidence -> passed
- `git diff --check` -> passed
- PII/sensitive-pattern scan over changed source/tests/evidence -> `NO_FINDINGS`

## Evidence

- `.omo/evidence/debtor-context-graph-v0/task-10-synthetic-full-graph.json`
- `.omo/evidence/debtor-context-graph-v0/task-10-real-ocr-debtor-summary.json`
- `.omo/evidence/debtor-context-graph-v0/task-10-unknown-only.json`
- `.omo/evidence/debtor-context-graph-v0/task-10-focused-pytest.txt`
- `.omo/evidence/debtor-context-graph-v0/task-10-basedpyright.txt`
- `.omo/evidence/debtor-context-graph-v0/task-10-py-compile.txt`
- `.omo/evidence/debtor-context-graph-v0/task-10-json-tool.txt`
- `.omo/evidence/debtor-context-graph-v0/task-10-diff-check.txt`
- `.omo/evidence/debtor-context-graph-v0/task-10-pii-scan.txt`

## Output summaries

- Synthetic full graph: 5 pages, 4 assemblies, 12 facts, 18 route candidates, 2 possible routes, 0 provenance issues.
- Real OCR summary-only: 208 pages, 1 aggregate unknown assembly, 18 route candidates, all `missing_facts`, 1 review item, no raw/source text.
- Unknown-only summary: 1 page, 1 unknown assembly, 18 route candidates, all `missing_facts`, 1 review item, no raw/source text.

## Notes

- `trustgraph_legal/debtor_context_cli.py` is 244 pure LOC: under the hard 250 ceiling, but in the warning band. Future CLI expansion should split parsing/output helpers before adding behavior.
- No MCP files, governance files, route resources, deployment docs, or K-owned route code were edited by M.
