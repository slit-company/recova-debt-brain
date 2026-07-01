# A Prompt Semantics Report - Todo 3

Member: A / prompt-semantics
Commit: `5cda329c fix(ontology): make extraction IDs source-safe`
Worktree: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debt-collection-ontology-todo-3-20260630/worktrees/A`
Branch: `team/debt-collection-ontology-todo-3-20260630/A`

## Result

Implemented Todo 3 in the A worktree only.

- Updated `ontology-prompt.md` so the canonical output example uses simplified JSONL `entity` / `relationship` / `attribute` objects, matching the active parser/converter contract.
- Replaced the old contradictory canonical food example (`Recipe`, `Ingredient`, `has_ingredient`) with legal examples using exact configured IDs such as `case-packet`, `legal-document`, `source-span`, `has-document`, `has-source-span`, and `source-ref`.
- Added explicit prompt guidance that bilingual labels/comments are explanatory only and must not be output identifiers unless they are exact configured IDs.
- Added legal source evidence instructions requiring `document_id`, `chunk_id`, and `source_refs` for legal facts, with instruction to omit unsupported legal facts.
- Added `tests/unit/test_extract/test_ontology/test_legal_prompt_semantics.py` covering rendered prompt semantics, simplified parser + converter output, and rejection of unconfigured legal values.

## Verification

Environment note: local editable installs failed because generated version modules such as `trustgraph.base_version` and `trustgraph.flow_version` are absent in this checkout. For verification only, I used an isolated venv under the team tmp directory plus a temporary composite source path outside the A git tree. No source files were edited for that setup.

Passed:

```text
PYTHONPATH=/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debt-collection-ontology-todo-3-20260630/tmp/A-todo3-src \
/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debt-collection-ontology-todo-3-20260630/tmp/A-todo3-venv/bin/python \
-m pytest tests/unit/test_extract/test_ontology/test_legal_prompt_semantics.py -q

3 passed
```

```text
PYTHONPATH=/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debt-collection-ontology-todo-3-20260630/tmp/A-todo3-src \
/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debt-collection-ontology-todo-3-20260630/tmp/A-todo3-venv/bin/python \
-m pytest \
  tests/unit/test_extract/test_ontology/test_legal_prompt_semantics.py \
  tests/unit/test_extract/test_ontology/test_prompt_and_extraction.py \
  tests/unit/test_extract/test_ontology/test_extract_with_simplified_format.py \
  tests/unit/test_extract/test_ontology/test_triple_converter_validation.py \
  -q

56 passed
```

```text
rg -n "resident|주민등록번호|[0-9]{6}-[0-9]{7}" ontology-prompt.md tests/unit/test_extract/test_ontology || true

no findings
```

```text
git diff --check
git diff --cached --check
git diff --check HEAD~1 HEAD

all passed
```

File size sanity:

```text
tests/unit/test_extract/test_ontology/test_legal_prompt_semantics.py: 178 pure LOC
ontology-prompt.md: 37 pure LOC
```

## Source Evidence Note

Todo 3 now makes legal source evidence mandatory in the rendered prompt contract and proves examples carry `document_id`, `chunk_id`, and `source_refs`. The current simplified parser/converter ignores those extra fields, so this slice does not claim source evidence persistence on emitted triples. Runtime graph provenance is still added downstream by the existing extractor; parser/converter-level source field persistence should be handled by a later scoped extraction/provenance task.

## Isolation Evidence

A worktree status after commit:

```text
## team/debt-collection-ontology-todo-3-20260630/A
```

Main checkout status after repair and commit:

```text
## master...origin/master [ahead 8]
?? .omo/
```

The main checkout has no prompt/test diff from A's work. The only main checkout status entry is the team `.omo/` directory.
