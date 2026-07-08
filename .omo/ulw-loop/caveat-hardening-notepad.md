# Caveat Hardening Notepad

Started: 2026-07-08T15:39:39+09:00

## Skills
- `omo:ulw-loop`: user requested `ulw`; use evidence-bound criteria and real-surface proof.
- `omo:programming`: Python code/test edits are expected.
- `omo:git-master`: user explicitly requested push; commit and push must preserve unrelated work and inspect history.
- `omo:debugging`: runtime caveat is a real boundary behavior risk; use hypothesis-driven evidence.

## Tier
HEAVY. This touches the domain/MCP workflow boundary, Python code, tests/evidence, and a push to `origin/master`.

## Success Criteria
1. Nested or unprojected structured workflow support remains exact at direct domain and MCP boundaries, reducing the prior support-field fragility.
2. Fully stripped support still fails safe: conservative advisory-only/human-review behavior, no unsafe raw/PII/contact/filing/authority fields.
3. Full structural-depth regression, type/lint, safety, review gate, commit, and push complete.

## Hypotheses
1. H1 confirmed then fixed: `domain_workflow_integration` only read projected top-level support fields, so payloads with nested `workflow_support` but no projection collapsed to evidence completion. It now reads the same generic fields from top-level payload or nested `workflow_support`.
2. H2 confirmed safe: fully stripped support still falls back conservatively with advisory-only/human-review semantics and unsafe/authority fields absent.
3. H3 partly confirmed and fixed: the extra strict `mcp_claim_domain_handlers.py` `reportAny` warning was removable by using a typed JSON loader boundary. Broad older remote/auth docs remain outside this code hardening scope.

## Planned Evidence
- RED: a boundary test or script showing nested `workflow_support` without top-level projection collapses before the fix.
- GREEN: the same boundary test/script passes at direct and MCP surfaces.
- Real surface: direct `evaluate_claim_domain_decision` and MCP `invoke_tool("evaluate_claim_domain_decision", ...)` across eight semireal scenarios.
- Cleanup: no tmux/server/browser/temp runtime resources left; any temporary scripts removed.

## Evidence Captured
- RED: `test_claim_domain_workflow_support_survives_without_projection` failed with `evidence_completion` instead of `title_acquisition`.
- GREEN: the same test passed after adding generic nested `workflow_support` support.
- C001 PASS: `.omo/evidence/debt-brain-structural-depth-v1/caveat-hardening-boundary.json`
- C002 PASS: `.omo/evidence/debt-brain-structural-depth-v1/caveat-hardening-fallback.json`
- Review blocker fixed: `test_review_items_scrub_nested_unsafe_support_fields` now proves nested raw/contact/filing/path/balance fields are removed from workflow review items while safe structured fields remain.
- Review blocker fixed: `trustgraph_legal/domain_decisions.py` split resource loading/version checks into `trustgraph_legal/domain_decision_resources.py`; pure LOC is now 199 for `domain_decisions.py`, 96 for the new resource module, and 243 for `workflow_judgments.py`.
- Review evidence added: `.omo/evidence/debt-brain-structural-depth-v1/caveat-hardening-red-transcript.txt`
- Slop/overfit coverage added: `.omo/evidence/debt-brain-structural-depth-v1/remove-ai-slops-review.md`
- Fresh gates after blocker fixes: focused pytest 30 passed, regression pytest 18 passed, reopened boundary pytest 11 passed, domain/MCP boundary pytest 8 passed, compileall passed, scoped basedpyright 0/0/0, scoped ruff passed, direct QA exact domain+MCP boundary passed, stripped-support fallback safety passed.
