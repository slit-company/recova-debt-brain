# C Legal Sources Report

Member: C `legal-sources`
Commit: `4b39b7a5 feat(legal-domain): curate domain legal sources v1`
Branch: `team/team-8953292e/C`

## Changed Files

- `.omo/evidence/debt-collection-domain-ontology-v1/task-3-*`
- `resources/legal_rules/debt_collection_domain_sources_v1.json`
- `scripts/legal_ontology/__init__.py`
- `scripts/legal_ontology/domain_sources_v1_common.py`
- `scripts/legal_ontology/validate_domain_sources_v1.py`
- `tests/unit/legal_ontology/test_domain_sources_v1.py`

## What Landed

- Added curated domain legal source v1 with 21 source records:
  - 18 article-level Korean-law records verified through MCP `get_law_text`.
  - 3 legacy/domain StopGate compatibility records marked `needs_legal_review` instead of pretending they are single statutory articles.
- Added deterministic validator CLI:
  - Validates v1 source metadata, evaluation/effective-date metadata, review/retrieval metadata, usage fields, route refs, workflow refs, and StopGate refs.
  - Does not call live Korean-law MCP.
- Added focused tests for validator happy path, unknown route source ref, and missing source metadata.

## Evidence

- Korean-law summary: `.omo/evidence/debt-collection-domain-ontology-v1/task-3-korean-law-source-map.json`
- Red-first pytest: `.omo/evidence/debt-collection-domain-ontology-v1/task-3-domain-sources-red-pytest.txt`
- Focused pytest: `.omo/evidence/debt-collection-domain-ontology-v1/task-3-domain-sources-pytest.txt`
- JSON parse: `.omo/evidence/debt-collection-domain-ontology-v1/task-3-json-tool.txt`
- Validator happy: `.omo/evidence/debt-collection-domain-ontology-v1/task-3-source-validator.txt`
- Validator failure: `.omo/evidence/debt-collection-domain-ontology-v1/task-3-source-validator-failure.txt`
- PII/path scan: `.omo/evidence/debt-collection-domain-ontology-v1/task-3-pii-path-scan.txt`
- py_compile: `.omo/evidence/debt-collection-domain-ontology-v1/task-3-py-compile.txt`
- basedpyright error-level check: `.omo/evidence/debt-collection-domain-ontology-v1/task-3-basedpyright-errors.txt`
- Size check: `.omo/evidence/debt-collection-domain-ontology-v1/task-3-size-check.txt`
- Diff check: `.omo/evidence/debt-collection-domain-ontology-v1/task-3-diff-check.txt`

## Commands

- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_domain_sources_v1.py -q` passed.
- `python3 -m json.tool resources/legal_rules/debt_collection_domain_sources_v1.json` passed.
- `python3 scripts/legal_ontology/validate_domain_sources_v1.py resources/legal_rules/debt_collection_domain_sources_v1.json resources/legal_routes/debt_collection_routes_v0.json resources/legal_rules/debt_collection_stopgate_v0.json` passed.
- Temp route copy with `missing-domain-source` failed as expected.
- `python3 -m py_compile scripts/legal_ontology/validate_domain_sources_v1.py scripts/legal_ontology/domain_sources_v1_common.py scripts/legal_ontology/__init__.py tests/unit/legal_ontology/test_domain_sources_v1.py` passed.
- `basedpyright --level error ...` reported `0 errors, 0 warnings, 0 notes`.
- PII/path scan reported `NO_FINDINGS`.
- `git diff --check`, `git diff --cached --check`, and `git diff --check HEAD~1 HEAD` passed.

## Korean-law Status

- Korean-law MCP tools were available.
- `search_law` exact-matched `민사집행법`, `민사소송법`, `민법`, and `채권의 공정한 추심에 관한 법률`.
- `search_law` returned API 404 for the two long law-title searches, so those were verified by direct existing `law_id`/`mst`/article lookup instead of guessed.
- Direct `get_law_text` verified all 18 article-level records used by v0 route legal/compliance refs.
- `legal_analysis verify_citations` was partial because grouped citations lost law-name context for repeated articles; this is recorded in evidence and not used as sole authority.

## Residual Risks

- The 3 legacy/domain bundle IDs are preserved for v0 StopGate compatibility and marked `needs_legal_review`; downstream v1 StopGate work should replace them with exact article-level refs where possible.
- This slice does not add route v1 or workflow v1 resources; it embeds workflow source refs only to make Todo 3 cross-reference validation deterministic.
- The resource is advisory-only and does not authorize filing, contact, payment demand, or execution.
