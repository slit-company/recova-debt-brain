# A Ontology Config Report

## Result

- Member: A `ontology-config`
- Branch: `team/debt-collection-ontology-todo-2-4-20260630/A`
- Commit: `5655529a feat(ontology): add recova debt collection ontology`
- Worktree: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debt-collection-ontology-todo-2-4-20260630/worktrees/A`

## Changed Files

- `resources/ontologies/recova-debt-collection.json`
- `scripts/legal_ontology/validate_ontology.py`
- `tests/unit/legal_ontology/test_validate_ontology.py`

## Ontology Coverage

The v0 TrustGraph config is keyed as `recova-debt-collection` and contains:

- 36 classes
- 41 object properties
- 44 datatype properties

It covers Party and Identity, Claim and Amount, Assignment and Succession,
Enforcement Title and Procedure, Attachment Target, Exemption and Priority,
Insolvency and Credit Recovery, Asset Evidence, Operational Ledger, Document
Provenance, Legal Check, StopGate, and versioned Rule Source / Rule Version /
Rule Evidence modeling.

## Verification

- Initial A worktree status before edits: clean.
- `python3 -m pytest tests/unit/legal_ontology/test_validate_ontology.py -q`: passed, 2 tests.
- `python3 -m json.tool resources/ontologies/recova-debt-collection.json`: passed.
- `python3 scripts/legal_ontology/validate_ontology.py resources/ontologies/recova-debt-collection.json`: `PASS ontology recova-debt-collection classes=36 objectProperties=41 datatypeProperties=44`.
- Temp-copy failure check with first object property `rdfs:range` changed to `missing-class`: exited 1 and reported `ERROR recova-debt-collection.objectProperties.has-document: unknown range missing-class`.
- `rg -n "resident|주민등록번호|[0-9]{6}-[0-9]{7}" resources/ontologies scripts/legal_ontology tests/unit/legal_ontology || true`: no findings.
- `python3 -m compileall -q scripts/legal_ontology/validate_ontology.py tests/unit/legal_ontology/test_validate_ontology.py`: passed.
- Pure LOC: validator 172, focused test 33.
- `git diff --cached --check`: passed before commit.
- `git diff --check HEAD~1 HEAD`: passed after commit.

## Isolation Evidence

Pre-commit A worktree `git status --short`:

```text
?? resources/
?? scripts/legal_ontology/validate_ontology.py
?? tests/unit/legal_ontology/
```

Pre-commit main checkout `git status --short`:

```text
?? .omo/
```

Post-commit A worktree `git status --short`:

```text

```

Post-commit main checkout `git status --short`:

```text
?? .omo/
```

## Notes

- The validator uses standalone structural checks because importing
  `OntologyLoader` directly through the package triggers broader TrustGraph
  runtime imports that are not available in this lightweight CLI context.
- Object property domains and ranges must point to existing ontology classes.
- Datatype property domains must point to existing classes, and ranges must use
  `xsd:` datatype identifiers.
- No raw OCR document text or raw sensitive identifiers were added.
