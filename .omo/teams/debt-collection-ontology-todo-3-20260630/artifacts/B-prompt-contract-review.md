# B Prompt Contract Review - Todo 3

Member: B / prompt-contract-review
Scope: read-only acceptance review for Todo 3 prompt semantics
Date: 2026-06-30

## Executive Result

Pre-implementation review. A's branch currently has no diff over `master`, so this report records the acceptance contract and risk checks A should satisfy before integration.

Current state is not acceptable for Todo 3:

- `ontology-prompt.md` lists configured ontology keys, but its example output uses generic food IDs such as `Recipe`, `Ingredient`, and `has_ingredient`.
- Runtime extraction now uses the simplified JSONL entity / relationship / attribute path, not the older triple-array path. Acceptance must test `extract_with_simplified_format` and `TripleConverter`, not only the legacy triple parser.
- Legal source evidence is required by the domain contract, but the current simplified parser/converter model has no per-item `source_refs`, `document_id`, or `chunk_id` fields. The runtime adds graph provenance from the chunk metadata after conversion, which is useful but not the same as prompt-level legal evidence fields.

## Status Outputs

B worktree status, captured before artifact writing:

```text
## team/debt-collection-ontology-todo-3-20260630/B
```

Main checkout status:

```text
## master...origin/master [ahead 8]
?? .omo/
```

A branch read-only status:

```text
## team/debt-collection-ontology-todo-3-20260630/A
```

A branch diff against `master`: no commits, no changed files.

## Todo 3 Contract

Todo 3 should enforce four things for `recova-debt-collection`:

1. Exact configured IDs
   - For classes, output must use ontology keys such as `case-packet`, `legal-document`, `source-span`, `claim`, `enforcement-title`, `stopgate`, or the corresponding full URI.
   - For object properties, output must use keys such as `has-document`, `has-source-span`, `has-legal-check`.
   - For datatype properties, output must use keys such as `document-id`, `source-ref`, `prompt-version`.
   - Labels like `Case packet`, `Legal document`, or Korean labels are explanatory only. They must not be accepted as `entity_type`, `subject_type`, `object_type`, `relation`, or `attribute` values unless they are also exact configured keys.

2. Prompt examples match the actual runtime format
   - `extract.py` calls prompt id `extract-with-ontologies` and reads `PromptResult.objects`.
   - The expected output shape is JSONL-style objects with `type: entity`, `type: relationship`, or `type: attribute`.
   - A triple-array example with `subject` / `predicate` / `object` is a regression risk unless the prompt config really still uses that legacy contract.

3. Legal source evidence is explicit
   - Prompt instructions must require source evidence for legal facts: document pointer, chunk pointer, and a redacted span or source reference.
   - The post-conversion graph provenance from `extract.py` is not enough to prove the LLM grounded each extracted legal fact. If Todo 3 only changes prompt text, the report should state that source evidence is prompt-level only until parser/converter support lands.

4. Unconfigured predicates are rejected
   - Unknown relationships must produce no relationship triple.
   - Unknown attributes must produce no attribute triple.
   - Unknown entity types must produce no entity triples.
   - Domain/range violations must continue to produce no triple.

## Current Evidence

- Todo 3 asks for exact legal IDs, explanatory labels, and document/chunk evidence: `.omo/plans/debt-collection-ontology.md:102-107`.
- Current prompt renders ontology keys but gives contradicting example IDs: `ontology-prompt.md:3-19` and `ontology-prompt.md:44-52`.
- Runtime path is simplified extraction: `trustgraph-flow/trustgraph/extract/kg/ontology/extract.py:341-443`.
- Prompt variables are currently only `text`, `classes`, `object_properties`, and `datatype_properties`: `trustgraph-flow/trustgraph/extract/kg/ontology/extract.py:449-464`.
- Converter rejects unknown or invalid ontology IDs by returning no triple: `trustgraph-flow/trustgraph/extract/kg/ontology/triple_converter.py:101-105`, `:145-149`, `:196-200`, `:158-172`, `:208-214`.
- Current prompt tests use a generic food ontology fixture and accept unprefixed generic IDs: `tests/unit/test_extract/test_ontology/test_prompt_and_extraction.py:27-92`.
- Existing simplified runtime test protects `.objects` handling but still uses generic food IDs: `tests/unit/test_extract/test_ontology/test_extract_with_simplified_format.py:95-130`.
- Domain contract requires document metadata and `source_refs`: `docs/product/debt-collection-ontology/domain-contract.md:121-135`.
- Domain contract requires source spans / provenance for material fact categories: `docs/product/debt-collection-ontology/domain-contract.md:168-183`.

## Recommended Acceptance Checks

PASS only if all of these hold:

1. Prompt rendering check
   - Render the `extract-with-ontologies` prompt with a small `recova-debt-collection` subset.
   - Assert the prompt includes legal IDs like `case-packet`, `legal-document`, `has-document`, `source-ref`.
   - Assert the prompt shows labels as explanatory text only.
   - Assert examples do not contain generic machine IDs from the old food example.
   - Assert examples use the same simplified JSONL object shape consumed by runtime.

2. Runtime extraction check
   - Mock `PromptResult(response_type="jsonl", objects=[...])` with legal IDs.
   - Assert `extract_with_simplified_format` returns triples using `https://recova.ai/ontologies/debt-collection#...` URIs.
   - Include one entity, one relationship, and one attribute.

3. Rejection check
   - Feed a relationship with an unconfigured `relation`.
   - Feed an attribute with an unconfigured `attribute`.
   - Feed an entity with an unconfigured `entity_type`.
   - Assert those inputs create no triples, while neighboring valid legal IDs still create triples.

4. Domain/range check
   - Use legal ontology IDs where `has-document` connects `case-packet` to `legal-document`.
   - Mutate subject or object types and assert no triple is emitted.

5. Source evidence check
   - The prompt must require a document/chunk/source reference for every legal fact.
   - If the parser/converter is not extended in Todo 3, the acceptance note must explicitly say source evidence is instruction-only and still depends on downstream provenance.
   - If the parser/converter is extended, tests must assert source fields survive parsing and can be attached to emitted facts or review items.

6. Scope check
   - No Hermes-specific behavior.
   - No user-facing UI requirement.
   - No legal execution behavior.

## High-Risk Files

- `ontology-prompt.md`: currently the primary semantic mismatch and likely edit target.
- `trustgraph-flow/trustgraph/extract/kg/ontology/extract.py`: actual runtime calls `extract-with-ontologies` and consumes JSONL objects.
- `trustgraph-flow/trustgraph/extract/kg/ontology/simplified_parser.py`: current dataclasses have no source evidence fields.
- `trustgraph-flow/trustgraph/extract/kg/ontology/triple_converter.py`: actual rejection point for unconfigured legal IDs.
- `tests/unit/test_extract/test_ontology/test_prompt_and_extraction.py`: useful legacy coverage, but insufficient for Todo 3 by itself.
- `tests/unit/test_extract/test_ontology/test_extract_with_simplified_format.py`: right runtime surface, but needs legal ontology fixtures.
- `tests/unit/test_extract/test_ontology/test_triple_converter_validation.py`: best existing home for unconfigured legal ID rejection and legal domain/range tests.

## Regression Commands

Baseline/final verification should use an isolated editable local install. Do not rely on `PYTHONPATH` only: the local `trustgraph-flow` and `trustgraph-base` package styles do not compose cleanly from source paths, and this worktree currently has no installed `trustgraph`, `trustgraph-base`, or `trustgraph-flow` packages.

```bash
python3 -m venv .omo/venvs/todo-3-prompt
. .omo/venvs/todo-3-prompt/bin/activate
python3 -m pip install -U pip
python3 -m pip install -e ./trustgraph -e ./trustgraph-base -e ./trustgraph-flow
python3 -m pip install pytest pytest-cov pytest-asyncio pytest-mock
```

Recommended Todo 3 test slice after A implements:

```bash
python3 -m pytest \
  tests/unit/test_extract/test_ontology/test_prompt_and_extraction.py \
  tests/unit/test_extract/test_ontology/test_extract_with_simplified_format.py \
  tests/unit/test_extract/test_ontology/test_triple_converter_validation.py \
  -q
```

Recommended new legal-specific tests:

```bash
python3 -m pytest \
  tests/unit/test_extract/test_ontology/test_legal_prompt_semantics.py \
  tests/unit/test_extract/test_ontology/test_extract_with_simplified_format.py \
  tests/unit/test_extract/test_ontology/test_triple_converter_validation.py \
  -q
```

Ontology sanity:

```bash
python3 scripts/legal_ontology/validate_ontology.py resources/ontologies/recova-debt-collection.json
```

Baseline note: running the ontology test slice directly in this worktree without installing packages failed during collection with `ModuleNotFoundError: No module named 'trustgraph.schema'`. This is an environment/setup precondition, not evidence of a Todo 3 regression.

## A Branch Pass/Fail Notes

Status: pre-implementation.

- PASS: A branch exists and is clean.
- PASS: No production edits to review yet.
- FAIL/PENDING: Todo 3 behavior is not implemented on A branch at time of review.
- PENDING: Re-run this review after A changes the prompt/tests/runtime surface.

## Final Recommendation

Do not accept Todo 3 on prompt text alone. Accept only when the rendered `extract-with-ontologies` prompt, the simplified runtime path, and converter rejection behavior all prove the same legal contract: exact configured IDs, labels as explanation only, explicit legal source evidence, and no triples from unconfigured predicates.
