# C Document Assembly Report

Status: DONE

Member: C / document-assembly
Worktree: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debtor-context-graph-v0-20260706/worktrees/C`
Branch: `team/debtor-context-graph-v0-20260706/C`

## Scope

Implemented Todo 2 only.

Files changed in the C worktree:

- `trustgraph_legal/document_assembly.py`
- `trustgraph_legal/document_assembly_pages.py`
- `tests/unit/legal_ontology/test_document_assembly.py`
- `.omo/evidence/debtor-context-graph-v0/task-2-*`

## Contract

- Public builder: `build_document_assembly(pages_dir, repo_root=None)`.
- Public CLI: `python -m trustgraph_legal.document_assembly --pages <dir> --repo-root <root> --out <json>`.
- Accepts a D-compatible folder under `tests/fixtures/legal-ocr-pages/`.
- If `<pages>/manifest.json` exists, it reads:
  - `pages[].document_id`
  - `pages[].canonical_document_type`
  - `pages[].relative_path`
  - `pages[].page_order`
  - optional `pages[].confidence`
  - optional `pages[].review_status`
- If no manifest exists, it scans `*.md` files in stable relative-path order and creates `unknown` / `needs_review` fallback assemblies grouped by first path segment.
- Output contains deterministic `DocumentPage` and `DocumentAssembly` DTOs from Todo 1.
- Output never includes raw OCR/source text.
- Page paths are resolved under the fixture root; `../outside.md` is rejected.

## D Fixture Handoff

D can land fixtures at `tests/fixtures/legal-ocr-pages/` with:

- `manifest.json`
- page markdown files referenced by `relative_path`
- stable `page_order` per `document_id`

C tests use temporary fixtures only and do not touch D-owned fixture/probe paths.

## Evidence

Task-2 evidence files are under:

- `.omo/evidence/debtor-context-graph-v0/task-2-red-pytest.txt`
- `.omo/evidence/debtor-context-graph-v0/task-2-green-pytest.txt`
- `.omo/evidence/debtor-context-graph-v0/task-2-document-assembly-happy.json`
- `.omo/evidence/debtor-context-graph-v0/task-2-document-assembly-cli.txt`
- `.omo/evidence/debtor-context-graph-v0/task-2-document-assembly-failure.txt`
- `.omo/evidence/debtor-context-graph-v0/task-2-json-tool.txt`
- `.omo/evidence/debtor-context-graph-v0/task-2-py-compile.txt`
- `.omo/evidence/debtor-context-graph-v0/task-2-basedpyright.txt`
- `.omo/evidence/debtor-context-graph-v0/task-2-pii-scan.txt`
- `.omo/evidence/debtor-context-graph-v0/task-2-diff-check.txt`

## Verification

- Focused pytest: `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_document_assembly.py -q` passed, 5 tests.
- Syntax: `/usr/bin/python3 -m py_compile trustgraph_legal/document_assembly.py trustgraph_legal/document_assembly_pages.py tests/unit/legal_ontology/test_document_assembly.py` passed.
- Type check: `basedpyright --level error trustgraph_legal/document_assembly.py trustgraph_legal/document_assembly_pages.py tests/unit/legal_ontology/test_document_assembly.py` passed with `0 errors, 0 warnings, 0 notes`.
- JSON evidence validation: `/opt/homebrew/bin/python3 -m json.tool .omo/evidence/debtor-context-graph-v0/task-2-document-assembly-happy.json` passed.
- PII scan: `.omo/evidence/debtor-context-graph-v0/task-2-pii-scan.txt` reports `NO_FINDINGS`.
- Diff hygiene: `git diff --check` passed.
- Size gate:
  - `trustgraph_legal/document_assembly.py`: 122 pure LOC.
  - `trustgraph_legal/document_assembly_pages.py`: 147 pure LOC.
  - `tests/unit/legal_ontology/test_document_assembly.py`: 181 pure LOC.

## Isolation

- Main checkout C-owned paths are absent/clean:
  - `tests/unit/legal_ontology/test_document_assembly.py`
  - `trustgraph_legal/document_assembly.py`
- C worktree contains only Todo 2 source/test/evidence changes.
