# Task 12 Debtor Governance Evidence

Status: DONE

## Scope

- Added service-side debtor governance records over existing debtor graph and route outputs.
- Preserved production ontology, route resources, legal-source resources, MCP adapters, and OCR artifacts as read-only.
- Kept the public API at `trustgraph_legal.debtor_governance.ManualFactReviewDecision` and `build_debtor_governance_payload`.

## Coverage

- Unknown assemblies.
- Unresolved identity.
- Conflicting fact signals.
- Draft, unretrieved, and future legal-source states.
- Blocked and review-required route candidates.
- Manual fact review decisions, including missing approval evidence rejection.

## Evidence

- `task-12-focused-pytest.txt`: focused unit tests, 3 passed.
- `task-12-python39-import.txt`: `/usr/bin/python3` import compatibility, import-ok.
- `task-12-python39-pycompile.txt`: `/usr/bin/python3 -m py_compile`, py_compile-ok.
- `task-12-basedpyright.txt`: changed-file type check, 0 errors.
- `task-12-size-gate.txt`: O production files under 250 pure LOC.
- `task-12-governance-happy.json`: graph-derived review records.
- `task-12-manual-rejection.json`: manual approval without evidence rejected service-side.
- `task-12-json-tool.txt`: JSON evidence validates.
- `task-12-pii-scan.txt`: NO_FINDINGS.
- `task-12-diff-check.txt`: `git diff --check` clean.
