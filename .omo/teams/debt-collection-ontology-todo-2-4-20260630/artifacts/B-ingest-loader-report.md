# B ingest-loader report

Member: B `ingest-loader`
Branch: `team/debt-collection-ontology-todo-2-4-20260630/B`
Worktree: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debt-collection-ontology-todo-2-4-20260630/worktrees/B`
Commit: `3f417a2d10dd192c03f9458dfdad7b1235a18011`

## Delivered

- Added runnable dry-run CLI: `python3 -m trustgraph_legal.ingest`.
- Reads OCR markdown files from a zip in deterministic path order.
- Emits registry JSON with `document_id`, `source_hash`, redacted `source_path`, `source_path_ref`, OCR/extractor/ontology/prompt versions, review status, confidence, provenance, tags, PII profile, hybrid evidence keys, and `case_packet_id`.
- Uses hash-based duplicate detection inside one dry run; duplicate content emits `registry_status: duplicate`.
- Keeps raw OCR text out of stdout and evidence. PII-shaped values are redacted before any string field is emitted.
- Does not call live TrustGraph services; records the intended `service/text-load` provenance interface only.

## Isolation status outputs

Initial B worktree check before edits:

```text
$ git status --short --branch
## team/debt-collection-ontology-todo-2-4-20260630/B
```

After isolation correction, before continuing/committing:

```text
$ git -C /Users/cosmos/dev/ontology/trustgraph status --short
?? .omo/
```

```text
$ git -C /Users/cosmos/dev/ontology/trustgraph/.omo/teams/debt-collection-ontology-todo-2-4-20260630/worktrees/B status --short
?? tests/unit/legal_ontology/
?? trustgraph_legal/
```

Post-commit status:

```text
$ git -C /Users/cosmos/dev/ontology/trustgraph status --short
?? .omo/
```

```text
$ git status --short
```

## Verification outputs

```text
$ python3 -m trustgraph_legal.ingest --zip /Users/cosmos/dev/ocr/MinerU/work/legal_ocr_20260630/legal_docs_markdown.zip --dry-run --limit 5 --evidence /tmp/task-4-dry-run.json
{"dry_run": true, "duplicates": 0, "evidence": "/tmp/task-4-dry-run.json", "insert_candidates": 5, "records": 5}
```

```text
$ python3 - <<'PY'
import json
from pathlib import Path
payload = json.loads(Path('/tmp/task-4-dry-run.json').read_text(encoding='utf-8'))
records = payload['records']
required = {'document_id', 'source_hash', 'source_path', 'ocr_version', 'extractor_version', 'ontology_version', 'prompt_version', 'review_status', 'confidence', 'case_packet_id', 'provenance', 'tags'}
print(f"records={len(records)}")
print(f"summary={payload['summary']}")
print(f"missing_required={[sorted(required - set(record)) for record in records]}")
print(f"statuses={[record['registry_status'] for record in records]}")
print(f"raw_text_included={[record['pii_profile']['raw_text_included'] for record in records]}")
PY
records=5
summary={'records': 5, 'insert_candidates': 5, 'duplicates': 0}
missing_required=[[], [], [], [], []]
statuses=['dry_run_insert_candidate', 'dry_run_insert_candidate', 'dry_run_insert_candidate', 'dry_run_insert_candidate', 'dry_run_insert_candidate']
raw_text_included=[False, False, False, False, False]
```

```text
$ python3 -m pytest tests/unit/legal_ontology/test_ingest.py -q
============================= test session starts ==============================
platform darwin -- Python 3.14.5, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/cosmos/dev/ontology/trustgraph/.omo/teams/debt-collection-ontology-todo-2-4-20260630/worktrees/B/tests
configfile: pytest.ini
plugins: asyncio-1.3.0, anyio-4.13.0, xdist-3.8.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 2 items

tests/unit/legal_ontology/test_ingest.py ..                              [100%]

============================== 2 passed in 0.03s ===============================
```

```text
$ python3 -m py_compile trustgraph_legal/__init__.py trustgraph_legal/pii.py trustgraph_legal/registry.py trustgraph_legal/ingest.py tests/unit/legal_ontology/test_ingest.py
```

```text
$ rg -n "resident|주민등록번호|[0-9]{6}-[0-9]{7}" trustgraph_legal tests/unit/legal_ontology /tmp/task-4-dry-run.json || true
```

```text
$ rg -n "010-[0-9]{3,4}-[0-9]{4}|[0-9]{2,6}-[0-9]{2,6}-[0-9]{2,8}" trustgraph_legal tests/unit/legal_ontology /tmp/task-4-dry-run.json || true
```

```text
$ git diff --cached --check
```

```text
$ git diff --check HEAD~1 HEAD
```

```text
$ git commit -m "feat(legal-ingest): add OCR markdown registry loader"
[team/debt-collection-ontology-todo-2-4-20260630/B 3f417a2d] feat(legal-ingest): add OCR markdown registry loader
 5 files changed, 410 insertions(+)
 create mode 100644 tests/unit/legal_ontology/test_ingest.py
 create mode 100644 trustgraph_legal/__init__.py
 create mode 100644 trustgraph_legal/ingest.py
 create mode 100644 trustgraph_legal/pii.py
 create mode 100644 trustgraph_legal/registry.py
```

## Changed files

```text
$ git show --stat --oneline --no-renames HEAD
3f417a2d feat(legal-ingest): add OCR markdown registry loader
 tests/unit/legal_ontology/test_ingest.py |  72 ++++++++++
 trustgraph_legal/__init__.py             |   3 +
 trustgraph_legal/ingest.py               |  60 ++++++++
 trustgraph_legal/pii.py                  |  44 ++++++
 trustgraph_legal/registry.py             | 231 +++++++++++++++++++++++++++++++
 5 files changed, 410 insertions(+)
```

Pure LOC check:

```text
$ for f in trustgraph_legal/*.py tests/unit/legal_ontology/test_ingest.py; do printf "%s " "$f"; awk '!/^[[:space:]]*$/ && !/^[[:space:]]*(\/\/|#|--)/' "$f" | wc -l; done
trustgraph_legal/__init__.py        2
trustgraph_legal/ingest.py       52
trustgraph_legal/pii.py       36
trustgraph_legal/registry.py      189
tests/unit/legal_ontology/test_ingest.py       59
```
