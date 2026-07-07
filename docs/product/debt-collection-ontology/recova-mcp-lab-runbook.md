# Recova MCP Lab Runbook

This is the current lab handoff for the Recova debt-brain MCP endpoint.

Status: lab-ready, not production-ready.

## Live Surface

- Active public MCP URL: `https://recova-mcp-lab.slit.company/mcp`
- Direct origin/fallback MCP URL: `https://recova-debt-brain-lab.vercel.app/mcp`
- Current edge path: Cloudflare Worker `recova-mcp-lab-proxy` route
  `recova-mcp-lab.slit.company/*`.
- Current origin host: Vercel serverless endpoint wrapping `trustgraph_legal.mcp_domain`.
- Preferred future durable origin host: always-on Linux VPS, not the retired Mac mini.
- Origin process: Docker Compose service `recova-mcp` plus Caddy reverse proxy.
- Internal MCP URL: `http://recova-mcp:8000/mcp` inside the Compose network.
- Host-local MCP URL: `http://127.0.0.1:8000/mcp` on the VPS.
- DNS path: Cloudflare proxied `CNAME` record for `recova-mcp-lab.slit.company`
  targeting `cname.vercel-dns.com`; Cloudflare Worker route handles requests
  before origin fallback.
- Database: Supabase project `recova-mcp-lab`
- Trace storage: Supabase `evaluation_runs`, `judgment_runs`, and `tool_traces`

The earlier candidate hostname `mcp-lab.recova.slit.company` is intentionally not the live endpoint. Cloudflare Universal SSL covers `*.slit.company`, not the deeper `*.recova.slit.company` hostname without an advanced certificate.

## Agent Connection

Use streamable HTTP MCP with bearer auth.

For a client-focused quickstart, see
`docs/product/debt-collection-ontology/recova-mcp-client-guide.md`.

```json
{
  "name": "recova-debt-brain-lab",
  "type": "streamable_http",
  "url": "https://recova-mcp-lab.slit.company/mcp",
  "headers": {
    "Authorization": "Bearer ${MCP_LAB_BEARER_TOKEN}"
  }
}
```

For Hermes, Claude Code or Desktop-style runtimes, OpenAI/ChatGPT-compatible MCP clients with custom header support, and generic MCP clients, the contract is the same:

- transport: streamable HTTP
- endpoint: `https://recova-mcp-lab.slit.company/mcp`
- auth: `Authorization: Bearer <lab token>`
- exposed tools: exactly 16 Recova debt-brain tools
- blocked surface: generic TrustGraph tools and real-world execution actions

Claude web custom connectors do not currently fit this Bearer-header quickstart because the Claude web UI asks for OAuth client credentials rather than arbitrary HTTP headers. Use an OAuth bridge before connecting Claude web.

Never pass `authorization`, `token`, or `bearer` as a tool argument. Auth belongs in the MCP HTTP context only.

## Expected Tool Surface

The public lab endpoint should expose only these tools:

```text
list_debt_collection_tools
ingest_legal_document
ingest_ocr_markdown
get_ingest_status
classify_legal_document
extract_case_packet
get_case_graph
check_case_stop_gates
check_limitation_status
check_attachment_target_rules
summarize_case_ledger
recommend_next_action
list_unknown_document_types
review_extracted_fact
promote_ontology_candidate
reprocess_case
```

Generic TrustGraph tools such as `embeddings`, `put_config`, `load_document`, and `delete_kg_core` must not be exposed from the lab endpoint.

## VPS Bootstrap

Bootstrap a fresh Ubuntu/Debian VPS once:

```sh
scp deploy/recova-mcp-lab/bootstrap_vps_ubuntu.sh root@<vps-ip>:/tmp/
ssh root@<vps-ip> 'sh /tmp/bootstrap_vps_ubuntu.sh'
```

The bootstrap installs Docker Compose, opens SSH/HTTP/HTTPS with `ufw`, and
creates `/opt/recova-mcp-lab`.

## Deploy Or Restart

From this repo:

```sh
set -a
. deploy/recova-mcp-lab/.env
set +a
scripts/recova_mcp/deploy_vps.sh user@<vps-ip-or-hostname>
```

The deploy script:

- verifies required lab env without printing secret values;
- copies the repo to `/opt/recova-mcp-lab/app`;
- copies the ignored lab `.env` separately;
- runs `docker compose -f deploy/recova-mcp-lab/docker-compose.yml up -d --build`;
- prints the remote Compose service status.

Use `root@<vps-ip>` for the first deployment unless another SSH user already
has write access to `/opt/recova-mcp-lab` and Docker permissions.

Manual restart on the VPS:

```sh
ssh user@<vps-ip-or-hostname> \
  'cd /opt/recova-mcp-lab/app && docker compose -f deploy/recova-mcp-lab/docker-compose.yml --env-file deploy/recova-mcp-lab/.env up -d --build'
```

## DNS And Edge

The old Cloudflare Tunnel-backed record has been replaced. Keeping that dead
tunnel route caused Cloudflare `530` / `error code: 1033`.

Current live path:

1. Cloudflare DNS has `recova-mcp-lab.slit.company` as a proxied `CNAME` to
   `cname.vercel-dns.com`.
2. Cloudflare Worker `recova-mcp-lab-proxy` is deployed from
   `deploy/cloudflare-mcp-proxy/`.
3. The Worker route `recova-mcp-lab.slit.company/*` forwards requests to
   `https://recova-debt-brain-lab.vercel.app`.
4. Vercel remains the current origin until a VPS is provisioned.

If moving to a VPS later, point the Worker upstream at the VPS hostname or
replace the Worker route with a reviewed `A` / `AAAA` DNS cutover and rerun the
health checks below.

The public MCP URL should not change for clients.

## Logs

```sh
ssh user@<vps-ip-or-hostname> \
  'cd /opt/recova-mcp-lab/app && docker compose -f deploy/recova-mcp-lab/docker-compose.yml logs --tail=120 recova-mcp'
ssh user@<vps-ip-or-hostname> \
  'cd /opt/recova-mcp-lab/app && docker compose -f deploy/recova-mcp-lab/docker-compose.yml logs --tail=120 caddy'
ssh user@<vps-ip-or-hostname> \
  'cd /opt/recova-mcp-lab/app && docker compose -f deploy/recova-mcp-lab/docker-compose.yml ps'
```

Do not paste `.env`, bearer tokens, Supabase keys, Cloudflare tokens, raw legal text, or full OCR text into logs, reports, or issue descriptions.

## Health Checks

Missing auth should be rejected:

```sh
curl -i https://recova-mcp-lab.slit.company/mcp
```

Expected: HTTP auth rejection, not TLS failure or host rejection.

Full MCP smoke from the repo:

```sh
set -a
. deploy/recova-mcp-lab/.env
set +a
/opt/homebrew/bin/python3 scripts/recova_mcp/mcp_lab_smoke.py \
  --url https://recova-mcp-lab.slit.company/mcp \
  --token-env MCP_LAB_BEARER_TOKEN \
  --out .omo/evidence/recova-mcp-deployment/cloudflare-worker-mcp-smoke.json \
  --allow-missing-trace
```

Expected:

- `status=ok`
- `tool_count=16`
- `generic_tools=[]`
- `decision` is one of `가능`, `보류`, `불가능`
- `trace_status=not_recorded` when Supabase env is not loaded with
  `--allow-missing-trace`

No-auth MCP client failure:

```sh
env -u MCP_LAB_BEARER_TOKEN /opt/homebrew/bin/python3 scripts/recova_mcp/mcp_lab_smoke.py \
  --url https://recova-mcp-lab.slit.company/mcp \
  --out .omo/evidence/recova-mcp-deployment/cloudflare-worker-mcp-no-auth.json \
  --expect-auth-failure
```

## Supabase Evidence

The lab uses Supabase as memory and evaluation storage, not as the MCP runtime.

Remote migration proof:

- `.omo/evidence/recova-mcp-deployment/task-10-db-push.txt`
- `.omo/evidence/recova-mcp-deployment/task-10-table-check.json`

Trace and judgment proof:

- `.omo/evidence/recova-mcp-deployment/task-10-trace-insert.json`
- `.omo/evidence/recova-mcp-deployment/task-10-trace-count.json`
- `.omo/evidence/recova-mcp-deployment/task-11-mcp-smoke.json`
- `.omo/evidence/recova-mcp-deployment/cloudflare-worker-mcp-smoke.json`
- `.omo/evidence/recova-mcp-deployment/cloudflare-worker-mcp-no-auth.json`

PII-shaped inserts should be rejected or redacted:

- `.omo/evidence/recova-mcp-deployment/task-10-rls-deny.txt`

## Token Rotation

1. Generate a new `MCP_LAB_BEARER_TOKEN`.
2. Update `deploy/recova-mcp-lab/.env` locally.
3. Update the Vercel `MCP_LAB_BEARER_TOKEN` environment variable for
   `recova-debt-brain-lab`, then redeploy the Vercel origin.
4. If the VPS origin is active instead, redeploy with
   `scripts/recova_mcp/deploy_vps.sh user@<vps-ip-or-hostname>`.
5. Rerun `scripts/recova_mcp/check_lab_env.sh --redacted`.
6. Rerun the authenticated and unauthenticated MCP smokes.

If a Supabase service key is exposed, rotate it in Supabase, update server/local `.env`, then rerun the Supabase trace smoke.

## Rollback

Dry-run the rollback plan:

```sh
scripts/recova_mcp/rollback_lab.sh --dry-run
```

Rollback defaults:

- stop the VPS Docker Compose stack
- snapshot `/opt/recova-mcp-lab/app` before deletion
- remove or disable the `recova-mcp-lab.slit.company` Cloudflare Worker route
  and DNS record after review
- preserve Supabase evidence unless the user explicitly requests a purge
- rotate exposed credentials if the rollback was caused by leakage

## Promotion Criteria

Promote from lab to stable only after all of these are true:

- live MCP smoke remains green for multiple fixture packs
- tool trace and judgment rows are useful enough for tuning
- human corrections can be reviewed without raw PII exposure
- StopGate decisions show stable failure labels and source refs
- no generic TrustGraph tools are visible from the public endpoint
- no execution/contact/payment/filing action exists in the public tool surface

## Evidence Bundle

Primary evidence root:

```text
.omo/evidence/recova-mcp-deployment/
```

Team reports:

```text
.omo/teams/team-89938d95/artifacts/A-preflight-baseline-report.md
.omo/teams/team-89938d95/artifacts/B-dns-authority-report.md
.omo/teams/team-89938d95/artifacts/C-supabase-schema-report.md
```

Current live smoke:

```text
.omo/evidence/recova-mcp-deployment/task-11-mcp-smoke.json
```
