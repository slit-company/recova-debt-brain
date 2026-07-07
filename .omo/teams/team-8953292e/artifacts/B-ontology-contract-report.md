# B ontology-contract report

Status: complete for Todo 2.

Scope honored:
- Added a new claim-centered ontology v1 resource.
- Added a dedicated validator for the v1 resource.
- Added focused tests for the validator happy path, missing Claim root failure, and missing required claim edge failure.
- Left `DebtorContextGraph` behavior untouched as the runtime memory root.
- Left v0 resources untouched and used them only as compatibility references.
- Did not edit Todo 1 or Todo 3 owned files.

Changed files:
- `resources/ontologies/recova-debt-collection-v1.json`
- `scripts/legal_ontology/validate_domain_ontology_v1.py`
- `tests/unit/legal_ontology/test_domain_ontology_v1.py`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-2-*`

Contract summary:
- Ontology key: `recova-debt-collection-v1`
- Root boundary: `Claim/Receivable`
- Runtime memory root preserved: `DebtorContextGraph`
- Required class count: 22
- Required claim edge count: 20
- Datatype property count: 11
- Non-execution semantics: `descriptive_only`

Verification commands:
- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_domain_ontology_v1.py -q --no-header --tb=short`
- `/opt/homebrew/bin/python3 -m json.tool resources/ontologies/recova-debt-collection-v1.json`
- `/opt/homebrew/bin/python3 scripts/legal_ontology/validate_domain_ontology_v1.py resources/ontologies/recova-debt-collection-v1.json`
- `jq '.[\"recova-debt-collection-v1\"].classes |= del(.claim)' resources/ontologies/recova-debt-collection-v1.json`
- `/opt/homebrew/bin/python3 -m py_compile scripts/legal_ontology/validate_domain_ontology_v1.py`
- `git diff --check`
- `rg` PII/path scan over changed Todo 2 files and evidence

Evidence paths:
- `.omo/evidence/debt-collection-domain-ontology-v1/task-2-isolation-proof.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-2-red-green-summary.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-2-focused-pytest.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-2-json-tool.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-2-ontology-validator.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-2-ontology-validator-failure.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-2-py-compile.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-2-diff-check.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-2-size-check.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-2-pii-scan.txt`

PII/path scan result: `NO_FINDINGS`.

Residual risks:
- This is a schema and validator contract only. Later todos still need to populate workflow, finance, route, source, action-packet, adapter, decision-engine, and MCP behavior against these IDs.
- The validator proves required classes, root labels, object-property domains/ranges, datatype ranges, and required edge IDs. It does not validate every optional alias or label text beyond the required root boundary.
- Commit hash is supplied in the final leader handoff after the Todo 2 commit is created.
