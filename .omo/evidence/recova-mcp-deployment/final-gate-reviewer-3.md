APPROVE

# Final Gate Reviewer 3: Recova MCP Deployment ULW Closure

recommendation: APPROVE
blockers: none

## originalIntent

The user wanted a read-only final gate re-review for the Recova MCP deployment ULW closure after the prior gate blocked only on evidence/reporting gaps. The expected user-visible outcome is a lab-ready, debt-only Recova MCP endpoint at `https://recova-mcp-lab.slit.company/mcp` with bearer auth enforced, exactly 16 Recova debt tools exposed, generic TrustGraph and execution tools absent, Supabase evaluation/judgment/tool-trace evidence recorded, and the evidence bundle sufficient for closure.

## desiredOutcome

- Current evidence closes the two prior gate blockers:
  - a current approving code-review artifact explicitly applying `omo:programming` and `omo:remove-ai-slops` overfit/slop criteria;
  - RED/failing-first evidence for the corrective auth-smoke, trace/judgment/evaluation, and deployment-config tests.
- Runtime/manual QA artifacts still support the desired public behavior.
- Direct final-gate inspection finds no unresolved production, test-quality, slop, secret, or evidence blocker.
- No production file or secret file is modified or read during this review.

## userOutcomeReview

Outcome review from the user's perspective: APPROVE. The shipped evidence supports the lab closure outcome.

- Fresh no-auth probe by this reviewer returned HTTPS `HTTP/2 401` and HTTP `HTTP/1.1 401 Unauthorized` with Bearer `invalid_token` and `Authentication required`; no bearer token was used.
- `task-11-mcp-smoke.json` reports `status=ok`, `tool_count=16`, `generic_tools=[]`, `execution_tools=[]`, a Korean legal decision, and `trace_status`, `evaluation_status`, and `judgment_status` all `recorded`.
- `task-11-no-auth.json` reports `status=auth_rejected`, `auth_error_detected=true`, and a `401 Unauthorized` summary.
- `task-10-trace-count.json` shows recent `evaluation_runs`, `judgment_runs`, and `tool_traces`, with the latest trace linked to both evaluation and judgment IDs.
- `task-9-mini-native-restart.txt` proves old/new native MCP PIDs and local origin `401`.
- `task-8-compose-config.txt` and `deploy/recova-mcp-lab/docker-compose.yml` show the MCP origin bound to `127.0.0.1:8000:8000`; `CLOUDFLARE_API_TOKEN` is absent from the runtime environment.
- `f4-sensitive-scan.txt` reports `NO_FINDINGS`.
- `final-manual-qa-reviewer-2.md` is APPROVE and includes a manual QA matrix with public unauthenticated HTTP/HTTPS probes.
- Current ULW plan state in `.omo/ulw-loop/recova-mcp-deployment-20260701/goals.json` is `completed`, with C001/C002/C003 all `pass`.

## priorBlockerClosure

1. Missing current approving code-review artifact: closed.
   - `.omo/evidence/recova-mcp-deployment/final-code-reviewer-2.md` is `APPROVE`, `codeQualityStatus: CLEAR`, `blockers: none`.
   - It explicitly states `omo:programming` and `omo:remove-ai-slops` review perspectives, including LOC, bounded broad exception handling, test quality, non-tautological config tests, and implementation-mirroring/slop checks.
   - `.omo/evidence/recova-mcp-deployment/f2-code-review.md` now references `final-code-reviewer-2.md` as superseding the stale blocked report.

2. Missing RED/failing-first artifact: closed.
   - `.omo/evidence/recova-mcp-deployment/corrective-red-first.txt` applies the new corrective tests to base `349b9b884e61c0a2787a603afa741aa7771a44be`.
   - RED 1 fails on missing `evaluation_run_row`.
   - RED 2 fails on missing `auth_error_details` and `validate_result`.
   - RED 3 fails on `CLOUDFLARE_API_TOKEN` in runtime config and public `8000:8000` exposure.

## directSkillAndSlopPass

Loaded and directly applied:

- `omo:programming`
- `omo:programming` Python README and code-smells reference
- `omo:remove-ai-slops`

Direct pass result: CLEAR.

- No changed Python module exceeds the 250 pure LOC ceiling:
  - `scripts/recova_mcp/mcp_lab_smoke.py`: 233
  - `scripts/recova_mcp/mcp_smoke_auth.py`: 41
  - `trustgraph_legal/lab_trace.py`: 212
  - `trustgraph_legal/lab_trace_supabase.py`: 75
- The only broad `except Exception` in the smoke script is bounded to MCP auth failure handling and re-raises non-auth failures after `auth_error_details()` rejects them.
- The corrective tests are not deletion-only, tautological, or implementation-mirroring:
  - auth test distinguishes auth-marked errors from DNS-style failures;
  - trace validation test rejects missing evaluation recording;
  - explicit missing-trace escape hatch is separately tested;
  - config tests pin deployment security contract regressions that failed on the old base.
- No excessive/useless tests, unnecessary production extraction, speculative abstraction, or scope drift was found.
- `--allow-missing-trace` remains an opt-in smoke-script escape hatch; the default path requires all trace/evaluation/judgment statuses to be `recorded`.

## verification

Fresh verification run by this reviewer:

- `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -B -m pytest tests/unit/legal_ontology tests/integration/legal_ontology -q -p no:cacheprovider`: 58 passed.
- `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -B -m py_compile scripts/recova_mcp/mcp_lab_smoke.py scripts/recova_mcp/mcp_smoke_auth.py trustgraph_legal/lab_trace.py trustgraph_legal/lab_trace_supabase.py tests/unit/legal_ontology/test_lab_trace.py tests/unit/legal_ontology/test_mcp_lab_smoke.py tests/unit/legal_ontology/test_recova_mcp_deployment_config.py`: passed.
- `git diff --check -- . ':(exclude)deploy/recova-mcp-lab/.env'`: passed.
- `curl -i -sS --max-time 20 https://recova-mcp-lab.slit.company/mcp`: returned auth rejection, HTTPS 401.
- `curl -i -sS --max-time 20 http://recova-mcp-lab.slit.company/mcp`: returned auth rejection, HTTP 401.
- `dig +short recova-mcp-lab.slit.company`: returned Cloudflare IPs.

## checkedArtifactPaths

- `.omo/evidence/recova-mcp-deployment/final-code-reviewer-2.md`
- `.omo/evidence/recova-mcp-deployment/corrective-red-first.txt`
- `.omo/evidence/recova-mcp-deployment/f2-code-review.md`
- `.omo/evidence/recova-mcp-deployment/final-manual-qa-reviewer-2.md`
- `.omo/evidence/recova-mcp-deployment/task-11-mcp-smoke.json`
- `.omo/evidence/recova-mcp-deployment/task-11-no-auth.json`
- `.omo/evidence/recova-mcp-deployment/task-10-trace-count.json`
- `.omo/evidence/recova-mcp-deployment/task-9-mini-native-restart.txt`
- `.omo/evidence/recova-mcp-deployment/task-8-compose-config.txt`
- `.omo/evidence/recova-mcp-deployment/f4-sensitive-scan.txt`
- `.omo/evidence/recova-mcp-deployment/f3-real-qa.txt`
- `.omo/evidence/recova-mcp-deployment/f4-scope-fidelity.md`
- `.omo/evidence/recova-mcp-deployment/final-review-https-unauth.txt`
- `.omo/evidence/recova-mcp-deployment/final-review-http-unauth.txt`
- `.omo/evidence/recova-mcp-deployment/task-4-generic-block.json`
- `.omo/evidence/recova-mcp-deployment/task-6-execution-block.json`
- `.omo/evidence/recova-mcp-deployment/task-10-rls-deny.txt`
- `.omo/evidence/recova-mcp-deployment/task-12-rollback-dry-run.txt`
- `.omo/evidence/recova-mcp-deployment/task-8-compose-down.txt`
- `.omo/evidence/recova-mcp-deployment/ulw-status-before-checkpoint.json`
- `.omo/evidence/recova-mcp-deployment/ulw-status-after-checkpoint.json`
- `.omo/evidence/recova-mcp-deployment/ulw-status-after-record.json`
- `.omo/evidence/recova-mcp-deployment/ulw-checkpoint-final.json`
- `.omo/ulw-loop/recova-mcp-deployment-20260701/goals.json`
- `.omo/ulw-loop/recova-mcp-deployment-20260701/ledger.jsonl`
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

None remaining.

Notes:

- `.omo/evidence/recova-mcp-deployment/ulw-checkpoint-final.json` contains an older `ok=false` Codex snapshot mismatch, but it is superseded by `ulw-status-before-checkpoint.json`, `ulw-status-after-checkpoint.json`, `ulw-status-after-record.json`, and current `goals.json`, all of which show the durable ULW criteria completed/passing.
- I did not read `deploy/recova-mcp-lab/.env` or any raw secret file.
- I did not rerun the authenticated smoke because that would require secret material; approval relies on the inspected authenticated smoke artifact and the current no-auth public probes.

## residualRisks

- The authenticated live path can drift after this review because it depends on external DNS, Cloudflare Tunnel, the `mini` host, bearer-token custody, and Supabase availability.
- Supabase evaluation, judgment, and tool-trace inserts are sequential, not transactional; a mid-write failure can leave partial rows, but the smoke path fails on write exceptions and this is acceptable for the lab scope.
- The lab is explicitly `lab-ready, not production-ready`; promotion requires additional fixture packs and operational hardening.
