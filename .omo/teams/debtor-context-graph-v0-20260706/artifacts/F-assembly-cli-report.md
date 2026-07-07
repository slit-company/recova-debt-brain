# F assembly-cli report

Todo 5 is complete in worktree F.

## Delivered

- Added `--ocr-root`, `--manifest-tsv`, `--summary-only`, and `--limit` support for `python3 -m trustgraph_legal.document_assembly`.
- Preserved `--pages` compatibility.
- Added minimal TSV bridge for required columns: `document_id`, `canonical_document_type`, `relative_path`, `page_order`.
- Normalized document and assembly identifiers so prefixed IDs do not become `document:document:*` or `assembly:document:*`.
- Kept CLI output deterministic and redacted. Summary-only output excludes raw page arrays.
- Split CLI/TSV helpers into `trustgraph_legal/document_assembly_cli.py` to keep source modules below the local size target.

## Verification

- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_document_assembly.py -q`: 7 passed.
- `/usr/bin/python3 -m py_compile trustgraph_legal/document_assembly.py trustgraph_legal/document_assembly_cli.py tests/unit/legal_ontology/test_document_assembly.py`: passed.
- `basedpyright --level error trustgraph_legal/document_assembly.py trustgraph_legal/document_assembly_cli.py tests/unit/legal_ontology/test_document_assembly.py`: 0 errors, 0 warnings.
- Happy CLI evidence: `.omo/evidence/debtor-context-graph-v0/task-5-assembly-cli.json` with `schema_version=recova-document-assembly/v0`, `summary.pages=5`, `summary.assemblies=4`, and `pii_profile.raw_text_included=false`.
- Failure CLI evidence: `.omo/evidence/debtor-context-graph-v0/task-5-assembly-cli-failure.txt` from `--limit 0`, nonzero exit, controlled error.
- Sensitive-pattern scan over changed source, tests, and task-5 evidence: no findings.
- `git diff --check`: passed.

## Size Review

- `trustgraph_legal/document_assembly.py`: 182 lines, 152 pure LOC.
- `trustgraph_legal/document_assembly_cli.py`: 219 lines, 184 pure LOC.
- `tests/unit/legal_ontology/test_document_assembly.py`: 315 lines, 253 pure LOC.

The test file is slightly above the local pure LOC target because it already uses BDD-style comments and self-contained fixture helpers. Source modules are below the threshold after the split.

## Isolation

- Parent checkout stayed clean for F-owned source, test, and task-5 evidence paths.
- G remained paused and clean; no G edits were used.
