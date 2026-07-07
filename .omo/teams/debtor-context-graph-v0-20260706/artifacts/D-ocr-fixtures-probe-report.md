# Member D - OCR Fixtures Probe Report

## Scope

Member D stayed within fixture/probe ownership:

- `tests/fixtures/legal-ocr-pages/`
- `scripts/legal_ontology/summarize_ocr_corpus.py`
- `tests/unit/legal_ontology/test_ocr_corpus_probe.py`
- `.omo/evidence/debtor-context-graph-v0/task-3-*`

No edits were made to `trustgraph_legal/document_assembly.py` or `tests/unit/legal_ontology/test_document_assembly.py`.

## Isolation Evidence

Before tests and commit, the parent checkout was rechecked:

- Parent top-level: `/Users/cosmos/dev/ontology/trustgraph`
- Parent branch: `master`
- `git status --short -- scripts/legal_ontology/summarize_ocr_corpus.py tests/fixtures/legal-ocr-pages tests/unit/legal_ontology/test_ocr_corpus_probe.py` returned no entries.
- All three D paths were missing from the parent checkout.
- `git ls-files -o --exclude-standard -- ...` returned no entries for the D paths.

The D worktree was rechecked:

- D top-level: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debtor-context-graph-v0-20260706/worktrees/D`
- D branch: `team/debtor-context-graph-v0-20260706/D`
- The three D-owned paths exist only in D pending commit.

## Fixture Contract

Added `tests/fixtures/legal-ocr-pages/manifest.json` and five synthetic page markdown files:

- `pages/payment_order_001.md`
- `pages/payment_order_002.md`
- `pages/service_finality_001.md`
- `pages/unknown_review_001.md`
- `pages/attachment_order_001.md`

The manifest provides:

- deterministic page order
- C-compatible per-page `document_id`
- C-compatible per-page `canonical_document_type`
- expected assembly IDs and document types
- SHA-256 source hashes
- line and character counts
- keyword signal counts
- optional confidence values
- redaction/PII policy metadata

The fixture intentionally includes an unknown review page so C's assembly builder can retain uncertain pages instead of dropping them.

## Real Corpus Probe

Added `scripts/legal_ontology/summarize_ocr_corpus.py`, an aggregate-only helper for `/Users/cosmos/dev/ocr/MinerU/work/legal_ocr_20260630`.

The helper emits:

- page count and available page count
- total/min/max/average character counts
- total line count
- aggregate keyword-signal page counts
- aggregate possible sensitive-pattern counts
- corpus fingerprint based only on page sizes and line counts

The helper does not emit raw OCR text, matched text, source file names, or source paths.

Real corpus evidence:

- `.omo/evidence/debtor-context-graph-v0/task-3-real-ocr-assembly-summary.json`
- pages: 208
- lines: 5,393
- chars: 350,586
- `raw_text_included=false`
- `matched_text_included=false`
- `source_paths_included=false`

## Verification

Commands run from D worktree:

```bash
/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_ocr_corpus_probe.py -q
/opt/homebrew/bin/python3 -m json.tool tests/fixtures/legal-ocr-pages/manifest.json
/opt/homebrew/bin/python3 -m py_compile scripts/legal_ontology/summarize_ocr_corpus.py tests/unit/legal_ontology/test_ocr_corpus_probe.py
basedpyright scripts/legal_ontology/summarize_ocr_corpus.py tests/unit/legal_ontology/test_ocr_corpus_probe.py
/opt/homebrew/bin/python3 scripts/legal_ontology/summarize_ocr_corpus.py --ocr-root tests/fixtures/legal-ocr-pages --out .omo/evidence/debtor-context-graph-v0/task-3-fixture-ocr-pages-summary.json
/opt/homebrew/bin/python3 scripts/legal_ontology/summarize_ocr_corpus.py --ocr-root /Users/cosmos/dev/ocr/MinerU/work/legal_ocr_20260630 --out .omo/evidence/debtor-context-graph-v0/task-3-real-ocr-assembly-summary.json
/opt/homebrew/bin/python3 -m json.tool .omo/evidence/debtor-context-graph-v0/task-3-real-ocr-assembly-summary.json
```

Results:

- focused pytest: 3 passed
- py_compile: passed
- basedpyright: 0 errors, 0 warnings
- fixture manifest JSON: valid
- fixture summary JSON: valid
- real OCR summary JSON: valid
- PII scan evidence: `.omo/evidence/debtor-context-graph-v0/task-3-pii-scan.txt` contains `NO_FINDINGS`
- pure LOC: `scripts/legal_ontology/summarize_ocr_corpus.py` is 217, under the 250 defect threshold but in the warning band; split CLI parsing out first if this file grows.

## Handoff Notes For C

C can consume `tests/fixtures/legal-ocr-pages/manifest.json` as optional metadata beside the page files. Each page now carries `document_id`, `canonical_document_type`, `relative_path`, `page_order`, optional `confidence`, and `review_status`, matching C's committed contract from `310eff3b`. The fixture shape is intentionally plain: markdown page files plus a manifest with expected page grouping and redacted source refs. D did not assert against C's assembly implementation.
