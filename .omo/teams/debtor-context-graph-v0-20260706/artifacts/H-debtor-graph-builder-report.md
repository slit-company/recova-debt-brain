# H debtor-graph-builder report

## Scope

Implemented Todo 6 in the H worktree only:

- `trustgraph_legal/debtor_context.py`
- `trustgraph_legal/debtor_context_builder.py`
- `tests/unit/legal_ontology/test_debtor_context.py`
- `.omo/evidence/debtor-context-graph-v0/task-6-debtor-graph-happy.json`
- `.omo/evidence/debtor-context-graph-v0/task-6-debtor-graph-failure.json`

Commit: `611909b5` (`feat(legal-graph): build debtor context graphs`)

Follow-up commit: `6ee22757` (`fix(legal-graph): clear verified route facts`)

## Behavior

- Builds `DebtorGraphPayload` from `DocumentAssemblyPayload` or from an OCR page path through `build_debtor_context_from_path(...)`.
- Uses stable `source_bundle_hash` to derive `debtor_graph_id` and `graph_snapshot_id`; `generated_at` does not influence either identifier.
- Emits material `FactAssertion` records with source refs, source document id, source hash, chunk id, line spans, versions, confidence, and review status.
- Emits route-compatible predicates including `enforceable_title` and `third_party_debtor_bank_hint` for the synthetic attachment/payment fixture.
- Uses `identity_unresolved` and source-bundle fallback when no identity evidence exists; similar placeholder debtor names do not merge across distinct source bundles.
- Rejects summary-only assembly JSON/payload with `DebtorContextInputError`.
- Does not import MCP, storage, Supabase, or cloud modules.

## Evidence

- Happy: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debtor-context-graph-v0-20260706/worktrees/H/.omo/evidence/debtor-context-graph-v0/task-6-debtor-graph-happy.json`
- Failure: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debtor-context-graph-v0-20260706/worktrees/H/.omo/evidence/debtor-context-graph-v0/task-6-debtor-graph-failure.json`

Failure evidence proves two similar placeholder debtor names without identity evidence produce distinct `debtor_graph_id` values and explicit `identity_unresolved` review items.

## Verification

- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_debtor_context.py -q` -> 3 passed
- `/usr/bin/python3 -m py_compile trustgraph_legal/debtor_context.py trustgraph_legal/debtor_context_builder.py tests/unit/legal_ontology/test_debtor_context.py` -> passed
- `basedpyright --level error trustgraph_legal/debtor_context.py trustgraph_legal/debtor_context_builder.py tests/unit/legal_ontology/test_debtor_context.py` -> 0 errors
- Evidence JSON parse check -> passed
- Evidence redaction scan for `"raw_text"`, `"source_text"`, `"excerpt"`, OCR body strings, and debtor placeholder tokens -> no matches
- Pure LOC: `debtor_context.py` 20, `debtor_context_builder.py` 236, test file 118
- Follow-up route probe: `bank_account_attachment` -> `possible`, `missing_facts=()`
