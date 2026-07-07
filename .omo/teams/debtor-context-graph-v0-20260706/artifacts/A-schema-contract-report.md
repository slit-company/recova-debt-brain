# A Schema Contract Report

Status: DONE

Member: A / schema-contract
Worktree: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debtor-context-graph-v0-20260706/worktrees/A`
Branch: `team/debtor-context-graph-v0-20260706/A`
Commit: `e58fd1fc feat(legal-graph): add debtor context graph schema`

## Scope

Implemented Todo 1 only.

Committed files:

- `trustgraph_legal/debtor_context_types.py`
- `tests/unit/legal_ontology/test_debtor_context_types.py`

Uncommitted task-1 evidence remains in:

- `.omo/evidence/debtor-context-graph-v0/task-1-red-pytest.txt`
- `.omo/evidence/debtor-context-graph-v0/task-1-green-pytest.txt`
- `.omo/evidence/debtor-context-graph-v0/task-1-schema-happy.json`
- `.omo/evidence/debtor-context-graph-v0/task-1-schema-failure.txt`
- `.omo/evidence/debtor-context-graph-v0/task-1-pii-scan.txt`

## Contract Added

- `SCHEMA_VERSION`: `recova-debtor-context-graph/v1`
- Shared versions: extractor, document assembly, ontology, route, legal rule-source
- Shared JSON aliases/helpers
- `DocumentPage`
- `DocumentAssembly`
- `ProcedureEpisode`
- `FactAssertion`
- `GraphSnapshot`
- `DebtorGraphPayload`
- `RouteCandidate`
- `FactAssertionSourceRefError`

PII/raw-text contract:

- `DebtorGraphPayload.to_json()["pii_profile"]["raw_text_included"]` is `false`.
- `DebtorGraphPayload.to_json()["pii_profile"]["source_text_included"]` is `false`.
- The schema types do not store or serialize raw OCR text.
- `FactAssertion` rejects empty source refs and placeholder source refs.

## Verification

- RED evidence captured before production module existed:
  - `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_debtor_context_types.py -q` failed with `ModuleNotFoundError: No module named 'trustgraph_legal.debtor_context_types'`.
- Focused pytest:
  - `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_debtor_context_types.py -q`
  - Result: 4 passed.
- Happy evidence:
  - Synthetic graph serialized to `.omo/evidence/debtor-context-graph-v0/task-1-schema-happy.json`.
  - `/opt/homebrew/bin/python3 -m json.tool .omo/evidence/debtor-context-graph-v0/task-1-schema-happy.json` passed.
- Failure evidence:
  - `.omo/evidence/debtor-context-graph-v0/task-1-schema-failure.txt` contains missing and placeholder source-ref validation errors.
- PII scan:
  - `.omo/evidence/debtor-context-graph-v0/task-1-pii-scan.txt`
  - Result: `NO_FINDINGS`.
- Syntax:
  - `/usr/bin/python3 --version`: Python 3.9.6.
  - `/usr/bin/python3 -m py_compile trustgraph_legal/debtor_context_types.py tests/unit/legal_ontology/test_debtor_context_types.py` passed.
- LSP:
  - `basedpyright` diagnostics on both changed Python files: no errors.
- Size gate:
  - `trustgraph_legal/debtor_context_types.py`: 249 pure LOC.
  - `tests/unit/legal_ontology/test_debtor_context_types.py`: 198 pure LOC.
- Git checks:
  - `git diff --check` passed before staging.
  - `git diff --cached --check` passed before commit.
  - `git diff --check HEAD~1 HEAD` passed after commit.

## Isolation

- Main checkout status for owned paths is clean:
  - `git -C /Users/cosmos/dev/ontology/trustgraph status --short -- tests/unit/legal_ontology/test_debtor_context_types.py trustgraph_legal/debtor_context_types.py`
  - Result: no output.
- A worktree status after commit:
  - branch `team/debtor-context-graph-v0-20260706/A`
  - only untracked task evidence remains under `.omo/evidence/debtor-context-graph-v0/`.
- No deployment files, MCP deployment docs, peer paths, real OCR data, or unrelated `.omo` evidence were changed or committed.
