# Final Code Quality Review - Recova MCP Deployment

Verdict: **BLOCKED**

- `codeQualityStatus`: `BLOCK`
- `recommendation`: `REQUEST_CHANGES`
- `reportPath`: `.omo/evidence/recova-mcp-deployment/final-code-reviewer.md`

## Skill-Perspective Check

Loaded and applied `omo:remove-ai-slops` and `omo:programming` before judging tests and maintainability.

- `remove-ai-slops`: no deletion-only or tautological test suite pattern found in the debt-only server and trace tests, but the final smoke script has a false-success path for a required deployment criterion.
- `programming`: core Python files reviewed for boundary validation, typed escape hatches, needless abstraction, broad defensive code, and 250 pure-LOC ceiling. The reviewed Python files are under the 250 pure-LOC limit. The deployment secret and smoke-gate issues below violate the skill perspective because they create false confidence and unnecessary boundary exposure.

## Findings

### CRITICAL

None.

### HIGH

1. **Compose publishes the MCP origin over plain HTTP, bypassing the intended HTTPS reverse proxy.**
   - References: `deploy/recova-mcp-lab/docker-compose.yml:29-30`, `.omo/plans/recova-mcp-deployment.md:22`, `.omo/plans/recova-mcp-deployment.md:198-199`.
   - The compose service exposes `recova-mcp` on host port `8000` while Caddy also fronts the service on `80/443`. If this bundle is used on a public host, clients can reach the FastMCP origin directly over cleartext HTTP instead of the required HTTPS `/mcp` surface. Bearer auth still applies, but tokens and MCP traffic can be sent over HTTP and proxy-level TLS/host assumptions are bypassed.
   - Evidence inspected: `task-8-local-mcp-http.txt` shows direct HTTP origin access returning an MCP auth response, proving the origin is reachable on the published port.
   - Required fix: remove the public `ports` mapping for `recova-mcp`, or bind it to loopback only for local smoke (`127.0.0.1:8000:8000`) and keep Caddy/Cloudflare as the only public path.

2. **The internet-facing MCP runtime is given the Cloudflare DNS mutation token.**
   - References: `deploy/recova-mcp-lab/docker-compose.yml:23-28`, `deploy/recova-mcp-lab/.env.example:5`, `docs/product/debt-collection-ontology/recova-mcp-lab-secrets.md:5-10`.
   - The secrets doc says `CLOUDFLARE_API_TOKEN` is used only for DNS mutation, but the compose file injects it into the MCP application container. That expands the blast radius of an MCP runtime compromise to DNS control.
   - Required fix: keep Cloudflare credentials in deployment tooling/operator environment only. Do not pass them to the MCP runtime container or require them in a runtime env check.

3. **The MCP smoke script can print `PASS` even when required Supabase trace recording is skipped.**
   - References: `scripts/recova_mcp/mcp_lab_smoke.py:141-144`, `scripts/recova_mcp/mcp_lab_smoke.py:161-173`, `scripts/recova_mcp/mcp_lab_smoke.py:124`, `.omo/plans/recova-mcp-deployment.md:160-165`, `.omo/plans/recova-mcp-deployment.md:202-204`.
   - `_record_trace_if_configured()` returns `not_recorded` when Supabase env is absent, but `_validate_result()` does not reject that state. The script then prints `PASS mcp_lab_smoke ok`.
   - Evidence inspected: `.omo/evidence/recova-mcp-deployment/task-9-mini-mcp-auth.json:2` prints `PASS mcp_lab_smoke ok` while `.omo/evidence/recova-mcp-deployment/task-9-mini-mcp-auth.json:28` records `trace_status: "not_recorded"`.
   - Current final live evidence does show `.omo/evidence/recova-mcp-deployment/task-11-mcp-smoke.json:27` as `trace_status: "recorded"`, but the gate script still permits a false pass for a stated success criterion.
   - Required fix: make `trace_status == "recorded"` mandatory for normal smoke success, with an explicit opt-in offline/local flag if skipped trace recording is intentionally acceptable.

### MEDIUM

None.

### LOW

None.

## Positive Evidence Inspected

- `git status --short --branch`: current branch is `master...origin/master`; pre-existing OMO loop/evidence files are modified/untracked.
- `git diff --check origin/master..HEAD`: clean. Because `HEAD == origin/master`, I also checked `git diff --check 5f7ee0f0^..349b9b88` and `git diff --check 5f7ee0f0..349b9b88`; both were clean.
- Commit range inspected: `5f7ee0f0` through `349b9b88`.
- `.omo/plans/recova-mcp-deployment.md`: scope, verification strategy, task 11 acceptance, and final success criteria.
- `.omo/evidence/recova-mcp-deployment/f2-code-review.md`: prior review and test evidence claims.
- `.omo/evidence/recova-mcp-deployment/task-11-mcp-smoke.json`: live authenticated smoke reports 16 tools, no generic tools, no execution tools, Korean decision, and `trace_status: recorded`.
- `.omo/evidence/recova-mcp-deployment/task-11-no-auth.json`: unauthenticated MCP client smoke is rejected.
- `.omo/evidence/recova-mcp-deployment/f3-real-qa.txt`, `f3-live-https-no-auth.txt`, `f3-live-http-plain.txt`, `f3-dig.txt`: live DNS/HTTPS/no-auth evidence.
- `.omo/evidence/recova-mcp-deployment/f4-sensitive-scan.txt`: `NO_FINDINGS`; I also ran a stricter path-only token/PII scan that found only a pre-existing dummy JWT test outside this commit range.
- `.omo/evidence/recova-mcp-deployment/task-10-trace-count.json`, `task-10-trace-insert.json`, `task-10-rls-deny.txt`, `task-3-supabase-smoke.txt`: Supabase trace/RLS/PII-shape evidence.
- Source/config/tests inspected: `trustgraph-mcp/trustgraph/mcp_server/legal_only.py`, `trustgraph-mcp/trustgraph/mcp_server/auth.py`, `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py`, `trustgraph_legal/lab_trace.py`, `trustgraph_legal/lab_trace_smoke.py`, `scripts/recova_mcp/mcp_lab_smoke.py`, `scripts/recova_mcp/check_lab_env.sh`, `scripts/recova_mcp/check_runbook.py`, `scripts/recova_mcp/rollback_lab.sh`, `scripts/legal_ontology/evaluate_packet.py`, `deploy/recova-mcp-lab/*`, `containers/Containerfile.mcp`, `supabase/migrations/20260701000100_recova_lab_memory.sql`, and the related legal ontology unit/integration tests.

I did not read committed or local raw `.env` secret values. I did not rerun pytest to preserve the requested read-only review mode; I inspected the recorded test evidence and source/tests directly.

## Blockers

- Remove or loopback-bind the direct MCP origin port in `deploy/recova-mcp-lab/docker-compose.yml`.
- Remove `CLOUDFLARE_API_TOKEN` from runtime MCP container env and runtime-required server variables.
- Make `scripts/recova_mcp/mcp_lab_smoke.py` fail normal success unless Supabase trace recording is actually `recorded`, or add an explicit local/offline mode that cannot be confused with deployment completion.
