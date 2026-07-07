# K route-stopgate-integration report

## Scope

Implemented Todo 9 in the K worktree only:

- `trustgraph_legal/route_candidates.py`
- `tests/unit/legal_ontology/test_route_candidates.py`
- `.omo/evidence/debtor-context-graph-v0/task-9-*`

Commit: `cb4ea60b` (`feat(legal-routes): attach stop gates and legal sources`)

Follow-up: `70bf69be` (`fix(legal-routes): keep route candidates python39 compatible`) removes Python 3.12-only `typing.override` usage so `route_candidates.py` still compiles under `/usr/bin/python3` 3.9 without changing route behavior.

Second follow-up: `e6b38de2` (`fix(legal-routes): drop route candidate import dependencies`) removes production `pydantic` usage from `route_candidates.py`, restores stdlib `json.loads` resource parsing with explicit `isinstance` boundary checks, and avoids Python 3.10-only dataclass slots at module import time.

The `RouteCandidate` schema remains stable. Curated legal source metadata is encoded into redacted `legal_source_refs` strings instead of adding fields.

## Behavior

- Route candidates now load curated legal source metadata and decorate refs as `source_id|lawId=...|MST=...|article=...|effective_date=...|retrieval_status=...|review_status=...`.
- Route resource JSON loading uses stdlib `json.loads` plus explicit object/list/type checks so importing the production route module does not require `pydantic`.
- Route review status is gated by `review_status`, `retrieval_status`, and `effective_date`; draft, deprecated, future-only, draft retrieval, and future-effective sources all produce `review_required`.
- StopGate reason codes are propagated into route blockers for affected collection routes. Title acquisition routes receive only global trust/provenance StopGate blockers, so unrelated collection execution blockers do not make every title route `review_required`.
- H-style summary `case_packets` are not treated as legacy StopGate case graphs. `evaluate_case_graph(...)` is used only for compatible packet shapes with an `entities` list; otherwise explicit `graph.stop_gates` are consumed and silence is not interpreted as clearance.
- No route claims direct execution; route candidates remain advisory and keep `no_direct_execution=True`.

## Decisions

- Left `accepted` out of `CLEAR_FACT_REVIEW_STATUSES`. The canonical master baseline uses H's follow-up behavior where high-confidence route facts are emitted as `verified`; E's alternate broadening to `accepted` was not adopted for Todo 9.
- Kept StopGate bridging conservative for v0 instead of applying every StopGate reason to every route.
- Did not edit `trustgraph_legal/debtor_context_builder.py` or duplicate H's verified-fact fix.

## Evidence

- Happy route evidence: `.omo/evidence/debtor-context-graph-v0/task-9-legal-route-happy.json`
- Failure route evidence: `.omo/evidence/debtor-context-graph-v0/task-9-legal-route-failure.json`
- Focused pytest: `.omo/evidence/debtor-context-graph-v0/task-9-focused-pytest.txt`
- py_compile: `.omo/evidence/debtor-context-graph-v0/task-9-pycompile.txt`
- diff check: `.omo/evidence/debtor-context-graph-v0/task-9-diff-check.txt`
- PII/sensitive-pattern scan: `.omo/evidence/debtor-context-graph-v0/task-9-pii-scan.txt`

## Verification

- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_route_candidates.py tests/unit/legal_ontology/test_stop_gates.py tests/unit/legal_ontology/test_debtor_context.py -q` -> 23 passed
- `/usr/bin/python3 -c 'import trustgraph_legal.route_candidates; print("import-ok")'` -> import-ok
- `/usr/bin/python3 -m py_compile trustgraph_legal/route_candidates.py tests/unit/legal_ontology/test_route_candidates.py` -> passed
- `git diff --check` -> passed
- JSON parse checks for happy/failure evidence -> passed
- LSP diagnostics for changed source/test files -> no diagnostics
- PII/sensitive-pattern scan over changed source/test/evidence/report files -> no findings
- Pure LOC: `route_candidates.py` 249, `test_route_candidates.py` 227. Both are under the 250 ceiling but in the warning band; future expansion should split helpers before adding more logic.
