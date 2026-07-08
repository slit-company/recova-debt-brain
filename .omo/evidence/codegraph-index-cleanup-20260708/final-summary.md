# CodeGraph Index Cleanup Final Summary

## Result

CodeGraph indexing is clean for `/Users/slit/dev/recova-debt-brain`.

## What Was Wrong

The root `.gitignore` had a broad `vertexai/` ignore rule. CodeGraph respects that ignore rule while scanning, so three tracked first-party provider files under `trustgraph-vertexai/trustgraph/model/text_completion/vertexai/` were skipped.

## What Changed

- `.gitignore` now keeps generic local `vertexai/` runtime folders ignored.
- `.gitignore` explicitly unignores `trustgraph-vertexai/trustgraph/model/text_completion/vertexai/` and its source files.
- `docs/ai-maintenance/codegraph.md` documents the rule so future maintenance does not accidentally re-break indexing.

## Verification

- Before fix: `SOURCE_COVERAGE_RED missing=3 extra=0 indexed_errors=0`.
- After fix: `SOURCE_COVERAGE_OK missing=0 extra=0 indexed_errors=0`.
- Forced reindex scanned and indexed 1,248 files.
- CodeGraph resolves the formerly missing `vertexai/llm.py` file with provider symbols.
- CodeGraph still resolves core debt-brain symbols including `evaluate_claim_domain_decision` and `evaluate_workflow_judgment`.
- `.codegraph` remains ignored through local git exclude and was not committed.

## Commits

- `4356b7c9 fix(codegraph): include vertexai provider sources`
- final evidence commit pending at the time this summary was written
