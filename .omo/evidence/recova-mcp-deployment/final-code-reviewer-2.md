APPROVE

# Final Code Review: Recova MCP Lab Corrective Changes

codeQualityStatus: CLEAR
recommendation: APPROVE
blockers: none

## Scope Reviewed

Reviewed the requested focus files only:

- `scripts/recova_mcp/mcp_lab_smoke.py`
- `scripts/recova_mcp/mcp_smoke_auth.py`
- `trustgraph_legal/lab_trace.py`
- `trustgraph_legal/lab_trace_supabase.py`
- `deploy/recova-mcp-lab/docker-compose.yml`
- `scripts/recova_mcp/check_lab_env.sh`
- `deploy/recova-mcp-lab/.env.example`
- `docs/product/debt-collection-ontology/recova-mcp-lab-runbook.md`
- `docs/product/debt-collection-ontology/recova-mcp-lab-secrets.md`
- `tests/unit/legal_ontology/test_lab_trace.py`
- `tests/unit/legal_ontology/test_mcp_lab_smoke.py`
- `tests/unit/legal_ontology/test_recova_mcp_deployment_config.py`

I did not read `deploy/recova-mcp-lab/.env` or print secrets.

## Skill-Perspective Check

Ran the required `omo:remove-ai-slops` and `omo:programming` review perspectives before judging test relevance and maintainability. Also loaded the Python programming reference, code-smells reference, and `httpx2` network-client reference because the diff touches Python and network smoke code.

Verdict from those perspectives: no blocking violation. The config tests are text-level tests, but the text is the deployment contract for the exact regressions under review, so they are not deletion-only false confidence. The smoke tests validate observable gate behavior (`auth_error_detected`, recorded trace/evaluation/judgment statuses), not only implementation constants. Python files remain under the 250 pure LOC ceiling.

## Findings By Severity

### CRITICAL

None.

### HIGH

None.

### MEDIUM

None.

### LOW

None requiring changes before approval.

Residual risks:

- `scripts/recova_mcp/mcp_lab_smoke.py:135` retains an explicit `--allow-missing-trace` escape hatch. It is opt-in, default smoke success requires recorded trace/evaluation/judgment rows, and docs use the default path.
- `trustgraph_legal/lab_trace_supabase.py:27` writes `evaluation_runs`, `judgment_runs`, and `tool_traces` sequentially rather than transactionally. A mid-sequence Supabase failure can leave partial rows, but the smoke fails on exceptions and this is acceptable for the lab corrective scope.

## Prior Blocker Verification

1. Public origin port exposure fixed.
   - `deploy/recova-mcp-lab/docker-compose.yml:29` now binds `127.0.0.1:8000:8000`.
   - Rendered compose evidence shows `host_ip: 127.0.0.1` for published `8000`.

2. Cloudflare token no longer passed into runtime.
   - `deploy/recova-mcp-lab/docker-compose.yml:23` through `deploy/recova-mcp-lab/docker-compose.yml:27` include MCP/Supabase runtime vars only.
   - `scripts/recova_mcp/check_lab_env.sh:10` checks only MCP/Supabase required vars.
   - `deploy/recova-mcp-lab/.env.example:1` through `deploy/recova-mcp-lab/.env.example:7` exclude `CLOUDFLARE_API_TOKEN`.
   - `docs/product/debt-collection-ontology/recova-mcp-lab-secrets.md:18` through `docs/product/debt-collection-ontology/recova-mcp-lab-secrets.md:21` correctly classify it as operator-only.

3. Auth-failure smoke no longer accepts arbitrary exceptions.
   - `scripts/recova_mcp/mcp_lab_smoke.py:87` through `scripts/recova_mcp/mcp_lab_smoke.py:98` accepts expected auth failure only after `auth_error_details` reports auth evidence.
   - `scripts/recova_mcp/mcp_smoke_auth.py:26` through `scripts/recova_mcp/mcp_smoke_auth.py:34` requires auth/401-style markers in the exception chain.
   - Independent check: nested `ExceptionGroup` with `401 Unauthorized` returns true; DNS-style failure returns false.
   - Evidence `.omo/evidence/recova-mcp-deployment/task-11-no-auth.json` has `auth_error_detected=true` and `401 Unauthorized` in the error summary.

4. Successful smoke requires trace/evaluation/judgment recording by default.
   - `scripts/recova_mcp/mcp_lab_smoke.py:230` through `scripts/recova_mcp/mcp_lab_smoke.py:253` rejects any normal success where trace, evaluation, or judgment status is not `recorded`.
   - `tests/unit/legal_ontology/test_mcp_lab_smoke.py:20` through `tests/unit/legal_ontology/test_mcp_lab_smoke.py:50` cover rejection and the explicit offline escape hatch.
   - Evidence `.omo/evidence/recova-mcp-deployment/task-11-mcp-smoke.json` reports `trace_status=recorded`, `evaluation_status=recorded`, and `judgment_status=recorded`.

5. Linked evaluation, judgment, and tool trace rows are supported.
   - `trustgraph_legal/lab_trace.py:78` through `trustgraph_legal/lab_trace.py:127` build linked row payloads.
   - `trustgraph_legal/lab_trace_supabase.py:27` through `trustgraph_legal/lab_trace_supabase.py:53` inserts evaluation, judgment, and linked tool trace rows.
   - `tests/unit/legal_ontology/test_lab_trace.py:71` through `tests/unit/legal_ontology/test_lab_trace.py:111` verifies linkage and redaction.
   - Evidence `.omo/evidence/recova-mcp-deployment/task-10-trace-count.json` shows recent `evaluation_runs`, `judgment_runs`, and a linked `tool_traces` row.

6. Python file size ceiling satisfied.
   - `scripts/recova_mcp/mcp_lab_smoke.py`: 233 pure LOC.
   - `scripts/recova_mcp/mcp_smoke_auth.py`: 41 pure LOC.
   - `trustgraph_legal/lab_trace.py`: 212 pure LOC.
   - `trustgraph_legal/lab_trace_supabase.py`: 75 pure LOC.

## Verification Run

Commands run without reading `.env`:

- `git diff --check -- <focused files>`: passed.
- `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -B -m pytest tests/unit/legal_ontology/test_lab_trace.py tests/unit/legal_ontology/test_mcp_lab_smoke.py tests/unit/legal_ontology/test_recova_mcp_deployment_config.py -q -p no:cacheprovider`: 8 passed.
- Python source compile check with `compile(...)` for the changed Python files: passed.
- Targeted auth-helper check: plain auth and nested `ExceptionGroup` auth errors are accepted; DNS-style error is rejected.
- Targeted trace validation check: `trace_status`, `evaluation_status`, and `judgment_status` set to `not_recorded` are each rejected.

I did not rerun the authenticated live smoke because the required token is in secret material that I was explicitly told not to read. I inspected the saved JSON evidence instead, and it contains the required recorded statuses and linked IDs.
