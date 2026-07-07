# A Manual Inventory Report

Member: A manual-inventory
Team: team-8953292e
Branch: team/team-8953292e/A
Commit: b96e92f3

## Scope

Implemented Todo 1 only: a PII-safe v2 manual inventory and candidate extractor under `scripts/legal_ontology/`, focused tests, and task-1 evidence under `.omo/evidence/debt-collection-domain-ontology-v1/`.

The extractor reads the user-provided v2 manual locally and emits summary-only JSON. The report intentionally omits the local manual path and raw manual prose.

## Changed Files

- `scripts/legal_ontology/__init__.py`
- `scripts/legal_ontology/domain_manual_inventory.py`
- `scripts/legal_ontology/domain_manual_inventory_collectors.py`
- `scripts/legal_ontology/domain_manual_inventory_terms.py`
- `tests/unit/legal_ontology/test_domain_manual_inventory.py`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-1-basedpyright.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-1-cached-diff-check.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-1-diff-check.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-1-focused-pytest.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-1-isolation-proof.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-1-json-tool.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-1-loc-check.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-1-manual-inventory-failure.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-1-manual-inventory.json`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-1-pii-scan.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-1-py-compile.txt`

## Inventory Result

- headings: 115
- route candidates: 66
- workflow candidates: 12
- fact handles: 9
- risk/blocker candidates: 6
- legal-source candidates: 4
- finance candidates: 8
- scoring fields: 5
- action-packet candidates: 6

PII profile in the JSON keeps `raw_text_included=false`, `source_text_included=false`, `matched_text_included=false`, and `source_paths_included=false`.

## Verification

- `/opt/homebrew/bin/python3 scripts/legal_ontology/domain_manual_inventory.py --manual <local manual> --out .omo/evidence/debt-collection-domain-ontology-v1/task-1-manual-inventory.json`
- `/opt/homebrew/bin/python3 scripts/legal_ontology/domain_manual_inventory.py --manual .omo/evidence/debt-collection-domain-ontology-v1/nonexistent-manual.md --out .omo/evidence/debt-collection-domain-ontology-v1/task-1-should-not-exist.json`
- `basedpyright scripts/legal_ontology/domain_manual_inventory.py scripts/legal_ontology/domain_manual_inventory_collectors.py scripts/legal_ontology/domain_manual_inventory_terms.py tests/unit/legal_ontology/test_domain_manual_inventory.py`
- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_domain_manual_inventory.py -q`
- `/opt/homebrew/bin/python3 -m py_compile scripts/legal_ontology/__init__.py scripts/legal_ontology/domain_manual_inventory.py scripts/legal_ontology/domain_manual_inventory_collectors.py scripts/legal_ontology/domain_manual_inventory_terms.py tests/unit/legal_ontology/test_domain_manual_inventory.py`
- `/opt/homebrew/bin/python3 -m json.tool .omo/evidence/debt-collection-domain-ontology-v1/task-1-manual-inventory.json`
- `git diff --check`
- `git diff --cached --check`
- strict PII/path scan over changed Todo 1 files and evidence

## Evidence

- `.omo/evidence/debt-collection-domain-ontology-v1/task-1-manual-inventory.json`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-1-manual-inventory-failure.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-1-focused-pytest.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-1-json-tool.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-1-py-compile.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-1-basedpyright.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-1-pii-scan.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-1-diff-check.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-1-cached-diff-check.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-1-loc-check.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-1-isolation-proof.txt`

## PII Scan Result

PASS: no manual source paths, phone/RRN/account-like patterns, long identifiers, or forbidden raw-text keys found in the changed Todo 1 files and evidence scanned.

## Residual Risks

- Legal-source candidates are inventory signals only and still require Todo 3 legal-source curation/review.
- Candidate extraction is deterministic and heading/keyword based; downstream Todo 4-7 work should treat these as candidate IDs/signals, not authoritative route eligibility decisions.
- The manual itself remains a local input only and is not committed.
