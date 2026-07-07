# S final eval pack report

Member: S `final-eval-pack`
Thread: `codex://threads/019f36ec-8b52-7430-a61c-0ac57c722c09`
Status: committed

## Final evidence

- Evidence directory: `.omo/evidence/debtor-context-graph-v0/`
- Real OCR summary pages: 208
- Real OCR assemblies: 1
- Route candidates: 18
- Review items: 1
- Unknown assemblies: 1
- MCP tool count: 21
- Existing 16 first: True
- Debtor graph tools appended: True
- Outside-root path probe: path_outside_repo_root

## Verification

- Focused pytest: `51 passed`
- JSON validation: see `final-json-tool.txt`.
- PII/path scan: `NO_FINDINGS`; no matched source lines, no absolute real OCR root, no local absolute user-home paths.
- Py compile: see `final-py-compile.txt`.
- Diff check: see `final-diff-check.txt`.
- Dirty scope: see `final-dirty-scope.txt`.

## Scope

- Summary-only final evidence.
- No raw OCR text, matched OCR snippets, real OCR source paths, personal identifiers, or secrets.
- No deployment or runbook files touched.
- Commit hash: `29de4441`.
