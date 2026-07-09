---
slug: recova-brain-supabase-mcp-deploy-v1
status: cloud-run-staging-live
intent: clear
pending-action: decide whether to keep staging in slit-497603 or fix billing on recova-brain-mcp before production cutover
approach: Use Supabase for DB/Auth/Audit trace storage, and deploy the Python MCP server as a containerized service. Do not run the Python MCP runtime inside Supabase Edge Functions.
---

# Draft: recova-brain-supabase-mcp-deploy-v1

## Components (topology ledger)
<!-- Lock the SHAPE before depth. One row per top-level component that can succeed or fail independently. -->
<!-- id | outcome (one line) | status: active|deferred | evidence path -->
| runtime-host | Python debt-brain MCP runs as an always-on container service, recommended default Cloud Run, with VPS/docker-compose as fallback | active | .omo/evidence/recova-brain-supabase-mcp-deploy-v1/runtime-host.json |
| supabase-data | Supabase stores audit traces, judgment runs, auth identities, RLS-protected project/user data, and optional attachments/metadata | active | .omo/evidence/recova-brain-supabase-mcp-deploy-v1/supabase-data.json |
| mcp-contract | Public MCP surface preserves the debt-only 25-tool contract, advisory-only outputs, bearer/JWT auth boundary, and unsafe-field exclusion | active | .omo/evidence/recova-brain-supabase-mcp-deploy-v1/mcp-contract.json |
| lab-cleanup | Existing lab docs/scripts are reconciled from stale 16-tool/Vercel-era assumptions to the current 25-tool real-boundary contract | active | .omo/evidence/recova-brain-supabase-mcp-deploy-v1/lab-cleanup.json |
| production-readiness | Staging deploy, secret custody, smoke tests, trace writes, rollback notes, and local-only/no-execution guardrails are verified before any public cutover | active | .omo/evidence/recova-brain-supabase-mcp-deploy-v1/production-readiness.json |

## Open assumptions (announced defaults)
<!-- Record any default you adopt instead of asking, so the user can veto it at the gate. -->
<!-- assumption | adopted default | rationale | reversible? -->
| runtime provider | Cloud Run first | Container-native Python server, managed HTTPS/scaling, no need to force Python MCP into Supabase Edge Function limits | yes |
| Google/GCP account | use the `slit.amazing` Google account | User selected this account for Google-side deployment work | yes |
| Google Cloud project | use billing-enabled fallback `slit-497603` for current staging; keep `Recova Brain MCP` / `recova-brain-mcp` deferred until billing quota is fixed | `recova-brain-mcp` was created under `slit.amazing`, but billing link failed with cloud billing quota exceeded; `slit-497603` has billing enabled and now hosts the live staging service | yes |
| Supabase role | DB/Auth/Audit store, not MCP runtime | Existing code already writes Supabase traces; Supabase Edge Functions are TypeScript/Deno and have tight limits for long-lived server behavior | yes |
| first public endpoint | keep current lab/staging endpoint until smokes pass | Avoid breaking existing clients while replacing old lab assumptions | yes |
| auth v1 | keep bearer token for staging, prepare Supabase JWT/RLS path as next production gate | Lowest-risk continuity; service-role remains server-only | yes |
| target repo | execute final integration in Recova_source/recova-brain once branch context is confirmed | User selected recova-brain as the monorepo package name; this planning artifact is being staged from current debt-brain workspace | yes |

## Findings (cited - path:lines)
- Existing Supabase trace code already models redacted `evaluation_runs`, `judgment_runs`, and `tool_traces`: `trustgraph_legal/lab_trace.py:57-75`, `trustgraph_legal/lab_trace.py:89-127`, `trustgraph_legal/lab_trace_supabase.py:27-53`.
- Supabase writes currently use REST inserts with a server-only service role key from environment: `trustgraph_legal/lab_trace.py:178-191`, `trustgraph_legal/lab_trace_supabase.py:56-76`.
- Existing MCP container already runs the Python server on `0.0.0.0:8000`: `containers/Containerfile.mcp:24-34`.
- Existing compose deployment already passes bearer/Supabase env and binds host-local port for a reverse proxy: `deploy/recova-mcp-lab/docker-compose.yml:1-38`.
- Existing runbook says the lab is not production-ready and records Supabase trace tables: `docs/product/debt-collection-ontology/recova-mcp-lab-runbook.md:5-23`.
- Existing runbook and smoke script are stale on tool count: runbook expects 16 tools at `docs/product/debt-collection-ontology/recova-mcp-lab-runbook.md:44-50` and `docs/product/debt-collection-ontology/recova-mcp-lab-runbook.md:179-186`; smoke hardcodes `EXPECTED_TOOL_COUNT = 16` at `scripts/recova_mcp/mcp_lab_smoke.py:39`.
- Existing secret custody docs already require bearer and Supabase vars without committing real values: `docs/product/debt-collection-ontology/recova-mcp-lab-secrets.md:1-37`.
- Supabase Edge Functions are TypeScript/Deno server-side functions; current official limits include 256MB memory, paid 400s/free 150s wall-clock, 2s CPU time, and 150s request idle timeout. This supports using Edge Functions only for small proxy/webhook glue, not the Python MCP runtime.
- Cloud Run container contract requires ingress to listen on `0.0.0.0` and the configured port / `$PORT`; WebSockets are treated as long-running HTTP requests with timeout/reconnect considerations.
- Supabase RLS must be enabled for exposed-schema tables and can combine with Supabase Auth for end-to-end security.
- External sources consulted: Supabase Edge Functions, Supabase Edge Function limits, Supabase Row Level Security, Cloud Run container runtime contract, Cloud Run WebSockets.

## Decisions (with rationale)
- Recommend Cloud Run as the default Python MCP runtime host, because the repo already has a containerized server and Cloud Run matches the container contract better than Supabase Edge Functions.
- Use the `slit.amazing` Google account for Google/GCP-side deployment setup.
- Use billing-enabled Google Cloud project `slit-497603` for the current Cloud
  Run staging path. Keep newly created project `Recova Brain MCP`
  (`recova-brain-mcp`) deferred until its billing quota/linking issue is fixed.
- Recommend Supabase for Postgres/Auth/RLS/audit traces, because the repo already has Supabase trace rows and service-role write logic, and this keeps application data separate from MCP runtime lifecycle.
- Keep service-role key server-only; client/browser paths should use anon/JWT/RLS, never service-role.
- First wave should reconcile stale 16-tool lab assumptions to the current 25-tool debt-only MCP surface before deployment work.
- Production-facing deployment should preserve advisory-only semantics and must not add contact, filing, payment, seizure, public write/admin, or authoritative finance behavior.

## Scope IN
- Write a detailed executable work plan for Supabase-backed MCP deployment.
- Include lab cleanup, schema/auth/RLS work, container deployment, secret custody, smoke tests, safety scans, and final verifier waves.
- Plan for exact real-boundary checks at direct MCP and client/MCP surfaces.
- Plan agent-executable verification only; no manual “please check in dashboard” as the sole proof.

## Scope OUT (Must NOT have)
- No product code implementation during the planning gate.
- No remote deployment, DNS cutover, Supabase mutation, or secret printing during planning.
- No migration to Supabase Edge Functions as the primary Python MCP runtime.
- No public admin/write tool, debtor contact, court filing, seizure, payment demand, production ledger mutation, or authoritative balance surface.
- No committing secrets, raw OCR/legal text, real debtor PII, bearer tokens, service-role keys, local paths, or Cloudflare tokens.

## Open questions
- Approve Cloud Run as the default runtime host, or choose VPS/docker-compose/Railway/Fly instead?
- Keep `recova-mcp-lab.slit.company` as staging until smoke tests pass, or cut over an existing endpoint immediately?
- Use staging bearer auth first while preparing Supabase JWT/RLS, or require Supabase JWT verification in the first deployment wave?
- Should the final plan be written/executed in current `recova-debt-brain` first, or in the monorepo path `Recova_source/recova-brain` as the real target?
- Decide whether to keep staging in `slit-497603` or fix/migrate
  `recova-brain-mcp` before production cutover.

## Approval gate
status: plan-written-awaiting-execution-approval
Execution should begin only after the user approves the plan or overrides one of the announced defaults.
