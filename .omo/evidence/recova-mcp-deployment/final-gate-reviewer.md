# Recova MCP Deployment Final Gate Review

recommendation: BLOCKED

## originalIntent

The user wanted the Recova MCP deployment completion gate reviewed from current artifacts and current live state. The intended shipped outcome is a live debt-only Recova debt-brain MCP lab at `https://recova-mcp-lab.slit.company/mcp`, backed by Supabase experiment memory, with generic TrustGraph tools and real-world execution actions blocked, no raw secrets/PII exposed, DNS/TLS/rollback/client evidence captured, and every must-have/must-not-have/success criterion proven by artifacts rather than claims.

## desiredOutcome

- Live HTTPS `/mcp` endpoint resolves and rejects missing auth.
- Authorized MCP smoke proves exactly 16 Recova debt tools, no generic tools, no execution tools, and a Korean StopGate decision with source/evidence capture.
- Supabase proves both trace and evaluation/judgment persistence for a live run, with RLS/redaction/PII rejection evidence.
- Runtime/deployment matches the plan's concrete host and Docker/Caddy or equivalent deployment requirements, with restart/rollback proof.
- Final review artifacts explicitly cover plan compliance, code quality, real QA, scope fidelity, and the required programming/remove-ai-slops overfit/slop criteria.

## userOutcomeReview

The endpoint is currently reachable and rejects unauthenticated requests: fresh `curl -i --max-time 20 https://recova-mcp-lab.slit.company/mcp -H 'Accept: application/json, text/event-stream'` returned `HTTP/2 401` with `invalid_token`, and plain HTTP returned `HTTP/1.1 401 Unauthorized`. Fresh `dig +short recova-mcp-lab.slit.company` returned Cloudflare IPs. The saved authenticated smoke JSON reports `status=ok`, `tool_count=16`, `generic_tools=[]`, `execution_tools=[]`, a Korean decision, and `trace_status=recorded`.

That is not enough to approve the gate. Several original success criteria and final-review requirements are not proven, and one smoke artifact is over-broad enough to produce false confidence. The prior F1-F4 reports all say APPROVE, but F2 does not document the required `programming` plus `remove-ai-slops`/overfit perspective, and direct inspection found unresolved slop in the MCP no-auth smoke.

## criteriaCoverageJudgment

- C001 live endpoint and saved authorized tool smoke: partially covered. Current unauth HTTPS is proven live; saved `task-11-mcp-smoke.json` proves the 16-tool debt-only surface and trace status. Current authorized smoke was not rerun because `MCP_LAB_BEARER_TOKEN`, `SUPABASE_URL`, and `SUPABASE_SERVICE_ROLE_KEY` are not exported in the review environment, and I did not access raw `.env` secrets.
- C002 adversarial path: partially covered. Curl proves missing auth rejection, and saved artifacts prove generic/execution tool absence. However `task-11-no-auth.json` is weak because the smoke script reports `auth_rejected` for any exception in expect-auth-failure mode.
- C003 regression/operations: partially covered. Saved pytest/local-compose/rollback artifacts exist. The plan's Docker/Caddy restart or reboot-level live criterion is not proven because the live target is documented as native Python on `mini` behind Cloudflare Tunnel, not Docker/Caddy.
- Must-have Supabase memory/evaluation: partially covered. Remote migrations/table existence and `tool_traces` rows are shown, but no artifact proves a live `judgment_runs` or `evaluation_runs` row insert/read even though the plan requires trace/evaluation rows.
- Final verification wave: not complete. F1-F4 exist and approve, but F2 lacks the required skill-perspective/slop coverage, and direct slop review found an unresolved false-positive risk.

## blockers

1. Missing required code-review coverage for programming/remove-ai-slops overfit/slop criteria.
   - Evidence: `.omo/evidence/recova-mcp-deployment/f2-code-review.md:1-25` lists reviewed areas and commands, but does not mention `programming`, `remove-ai-slops`, slop, overfit, tautological tests, implementation-mirroring tests, deletion-only tests, or excessive/useless tests.
   - Direct check: `rg -n "programming|remove-ai-slops|slop|overfit|tautolog|implementation|mirror|deletion-only|excessive|coverage" f1/f2/f3/f4` only found the APPROVE status lines, not the required criterion coverage.

2. Unresolved no-auth smoke slop can turn unrelated failures into a passing auth-rejection artifact.
   - Evidence: `scripts/recova_mcp/mcp_lab_smoke.py:77-83` catches `Exception` and, when `--expect-auth-failure` is set, returns `{"status":"auth_rejected","auth_failure":true}` for any exception type.
   - Evidence: `scripts/recova_mcp/mcp_lab_smoke.py:161-165` then validates only `status == "auth_rejected"`.
   - Evidence: `.omo/evidence/recova-mcp-deployment/task-11-no-auth.json:1-4` contains only `status=auth_rejected`, `auth_failure=true`, and `error_type=ExceptionGroup`; it does not prove the exception was an HTTP 401 bearer-auth rejection rather than DNS/TLS/server/import failure.
   - Impact: this is exactly the kind of false-confidence/overfit artifact the `remove-ai-slops` pass is supposed to reject.

3. Supabase live evaluation/judgment row proof is missing.
   - Plan requirement: `.omo/plans/recova-mcp-deployment.md:25` requires Supabase trace/evaluation logs; `.omo/plans/recova-mcp-deployment.md:156-157` requires trace/evaluation tables and specifically one redacted `judgment_runs` row plus one redacted `tool_traces` row for the happy DB smoke; `.omo/plans/recova-mcp-deployment.md:204` requires redacted trace/evaluation rows for a live run.
   - Evidence present: `.omo/evidence/recova-mcp-deployment/task-10-table-check.json:3-15` proves table existence for `judgment_runs` and `tool_traces`.
   - Evidence present: `.omo/evidence/recova-mcp-deployment/task-10-trace-count.json:1-10` proves recent `tool_traces` only.
   - Evidence present: `trustgraph_legal/lab_trace.py:112-132` writes only to `/rest/v1/tool_traces`.
   - Gap: no checked artifact proves a live insert/read row in `judgment_runs` or `evaluation_runs`.

4. Live Docker/Caddy restart or reboot-level deployment proof is missing, and live runtime diverges from the goal wording.
   - Plan requirement: `.omo/plans/recova-mcp-deployment.md:22-23` asks for HTTPS `/mcp` via Caddy or equivalent and Docker Compose installation; `.omo/plans/recova-mcp-deployment.md:206` requires Docker/Caddy restart survival or reboot-level smoke.
   - Current artifact: `.omo/evidence/recova-mcp-deployment/task-9-server-target.json` names `target_kind=cloudflare_tunnel_on_mini_native_python` and `process=native Python FastMCP under pyenv 3.14.3 venv`.
   - Current runbook: `docs/product/debt-collection-ontology/recova-mcp-lab-runbook.md` states the live lab runs on `mini` through native Python plus Cloudflare Tunnel, while the Docker/Caddy bundle is retained as a reproducible package.
   - Gap: local compose evidence exists, but no artifact proves the live Docker/Caddy restart/reboot criterion.

5. Current authorized live smoke could not be refreshed without secrets.
   - Safe presence check showed `MCP_LAB_BEARER_TOKEN=absent`, `SUPABASE_URL=absent`, and `SUPABASE_SERVICE_ROLE_KEY=absent`.
   - I did not read raw `.env` files. Therefore current live authorized MCP/Supabase state rests on saved artifacts, not a fresh gate-run smoke.

## missingEvidenceAudit

- Missing or unsupported: `.omo/evidence/recova-mcp-deployment/task-10-supabase-remote.json` named by the plan's Todo 10 happy path does not appear in the evidence inventory inspected.
- Missing: live `judgment_runs`/`evaluation_runs` row insert/read proof for the same run id as the live MCP smoke.
- Missing: code review report section explicitly applying `programming` and `remove-ai-slops` criteria to production code and tests.
- Missing: no-auth MCP client proof that checks for the actual HTTP bearer-auth rejection rather than any exception.
- Missing: current authorized smoke rerun from the review environment without accessing `.env` secrets.
- Missing/unsupported: live Docker/Caddy restart or reboot-level smoke for the actual public runtime.
- Not supplied: a separate notepad path; I inspected the requested goals/ledger/plan/evidence instead.

## checkedArtifactPaths

- `.omo/ulw-loop/recova-mcp-deployment-20260701/goals.json`
- `.omo/ulw-loop/recova-mcp-deployment-20260701/ledger.jsonl`
- `.omo/plans/recova-mcp-deployment.md`
- `.omo/evidence/recova-mcp-deployment/f1-plan-compliance.md`
- `.omo/evidence/recova-mcp-deployment/f2-code-review.md`
- `.omo/evidence/recova-mcp-deployment/f3-real-qa.txt`
- `.omo/evidence/recova-mcp-deployment/f3-dig.txt`
- `.omo/evidence/recova-mcp-deployment/f3-live-https-no-auth.txt`
- `.omo/evidence/recova-mcp-deployment/f3-live-http-plain.txt`
- `.omo/evidence/recova-mcp-deployment/f4-scope-fidelity.md`
- `.omo/evidence/recova-mcp-deployment/f4-sensitive-scan.txt`
- `.omo/evidence/recova-mcp-deployment/task-11-mcp-smoke.json`
- `.omo/evidence/recova-mcp-deployment/task-11-no-auth.json`
- `.omo/evidence/recova-mcp-deployment/task-10-table-check.json`
- `.omo/evidence/recova-mcp-deployment/task-10-trace-count.json`
- `.omo/evidence/recova-mcp-deployment/task-10-trace-insert.json`
- `.omo/evidence/recova-mcp-deployment/task-10-rls-deny.txt`
- `.omo/evidence/recova-mcp-deployment/task-12-rollback-dry-run.txt`
- `.omo/evidence/recova-mcp-deployment/task-8-local-mcp-http.txt`
- `.omo/evidence/recova-mcp-deployment/task-8-compose-down.txt`
- `.omo/evidence/recova-mcp-deployment/task-9-server-target.json`
- `.omo/evidence/recova-mcp-deployment/final-manual-qa-reviewer.md`
- `scripts/recova_mcp/mcp_lab_smoke.py`
- `trustgraph_legal/lab_trace.py`
- `docs/product/debt-collection-ontology/recova-mcp-lab-runbook.md`
- `deploy/recova-mcp-lab/docker-compose.yml`
- `deploy/recova-mcp-lab/Caddyfile`

## liveStateAndGitRemoteStatus

- Fresh DNS: `dig +short recova-mcp-lab.slit.company` returned `104.21.38.181` and `172.67.137.32`.
- Fresh HTTPS no-auth: `curl -i --max-time 20 https://recova-mcp-lab.slit.company/mcp -H 'Accept: application/json, text/event-stream'` returned `HTTP/2 401` with `Authentication required`.
- Fresh HTTP no-auth: `curl -i --max-time 20 http://recova-mcp-lab.slit.company/mcp -H 'Accept: application/json, text/event-stream'` returned `HTTP/1.1 401 Unauthorized`.
- Git HEAD: `349b9b884e61c0a2787a603afa741aa7771a44be`.
- `origin/master` via `git ls-remote`: `349b9b884e61c0a2787a603afa741aa7771a44be`.
- `upstream/master` via `git ls-remote`: `04c5921687ddc413b05da6707821a964c3ec13ab`.
- Working tree before this report was not clean: modified ULW `goals.json` and `ledger.jsonl`, plus untracked review/evidence artifacts.

## slopReview

I loaded/consulted `omo:programming` and `omo:remove-ai-slops`. Direct pass result:

- Production code/test sizes checked: no reviewed Python file exceeded 250 pure LOC.
- Found unresolved overfit/slop: broad auth-failure smoke exception handling in `scripts/recova_mcp/mcp_lab_smoke.py`.
- Found report-coverage failure: F2 does not show the required skill-perspective or overfit/slop criterion coverage.
- Found missing behavior proof: no remote evaluation/judgment row proof despite the plan requiring it.

Final gate result: BLOCKED until the blockers above are fixed and evidenced with fresh artifacts.
