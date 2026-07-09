# recova-brain-supabase-mcp-deploy-v1 - Work Plan

## TL;DR (For humans)

**What you'll get:** Recova Brain MCP will be prepared for a real server deployment: the Python MCP server runs as a container, while Supabase stores users, permissions, audit traces, and judgment records.

**Why this approach:** Supabase is excellent as the data/auth/audit layer, but the current Python MCP server already fits a container runtime better than Supabase Edge Functions. The plan keeps that separation clean.

**What it will NOT do:** It will not deploy secrets into the repo, add debtor-contact/court-filing/payment actions, or turn fixture finance/legal outputs into authoritative execution.

**Effort:** Large
**Risk:** Medium - deployment/auth/storage boundaries touch several surfaces, but the repo already has most of the building blocks.
**Decisions to sanity-check:** Cloud Run as default runtime host, `slit.amazing` as the Google/GCP account, `slit-497603` as the current billing-enabled staging project, `recova-brain-mcp` as a deferred project until billing is fixed, bearer-token staging before Supabase JWT production auth, and keeping the current lab endpoint separate until smoke tests pass.

Your next move: approve execution, or override one of the sanity-check decisions above. Full execution detail follows below.

---

> TL;DR (machine): Large/medium plan to make Recova Brain MCP deploy-ready with Python container runtime, Supabase DB/Auth/Audit, 25-tool MCP contract, staging smoke, and final verification.

## Scope
### Must have
- Use Supabase as DB/Auth/Audit storage, not as the primary Python MCP runtime.
- Deploy or prepare deployment for the Python MCP server as a containerized service.
- Prefer Cloud Run as the default runtime target, with the existing VPS/docker-compose lab path documented as fallback.
- Use the `slit.amazing` Google account for Google/GCP-side deployment setup.
- Use Google Cloud project `slit-497603` for the current Cloud Run staging path,
  because `Recova Brain MCP` / `recova-brain-mcp` is created but blocked on
  billing quota.
- Preserve the current debt-brain MCP public contract: 25 debt-only tools, no generic TrustGraph tools, no execution/write/admin tools.
- Preserve advisory-only semantics: no debtor contact, court filing, seizure, payment demand, production ledger mutation, or authoritative finance balance.
- Keep service-role credentials server-only; browser/client paths must use anon/JWT/RLS boundaries.
- Update stale lab assumptions that still expect 16 tools.
- Verify direct MCP behavior, auth rejection, Supabase trace behavior, unsafe-field absence, and rollback/readiness docs.
- Produce evidence under `.omo/evidence/recova-brain-supabase-mcp-deploy-v1/`.

### Must NOT have (guardrails, anti-slop, scope boundaries)
- Do not print, commit, or store secret values in evidence, plans, logs, or PR bodies.
- Do not put raw OCR/legal text, real debtor PII, bearer tokens, service-role keys, Cloudflare tokens, local absolute paths, or court/contact destinations into fixtures or evidence.
- Do not migrate the Python MCP server into Supabase Edge Functions.
- Do not change MCP tool order or add public admin/write/deploy tools.
- Do not perform DNS/public production cutover until staging smoke and final verification pass.
- Do not weaken existing StopGate, finance non-authority, or advisory-only protections.
- Do not treat green unit tests as enough; the endpoint must be driven through MCP client behavior.

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: TDD for behavior changes touching MCP contract, trace storage, auth, deployment scripts, and schema/RLS.
- Evidence directory: `.omo/evidence/recova-brain-supabase-mcp-deploy-v1/`.
- Required recurring checks:
  - MCP server smoke: `list_tools` returns 25 and exact accepted tail remains stable.
  - Auth smoke: missing/invalid auth is rejected without leaking secrets.
  - Decision smoke: at least one workflow/domain decision succeeds and remains advisory-only.
  - Supabase trace smoke: trace writes record redacted `evaluation_runs`, `judgment_runs`, and `tool_traces`, or explicitly record `not_recorded` when env is intentionally absent.
  - Safety scan: no raw text, tokens, local paths, PII-shaped payloads, execution/contact/filing/destination fields, or authoritative balance fields in evidence.
  - Static checks: compile, ruff, scoped basedpyright, JSON validation, and `git diff --check`.

## Execution strategy
### Parallel execution waves
- Wave 1: contract cleanup and source-of-truth alignment.
- Wave 2: Supabase schema/auth/audit hardening.
- Wave 3: container/runtime deployment readiness.
- Wave 4: staging smoke and runbook refresh.
- Wave 5: final verification.

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1 | none | 3, 5, 6 | 2, 4 |
| 2 | none | 5, 6 | 1, 3 |
| 3 | 1 | 6, 7 | 2, 4 |
| 4 | none | 5, 7 | 1, 2 |
| 5 | 2, 4 | 7, 8 | 3 |
| 6 | 1, 3 | 7, 8 | 5 after schema contract is known |
| 7 | 3, 5, 6 | 8, final verification | none |
| 8 | 5, 6, 7 | final verification | none |

## Todos
> Implementation + Test = ONE todo. Never separate.

- [ ] 1. Reconcile MCP public contract from stale 16-tool lab assumptions to current 25-tool contract
  What to do / Must NOT do: Update lab smoke, runbook, and any deployment-readiness references that still expect 16 tools. Preserve debt-only filtering and do not add generic TrustGraph or execution tools.
  Parallelization: Wave 1 | Blocked by: none | Blocks: 3, 5, 6
  References: `scripts/recova_mcp/mcp_lab_smoke.py:39`, `scripts/recova_mcp/mcp_lab_smoke.py:238-253`, `docs/product/debt-collection-ontology/recova-mcp-lab-runbook.md:44-50`, `docs/product/debt-collection-ontology/recova-mcp-lab-runbook.md:179-186`
  Acceptance criteria: focused smoke/unit tests prove `expected_tool_count=25`, generic/execution tool lists stay empty, and missing auth still rejects.
  QA scenarios: run MCP lab smoke against a local server with valid token and with no token; evidence `.omo/evidence/recova-brain-supabase-mcp-deploy-v1/task-1-mcp-contract.json`
  Commit: Y | `fix(mcp): align lab smoke with 25-tool debt-brain contract`

- [ ] 2. Define Supabase data/auth/audit schema and RLS contract
  What to do / Must NOT do: Create or refresh Supabase migration/docs for `evaluation_runs`, `judgment_runs`, `tool_traces`, user/project ownership, and RLS policies. Keep service-role inserts server-only and client reads constrained by anon/JWT/RLS.
  Parallelization: Wave 1 | Blocked by: none | Blocks: 5, 6
  References: `trustgraph_legal/lab_trace.py:57-75`, `trustgraph_legal/lab_trace.py:89-127`, `trustgraph_legal/lab_trace.py:178-191`, `trustgraph_legal/lab_trace_supabase.py:27-76`, `docs/product/debt-collection-ontology/recova-mcp-lab-secrets.md:5-16`
  Acceptance criteria: migration files validate locally, schema has RLS enabled for exposed tables, service-role-only writes are documented/tested, anon access denial is tested without real secrets.
  QA scenarios: run local SQL/schema validation plus anon-denial fixture smoke; evidence `.omo/evidence/recova-brain-supabase-mcp-deploy-v1/task-2-supabase-schema.json`
  Commit: Y | `feat(storage): define Supabase audit and auth schema`

- [ ] 3. Make the Python MCP container Cloud Run compatible while preserving VPS fallback
  What to do / Must NOT do: Adapt container entrypoint/config so the ingress process listens on `0.0.0.0` and honors `$PORT` for Cloud Run, while keeping docker-compose fallback working. Do not bind production ingress to `127.0.0.1` except inside local reverse-proxy compose.
  Parallelization: Wave 2 | Blocked by: 1 | Blocks: 6, 7
  References: `containers/Containerfile.mcp:24-34`, `deploy/recova-mcp-lab/docker-compose.yml:1-38`
  Acceptance criteria: container build succeeds, local container run exposes MCP on configured port, healthcheck passes, and compose still works.
  QA scenarios: build/run container locally with a non-default `PORT`, then MCP `list_tools`; evidence `.omo/evidence/recova-brain-supabase-mcp-deploy-v1/task-3-container-runtime.json`
  Commit: Y | `feat(deploy): prepare MCP container for Cloud Run`

- [ ] 4. Harden secret custody and environment validation
  What to do / Must NOT do: Ensure required env checks cover bearer auth, Supabase URL, service-role key, optional anon key, and provider-specific deployment vars without printing values. Add redacted evidence patterns and rotation notes.
  Parallelization: Wave 1 | Blocked by: none | Blocks: 5, 7
  References: `docs/product/debt-collection-ontology/recova-mcp-lab-secrets.md:1-37`, `deploy/recova-mcp-lab/docker-compose.yml:23-30`
  Acceptance criteria: env check passes with fake/redacted fixture values, fails clearly when required names are absent, and evidence contains only variable names/status.
  QA scenarios: run env check with complete fake env and missing env; evidence `.omo/evidence/recova-brain-supabase-mcp-deploy-v1/task-4-secret-custody.json`
  Commit: Y | `chore(deploy): harden redacted environment checks`

- [ ] 5. Wire Supabase trace smoke into MCP deployment readiness
  What to do / Must NOT do: Ensure MCP smoke can record redacted judgment/tool traces when Supabase env is present and cleanly records `not_recorded` when intentionally absent. Do not allow trace rows to contain raw text, service-role key names as values, bearer values, or local paths.
  Parallelization: Wave 2 | Blocked by: 2, 4 | Blocks: 7, 8
  References: `trustgraph_legal/lab_trace.py:23-27`, `trustgraph_legal/lab_trace.py:166-191`, `trustgraph_legal/lab_trace.py:194-202`, `trustgraph_legal/lab_trace_supabase.py:27-76`, `scripts/recova_mcp/mcp_lab_smoke.py:165-210`
  Acceptance criteria: trace smoke passes in fake/no-env mode and real-env mode when secrets are available; safety scan reports no forbidden values.
  QA scenarios: run smoke with `--allow-missing-trace`, and if staging Supabase env exists, run trace insert/count check; evidence `.omo/evidence/recova-brain-supabase-mcp-deploy-v1/task-5-trace-smoke.json`
  Commit: Y | `feat(observability): connect MCP smoke to Supabase traces`

- [x] 6. Add Cloud Run staging deployment artifacts without public cutover
  What to do / Must NOT do: Add deployment docs/config/scripts for staging Cloud Run under the `slit.amazing` Google account and current billing-enabled `slit-497603` project context: image build, env/secret mapping, billing/API readiness checks, auth expectations, rollback, timeout notes, and no-DNS-cutover default. Do not deploy production or change DNS in this todo unless a separate explicit execution approval is present.
  Parallelization: Wave 2 | Blocked by: 1, 2, 3 | Blocks: 7, 8
  References: `deploy/recova-mcp-lab/README.md`, `docs/product/debt-collection-ontology/recova-mcp-lab-runbook.md:7-23`, `docs/product/debt-collection-ontology/recova-mcp-lab-runbook.md:122-141`
  Acceptance criteria: Cloud Build and Cloud Run deploy succeed, runbook states staging-first and no public cutover, and Cloud Run config uses `$PORT`/`0.0.0.0`.
  QA scenarios: live Cloud Run service `recova-brain-mcp-staging` revision `recova-brain-mcp-staging-00003-qbb`; evidence `.omo/evidence/recova-brain-supabase-mcp-deploy-v1/gcp-readiness.json`
  Commit: Y | `docs(deploy): add Cloud Run staging path for Recova Brain MCP`

- [x] 7. Run live staging MCP smoke against the deployed endpoint
  What to do / Must NOT do: Drive the MCP endpoint through a real streamable HTTP MCP client: tool listing, auth rejection, workflow/domain decision, trace status, unsafe-field absence. If cloud credentials are unavailable, run the identical smoke against the local container and record cloud deployment as not executed.
  Parallelization: Wave 3 | Blocked by: 3, 5, 6 | Blocks: 8, final verification
  References: `scripts/recova_mcp/mcp_lab_smoke.py:54-126`, `scripts/recova_mcp/mcp_lab_smoke.py:238-253`, `tests/integration/legal_ontology/test_mcp_debt_only_server.py`
  Acceptance criteria: MCP client observes 25 tools, generic/execution tools absent, auth failure rejects, one decision succeeds, advisory-only fields are present, unsafe fields absent, trace status matches configured env.
  QA scenarios: valid-token and no-token streamable HTTP MCP smoke passed against `https://recova-brain-mcp-staging-i3pqv2n2rq-du.a.run.app/mcp`; evidence `.omo/evidence/recova-brain-supabase-mcp-deploy-v1/cloud-run-mcp-smoke.json` and `.omo/evidence/recova-brain-supabase-mcp-deploy-v1/cloud-run-mcp-no-auth.json`
  Commit: N unless docs/evidence-only changes are needed

- [ ] 8. Refresh final product/deployment docs and release handoff
  What to do / Must NOT do: Update product/deployment docs to describe the final architecture: Python MCP container runtime, Supabase DB/Auth/Audit, staging endpoint, exact MCP contract, secret custody, rollback, and deferred production cutover. Do not claim remote deployment if only local-equivalent smoke was run.
  Parallelization: Wave 4 | Blocked by: 5, 6, 7 | Blocks: final verification
  References: `.omo/drafts/recova-brain-supabase-mcp-deploy-v1.md`, `docs/product/debt-collection-ontology/recova-mcp-lab-runbook.md`, `docs/product/debt-collection-ontology/recova-mcp-lab-secrets.md`
  Acceptance criteria: docs match actual observed endpoint state, stale 16-tool language is absent, local-only vs staging-live status is explicit, and safety scan is clean.
  QA scenarios: docs/evidence consistency checker plus forbidden-word/value scan; evidence `.omo/evidence/recova-brain-supabase-mcp-deploy-v1/task-8-docs-readiness.json`
  Commit: Y | `docs(deploy): finalize Recova Brain MCP deployment handoff`

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.
- [ ] F1. Plan compliance audit
  Prove no remote production cutover, admin/write tool, debtor contact, court filing, payment demand, seizure, production ledger mutation, authoritative balance, secret leak, or PII leak was introduced.
- [ ] F2. Code quality review
  Run compile, focused tests, ruff, scoped basedpyright, JSON validation, and `git diff --check`; inspect changed public contracts for narrow deterministic behavior.
- [ ] F3. Real MCP manual QA
  Drive the final endpoint or local-equivalent container through MCP client behavior: valid auth, missing auth, tool list, decision call, trace behavior, unsafe-field absence.
- [ ] F4. Scope fidelity review
  Confirm architecture remains Python MCP container plus Supabase DB/Auth/Audit, not Supabase Edge Function runtime, and docs/evidence do not overclaim deployment state.

## Commit strategy
- Prefer one commit per completed wave if the repo is otherwise stable.
- Do not commit secrets, generated caches, local `.env`, raw smoke payloads, or evidence containing local absolute paths.
- If concurrent unrelated changes exist, stage only touched files for the current wave.
- Suggested branch: `codex/recova-brain-supabase-mcp-deploy`.
- Suggested PR title: `Deploy Recova Brain MCP with Supabase audit storage`.

## Success criteria
- The plan has been executed into a staging-ready Recova Brain MCP deployment path.
- MCP public surface is observed at 25 debt-only tools.
- Auth rejection and valid-token behavior are both observed through MCP client behavior.
- Supabase audit trace path is proven with redacted rows or explicitly documented as deferred due missing staging secrets.
- Cloud Run/container contract is satisfied or VPS fallback is clearly marked as the active runtime.
- Project `recova-brain-mcp` remains blocked on billing quota; current live
  staging deploy uses billing-enabled project `slit-497603`.
- Product/deploy docs accurately describe actual state and no longer contain stale 16-tool deployment expectations.
- Final verification wave approves without blockers.
