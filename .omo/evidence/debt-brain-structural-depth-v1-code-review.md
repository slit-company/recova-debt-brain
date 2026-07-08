# Structural-Depth Caveat Hardening Code Review

Review date: 2026-07-08
Repository: `/Users/slit/dev/recova-debt-brain`
Verdict: REJECT
codeQualityStatus: BLOCK
recommendation: REQUEST_CHANGES

## Skill-Perspective Check

Ran required skill-perspective check before judging tests/maintainability:

- Loaded `omo:remove-ai-slops` from `/Users/slit/.codex/plugins/cache/sisyphuslabs/omo/4.15.1/skills/remove-ai-slops/SKILL.md`.
- Loaded `omo:programming` from `/Users/slit/.codex/plugins/cache/sisyphuslabs/omo/4.15.1/skills/programming/SKILL.md`.
- Loaded Python programming reference and code-smells reference.

Diff violates the skill perspectives:

- `remove-ai-slops`: unsafe-field guardrail tests do not cover nested or item-level forbidden fields; production code copies those fields through support `workflow_signals`/`review_items`.
- `programming`: touched Python source `trustgraph_legal/domain_decisions.py` is now 256 pure LOC, above the 250 pure-LOC ceiling.

## CRITICAL

1. Unsafe-field sanitizer is shallow and leaks forbidden raw/contact fields from support review items.

   Reference: `trustgraph_legal/workflow_judgments.py:166`

   `_safe_items` only drops a small top-level key set from each support item:
   `raw_excerpt`, `raw_text`, `source_text`, `remaining_balance`, `collectable_balance_authority`.
   It does not remove top-level `debtor_contact_payload`, `filing_destination`, or `court_destination`, and it does not recursively scrub nested objects. A support signal can therefore appear in `workflow_judgment.review_items` with forbidden raw/contact fields while `pii_profile` still claims they are absent.

   Probe run during review:

   ```bash
   uv run --with pydantic --with typing-extensions python - <<'PY'
   from trustgraph_legal.workflow_judgments import WorkflowJudgmentRequest, evaluate_workflow_judgment
   import json
   request = WorkflowJudgmentRequest(
       claim_domain_payload={"schema_version": "trustgraph-claim-domain-adapter/v1", "claim_root": {"claim_ref": "claim:x"}, "fact_handles": [], "source_refs": ["fixture:x"]},
       evidence_checkpoint={
           "schema_version": "trustgraph-evidence-quality-check/v1",
           "decision": "review_required",
           "workflow_signals": [{"code": "nested_unsafe", "category": "evidence", "details": {"raw_text": "LEAK", "debtor_contact_payload": {"phone": "010"}}}],
       },
       finance_bridge={"workflow_flags": {}, "signals": []},
       legal_checkpoints={"checkpoints": []},
   )
   encoded = json.dumps(evaluate_workflow_judgment(request), ensure_ascii=False)
   print('"raw_text":' in encoded, '"debtor_contact_payload":' in encoded)
   PY
   ```

   Observed output: `True True`.

   Why this blocks approval: the user explicitly required no unsafe raw/PII/contact/filing/balance-authority fields. Current fixture/evidence scans are too narrow and give false confidence.

## HIGH

1. Touched source file exceeds the local 250 pure-LOC ceiling.

   Reference: `trustgraph_legal/domain_decisions.py:99`

   `trustgraph_legal/domain_decisions.py` was 249 pure LOC at `HEAD` and is now 256 pure LOC after this diff. The local programming rule treats `>250` pure LOC as a defect for touched source files.

   Commands:

   ```bash
   git show HEAD:trustgraph_legal/domain_decisions.py | awk '!/^[[:space:]]*$/ && !/^[[:space:]]*(#|\/\/|--)/' | wc -l
   awk '!/^[[:space:]]*$/ && !/^[[:space:]]*(#|\/\/|--)/' trustgraph_legal/domain_decisions.py | wc -l
   ```

   Observed: `249` before, `256` now.

2. Caveat-hardening work is not pushed from the reviewed worktree.

   Reference: repository state

   `git status -sb` shows `master...origin/master [ahead 1]` plus many modified and untracked caveat-hardening files. Since the stated goal includes "push", this delivery criterion is not met in the reviewed state.

## MEDIUM

1. Semireal unit helper is scenario-id keyed.

   Reference: `tests/unit/legal_ontology/workflow_scenario_requests.py:16`

   This is test-only, not production branching, and the integration boundary test correctly consumes fixture `workflow_support`. Still, the scenario-keyed helper is overfit-prone and should not be treated as independent proof of generic behavior.

2. MCP handler type warning is clean, but the fix is a type-only JSON loader shim.

   Reference: `trustgraph_legal/mcp_claim_domain_handlers.py:16`

   Scoped basedpyright reports `0 errors, 0 warnings, 0 notes`, satisfying the warning criterion. The `TYPE_CHECKING` wrapper mirrors an existing local pattern, but it is still a type-only boundary around `json.loads`; prefer a shared typed JSON loader/parser if this pattern spreads.

## LOW

1. Evidence artifacts are useful but fixture-shape limited.

   References:

   - `.omo/evidence/debt-brain-structural-depth-v1/caveat-hardening-boundary.json`
   - `.omo/evidence/debt-brain-structural-depth-v1/caveat-hardening-fallback.json`
   - `.omo/evidence/debt-brain-structural-depth-v1/caveat-hardening-final.json`

   They contain artifact paths and match the main scenario claims, but the unsafe-field check did not cover adversarial nested support items.

## Verification Performed

Passed:

```bash
uv run --with pytest --with pydantic --with typing-extensions python -m pytest tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py::test_claim_domain_workflow_support_survives_without_projection tests/unit/legal_ontology/test_workflow_judgments_v1.py::test_guardrails_reject_raw_excerpts_and_preserve_advisory_only_semantics tests/unit/legal_ontology/test_domain_decision_engine_v1.py::test_engine_returns_advisory_payload_for_possible_missing_and_blocked_routes -q
```

Result: `3 passed`, with existing `asyncio_mode` pytest warning.

```bash
uv run --with pytest --with pydantic --with typing-extensions python -m pytest tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py -q
```

Result: `3 passed`, with existing `asyncio_mode` pytest warning.

```bash
uv run --with pytest --with pydantic --with typing-extensions python -m pytest tests/unit/legal_ontology/test_workflow_judgments_v1.py tests/unit/legal_ontology/test_domain_decision_engine_v1.py tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py -q
```

Result: `15 passed`, with existing `asyncio_mode` pytest warning.

```bash
uv run --with pytest --with pydantic --with typing-extensions python -m pytest tests/unit/legal_ontology/test_evidence_quality_v1.py tests/unit/legal_ontology/test_finance_workflow_bridge_v1.py tests/unit/legal_ontology/test_legal_workflow_checkpoints_v1.py tests/unit/legal_ontology/test_operator_playbook_v1.py -q
```

Result: `16 passed`, with existing `asyncio_mode` pytest warning.

```bash
uv run --with basedpyright --with pydantic --with typing-extensions basedpyright trustgraph_legal/mcp_claim_domain_handlers.py trustgraph_legal/domain_workflow_integration.py trustgraph_legal/domain_decisions.py
```

Result: `0 errors, 0 warnings, 0 notes`.

```bash
uv run --with ruff ruff check trustgraph_legal/mcp_claim_domain_handlers.py trustgraph_legal/domain_workflow_integration.py trustgraph_legal/domain_decisions.py tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py
```

Result: `All checks passed!`

```bash
uv run python -m compileall trustgraph_legal/domain_workflow_integration.py trustgraph_legal/mcp_claim_domain_handlers.py trustgraph_legal/domain_decisions.py tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py
git diff --check
```

Result: passed.

Manual probes:

- Nested `workflow_support` without top-level support fields: `NESTED_SUPPORT_CHECK OK` across 8 scenarios, direct domain and MCP.
- Fully stripped support: `STRIPPED_SUPPORT_CHECK OK` across 8 scenarios, direct domain and MCP, for the current fixture shape.
- Adversarial nested unsafe support item: failed; forbidden fields leaked.

## Blockers

1. Fix `trustgraph_legal/workflow_judgments.py` so review/support items cannot leak forbidden fields at any depth. Prefer a whitelist of safe review-item fields over copying arbitrary JSON.
2. Add a failing regression test that puts forbidden keys at top level and nested inside `workflow_signals`, `signals`, `review_items`, and `hold_items`, then asserts the encoded workflow judgment and operator steps contain none of them.
3. Bring `trustgraph_legal/domain_decisions.py` back to `<=250` pure LOC or split a cohesive responsibility out before approval.
4. Commit and push the caveat-hardening work only after the blockers above are fixed and verification is rerun.

Suggested verification after fixes:

```bash
awk '!/^[[:space:]]*$/ && !/^[[:space:]]*(#|\/\/|--)/' trustgraph_legal/domain_decisions.py | wc -l
uv run --with pytest --with pydantic --with typing-extensions python -m pytest tests/unit/legal_ontology/test_workflow_judgments_v1.py tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py tests/unit/legal_ontology/test_domain_decision_engine_v1.py tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py -q
uv run --with basedpyright --with pydantic --with typing-extensions basedpyright trustgraph_legal/mcp_claim_domain_handlers.py trustgraph_legal/domain_workflow_integration.py trustgraph_legal/domain_decisions.py trustgraph_legal/workflow_judgments.py
uv run --with ruff ruff check trustgraph_legal/mcp_claim_domain_handlers.py trustgraph_legal/domain_workflow_integration.py trustgraph_legal/domain_decisions.py trustgraph_legal/workflow_judgments.py tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py tests/unit/legal_ontology/test_workflow_judgments_v1.py
git diff --check
git status -sb
```
