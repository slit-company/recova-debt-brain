# U Final Eval Pack Preflight

Status: PREFLIGHT ONLY
Final eval status: BLOCKED PENDING S/T INTEGRATION

Do not treat this artifact as Todo 15 completion. Per leader update, U must not create final eval evidence, stage files, or commit until the leader confirms Todo 13 (S) and Todo 14 (T) are integrated into `master`.

## Scope

- Team: debt-collection-domain-ontology-v1
- Member: U final-eval-pack
- Worktree: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/team-8953292e/worktrees/U`
- Branch: `team/team-8953292e/U`
- Snapshot inspected: `059d951f` (`Merge branch 'team/team-8953292e/Q'`)
- Preflight artifact: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/team-8953292e/artifacts/U-final-eval-pack-preflight.md`

## Current Gate State

- U worktree exists, contains repo files, and is a git worktree.
- `git status --short --branch` in U reported `## team/team-8953292e/U`.
- S/T are not integrated into U at this snapshot; U/S/T/V all point at `059d951f`.
- Shared artifacts present at preflight time: A through R reports/reviews and `V-final-contract-review.md`.
- T handoff received after initial preflight:
  - Report: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/team-8953292e/artifacts/T-domain-docs-report.md`
  - Commit: `7c1c6ad04494f450268eead4c592ceb1f463f270`
  - Reported evidence: `.omo/evidence/debt-collection-domain-ontology-v1/task-14-docs-smoke.txt` and `.omo/evidence/debt-collection-domain-ontology-v1/task-14-docs-pii.txt`
  - Reported checks: docs acceptance command passed, 25-tool smoke preserved claim-domain tools, and Todo 14 PII/path scan reported `NO_FINDINGS`.
- Remaining missing or not-yet-integrated Todo 13/14 inputs:
  - `artifacts/S-integration-fixtures-report.md`
  - `tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py`
  - `.omo/evidence/debt-collection-domain-ontology-v1/task-13-integration-happy.json`
  - `.omo/evidence/debt-collection-domain-ontology-v1/task-13-integration-failure.json`
  - Leader-confirmed integration of T commit into `master` and U's final-eval base.

## Preflight Commands Already Run

Resource JSON parse/count probe:

```bash
/opt/homebrew/bin/python3 - <<'PY'
import json
from pathlib import Path
root = Path("resources")
for path in sorted(root.rglob("*.json")):
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    print(f"PASS {path}")
PY
```

Outcome: all current resource JSON files parsed. Current notable counts: ontology classes=22, route v1 routes=32, domain sources=21, workflow states=12, workflow loops=2, finance component types=11, finance review triggers=6, action packet type catalog=6, stopgate v1 rules=14, manual inventory headings=115, manual route candidates=66, manual workflow candidates=12, manual action packet candidates=6.

Current focused baseline:

```bash
/opt/homebrew/bin/python3 -m pytest \
  tests/unit/legal_ontology/test_domain_ontology_v1.py \
  tests/unit/legal_ontology/test_domain_sources_v1.py \
  tests/unit/legal_ontology/test_finance_claim_model_v1.py \
  tests/unit/legal_ontology/test_workflow_v1.py \
  tests/unit/legal_ontology/test_routes_v1.py \
  tests/unit/legal_ontology/test_route_decisions_v1.py \
  tests/unit/legal_ontology/test_action_packets_v1.py \
  tests/unit/legal_ontology/test_domain_graph_adapter_v1.py \
  tests/unit/legal_ontology/test_domain_decision_engine_v1.py \
  tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py \
  tests/unit/legal_ontology/test_mcp_domain_tools.py \
  tests/integration/legal_ontology/test_mcp_tools.py \
  -q
```

Outcome: `48 passed in 3.78s`.

Missing-input probe:

```bash
for p in \
  tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py \
  docs/product/debt-collection-ontology/claim-domain-ontology-v1.md \
  /Users/cosmos/dev/ontology/trustgraph/.omo/teams/team-8953292e/artifacts/S-integration-fixtures-report.md \
  /Users/cosmos/dev/ontology/trustgraph/.omo/teams/team-8953292e/artifacts/T-domain-docs-report.md \
  .omo/evidence/debt-collection-domain-ontology-v1/task-13-integration-happy.json \
  .omo/evidence/debt-collection-domain-ontology-v1/task-13-integration-failure.json \
  .omo/evidence/debt-collection-domain-ontology-v1/task-14-docs-smoke.txt \
  .omo/evidence/debt-collection-domain-ontology-v1/task-14-docs-pii.txt
do
  test -e "$p" && echo "PRESENT $p" || echo "MISSING $p"
done
```

Outcome: all listed Todo 13/14 gate inputs were missing at this preflight snapshot.

## Final Todo 15 Runbook After Leader Opens Gate

Only after leader confirms S and T are integrated into `master`:

1. Sync/rebase or otherwise receive the leader-approved integrated state in U.
2. Confirm `master` contains S/T commits and U is based on that integrated state.
3. Verify the S/T handoff files exist:
   - `artifacts/S-integration-fixtures-report.md`
   - `artifacts/T-domain-docs-report.md`
   - `task-13-integration-happy.json`
   - `task-13-integration-failure.json`
   - `task-14-docs-smoke.txt`
   - `task-14-docs-pii.txt`
4. Run the final focused suite, including Todo 13 pipeline coverage:

```bash
/opt/homebrew/bin/python3 -m pytest \
  tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py \
  tests/unit/legal_ontology/test_domain_decision_engine_v1.py \
  tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py \
  tests/unit/legal_ontology/test_mcp_domain_tools.py \
  tests/integration/legal_ontology/test_mcp_tools.py \
  -q
```

5. Validate every resource and evidence JSON:

```bash
find resources .omo/evidence/debt-collection-domain-ontology-v1 -name '*.json' -print0 \
  | xargs -0 -n 1 /opt/homebrew/bin/python3 -m json.tool >/tmp/domain-ontology-json-validate.txt
```

6. Run final PII/path scan over final source/docs/evidence. The scan must distinguish expected literal keys such as `raw_text_included=false` from leaks of raw OCR text, real PII, secret tokens, or unredacted local paths.
7. Run summary-only manual eval if the v2 manual evidence is available. Do not include raw manual prose, raw OCR, debtor PII, or local paths in the output.
8. Write:
   - `.omo/evidence/debt-collection-domain-ontology-v1/final-domain-eval.json`
   - `.omo/evidence/debt-collection-domain-ontology-v1/final-negative-eval.json`
   - `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/team-8953292e/artifacts/U-final-eval-pack-report.md`
9. Ensure final eval JSON reports at least:
   - resource counts
   - route counts
   - workflow state counts
   - legal source counts
   - action packet type counts
   - synthetic scenario results
   - manual inventory counts
   - MCP 25-tool order if MCP tools remain in scope
10. Run `git diff --check`, stage only U-owned final eval/report artifacts, commit with `test(legal-domain): add domain ontology final eval`, then report the commit to the leader and V.

## Coordination Notes

- S acknowledged U dependency and will provide exact paths for report, task-13 happy/failure evidence, focused pytest command, and commit hash when ready.
- T handoff is received and recorded, but U still must wait for leader-confirmed S/T integration into `master` before final eval evidence or commit.
- V initial checklist is available at `artifacts/V-final-contract-review.md`; U final evidence should align with V's Todo 15 review checklist.
- `team.json` leader.sessionId is `team-8953292e`, but `codex_app.send_message_to_thread` did not accept it as a thread id. U is using the delegation source leader thread `codex://threads/019f124c-74e3-76c1-9a67-4c65799f2cd3` for leader updates.

## Current Verdict

BLOCKED FOR FINAL EVAL. Preflight is complete for the current integrated baseline, but Todo 15 final evidence and commit must wait for leader-confirmed integration of Todo 13 and Todo 14 into `master`.
