# G routes-v1 report

## Scope
- Member: G / routes-v1
- Todo: 6. Expand legal route catalog v1 from manual and curated sources
- Branch: `team/team-8953292e/G`

## Deliverables
- Added `resources/legal_routes/debt_collection_routes_v1.json`.
- Updated `scripts/legal_ontology/validate_routes.py` to validate routes against either the legacy v0 route-source file or `resources/legal_rules/debt_collection_domain_sources_v1.json`.
- Added `tests/unit/legal_ontology/test_routes_v1.py`.
- Generated task-6 evidence under `.omo/evidence/debt-collection-domain-ontology-v1/`.
- Commit: `d2c38554 feat(legal-routes): expand debt collection route catalog v1`.

## Contract
- Route catalog version: `recova-debt-collection-routes@v1.0.0`.
- Route count: 32, expanded beyond the v0 count of 18.
- Legal source file: `recova-debt-collection-domain-sources@v1.0.0`.
- Legal refs validated: 68 route legal refs plus compliance refs checked for existence.
- Route families covered: voluntary repayment, notarial deed, title acquisition, provisional remedy, financial assets, wage/income, lease/housing, business receivables, real estate, movable/business assets, insurance/refund/deposit, tax/refund/distribution/compensation, inheritance/family property, fraudulent transfer/hidden assets, special property rights, welfare/public-benefit exclusions, asset disclosure/inquiry/default registry, insolvency/recovery, and monitoring/retry.
- Every route keeps `direct_execution_allowed: false`, `no_direct_execution: true`, and `execution_semantics: none_advisory_only`.

## Verification
- `PASS /opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_routes_v1.py -q`
- `PASS /opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_validate_routes.py -q`
- `PASS /opt/homebrew/bin/python3 scripts/legal_ontology/validate_routes.py resources/legal_routes/debt_collection_routes_v1.json resources/legal_rules/debt_collection_domain_sources_v1.json`
- `PASS /opt/homebrew/bin/python3 -m json.tool resources/legal_routes/debt_collection_routes_v1.json`
- `PASS /usr/bin/python3 -m py_compile scripts/legal_ontology/validate_routes.py`
- `PASS LSP basedpyright diagnostics severity=error` for changed Python files.
- `PASS git diff --check`

## Evidence
- `.omo/evidence/debt-collection-domain-ontology-v1/task-6-route-validator.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-6-route-validator-failure.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-6-focused-pytest.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-6-json-tool.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-6-py-compile.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-6-lsp-diagnostics.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-6-size-check.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-6-diff-check.txt`
- `.omo/evidence/debt-collection-domain-ontology-v1/task-6-pii-path-scan.txt`

## Notes
- The validator preserves v0 compatibility by making fact-handle validation active only when a route resource declares `fact_handle_catalog`.
- Evidence files avoid raw manual prose, personal identifiers, and local absolute paths.
