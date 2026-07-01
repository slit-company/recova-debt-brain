BLOCKED

recommendation: REJECT

## originalIntent

The user wanted a final read-only gate review for the Recova MCP deployment ULW closure. The intended outcome is a live debt-only Recova MCP lab at `https://recova-mcp-lab.slit.company/mcp`, with auth enforced, exactly 16 Recova debt tools exposed, generic/execution tools absent, Supabase evaluation/judgment/tool-trace evidence recorded, deployment/rollback operations evidenced, and the previous gate blockers demonstrably corrected.

## desiredOutcome

- Current artifacts prove the live endpoint, tool surface, Supabase rows, restart/operations evidence, and verification gates.
- Current code and tests satisfy the OMO `programming`, `remove-ai-slops`, and refactor/slop constraints.
- The code review report explicitly covers the same programming/remove-ai-slops overfit/slop perspective required by the final gate.
- No production files or secrets are read or modified during this review.

## userOutcomeReview

Current runtime and code evidence are mostly strong:

- Fresh unauthenticated HTTPS probe returned `HTTP/2 401` with `invalid_token` and `Authentication required`.
- Fresh unauthenticated HTTP probe returned `HTTP/1.1 401 Unauthorized` with the same bearer-auth rejection.
- Fresh DNS lookup returned Cloudflare IPs for `recova-mcp-lab.slit.company`.
- `task-11-mcp-smoke.json` reports `status=ok`, `tool_count=16`, `generic_tools=[]`, `execution_tools=[]`, Korean `decision=보류`, and `trace_status/evaluation_status/judgment_status=recorded`.
- `task-10-trace-count.json` includes linked recent rows: `evaluation_runs.id=d931d7ea-9a06-44ac-b299-baa0be68dc53`, `judgment_runs.evaluation_run_id=d931d7ea-9a06-44ac-b299-baa0be68dc53`, and `tool_traces` with both linked IDs.
- `task-9-mini-native-restart.txt` proves old PID `85097`, new PID `89515`, and local origin `401`.
- `task-8-compose-config.txt` shows `127.0.0.1:8000:8000` and no `CLOUDFLARE_API_TOKEN` in the runtime environment.
- Local verification rerun by this reviewer: `58 passed in 2.81s`, `py_compile` passed, and `git diff --check` passed.
- Changed Python pure LOC: `mcp_lab_smoke.py` 233, `mcp_smoke_auth.py` 41, `lab_trace.py` 212, `lab_trace_supabase.py` 75.

I did not read `deploy/recova-mcp-lab/.env` or any raw secret file, and I did not print secrets.

## blockers

1. Required code-review skill/slop coverage is still not supported by a current approving report.
   - `.omo/evidence/recova-mcp-deployment/f2-code-review.md` is the updated approving code-review artifact, but it does not explicitly state that `omo:programming` and `omo:remove-ai-slops` were loaded/applied, and it does not cover overfit/slop classes such as deletion-only tests, tautological tests, implementation-mirroring tests, or excessive/useless tests.
   - `.omo/evidence/recova-mcp-deployment/final-code-reviewer.md` does contain a skill-perspective section, but its verdict is still `BLOCKED` and its findings are stale relative to the current corrective diff. It cannot serve as current approving code-review evidence.
   - Gate requirement: reject if code-review report coverage is absent, missing, or unsupported.

2. Failing-first evidence for the corrective tests is missing from the inspected artifacts.
   - Current tests are behavioral and pass, but I did not find a RED/failing-first artifact for the corrective tests added around auth-smoke validation, trace/evaluation/judgment recording, or compose/runtime credential exposure.
   - The plan mentions failing-first expectations, and green evidence exists, but the final gate requested proof that tests were added first. Counts and current passing tests do not prove that order.

No current production-code blocker was found in the direct pass. The remaining blockers are evidence/reporting blockers for the final gate.

## directSlopAndProgrammingPass

Loaded and applied:

- `omo:programming`
- `omo:remove-ai-slops`
- `omo:refactor` constraints as relevant to the reported refactor/slop gate
- Python reference and code-smell reference for LOC, broad exception, over-defensive code, test quality, and maintenance-burden checks

Direct findings:

- No changed Python module exceeds the 250 pure-LOC ceiling.
- The one broad `except Exception` in `mcp_lab_smoke.py` is bounded to expected MCP auth failure handling: non-auth exceptions are re-raised after `auth_error_details()` rejects them.
- Normal authenticated smoke now requires `trace_status`, `evaluation_status`, and `judgment_status` to be `recorded`; missing trace is only allowed behind explicit `--allow-missing-trace`.
- The new tests are not deletion-only and do not merely assert that code was removed. They exercise auth-marker discrimination, trace status validation, and runtime config exclusion.
- No unnecessary production extraction or speculative abstraction was found that would block the gate.

## checkedArtifactPaths

- `.omo/evidence/recova-mcp-deployment/task-11-mcp-smoke.json`
- `.omo/evidence/recova-mcp-deployment/task-11-no-auth.json`
- `.omo/evidence/recova-mcp-deployment/task-10-trace-count.json`
- `.omo/evidence/recova-mcp-deployment/task-9-mini-native-restart.txt`
- `.omo/evidence/recova-mcp-deployment/task-8-compose-config.txt`
- `.omo/evidence/recova-mcp-deployment/final-review-https-unauth.txt`
- `.omo/evidence/recova-mcp-deployment/final-review-http-unauth.txt`
- `.omo/evidence/recova-mcp-deployment/f2-code-review.md`
- `.omo/evidence/recova-mcp-deployment/f3-real-qa.txt`
- `.omo/evidence/recova-mcp-deployment/f4-scope-fidelity.md`
- `.omo/evidence/recova-mcp-deployment/f4-sensitive-scan.txt`
- `.omo/evidence/recova-mcp-deployment/final-code-reviewer.md`
- `.omo/evidence/recova-mcp-deployment/final-manual-qa-reviewer.md`
- `.omo/evidence/recova-mcp-deployment/ulw-status-before-checkpoint.json`
- `.omo/evidence/recova-mcp-deployment/ulw-checkpoint-final.json`
- `.omo/evidence/recova-mcp-deployment/ulw-status-after-checkpoint.json`
- `.omo/evidence/recova-mcp-deployment/ulw-status-after-record.json`
- `.omo/evidence/recova-mcp-deployment/ulw-record-c001.json`
- `.omo/evidence/recova-mcp-deployment/ulw-record-c002.json`
- `.omo/evidence/recova-mcp-deployment/ulw-record-c003.json`
- `scripts/recova_mcp/mcp_lab_smoke.py`
- `scripts/recova_mcp/mcp_smoke_auth.py`
- `trustgraph_legal/lab_trace.py`
- `trustgraph_legal/lab_trace_supabase.py`
- `tests/unit/legal_ontology/test_lab_trace.py`
- `tests/unit/legal_ontology/test_mcp_lab_smoke.py`
- `tests/unit/legal_ontology/test_recova_mcp_deployment_config.py`
- `deploy/recova-mcp-lab/docker-compose.yml`
- `deploy/recova-mcp-lab/.env.example`
- `scripts/recova_mcp/check_lab_env.sh`
- `docs/product/debt-collection-ontology/recova-mcp-lab-runbook.md`
- `docs/product/debt-collection-ontology/recova-mcp-lab-secrets.md`

## exactEvidenceGaps

- Current approving code-review report with explicit `programming` plus `remove-ai-slops` overfit/slop coverage: missing.
- Current approving code-review report superseding the stale `final-code-reviewer.md` BLOCKED verdict: missing.
- RED/failing-first artifact for the corrective auth-smoke, trace/evaluation/judgment, and compose/runtime credential tests: missing.

Final gate result remains BLOCKED until those evidence gaps are closed.
