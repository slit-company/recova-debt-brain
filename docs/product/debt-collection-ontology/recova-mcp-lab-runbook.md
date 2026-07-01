# Recova MCP Lab Runbook

This is the current lab handoff for the Recova debt-brain MCP endpoint.

Status: lab-ready, not production-ready.

## Live Surface

- Public MCP URL: `https://recova-mcp-lab.slit.company/mcp`
- Origin host: `mini`
- Origin process: native Python FastMCP server in `~/recova-mcp-lab`
- Origin URL: `http://127.0.0.1:8000/mcp`
- DNS path: Cloudflare Tunnel route for `recova-mcp-lab.slit.company`
- Database: Supabase project `recova-mcp-lab`
- Trace storage: Supabase `evaluation_runs`, `judgment_runs`, and `tool_traces`

The earlier candidate hostname `mcp-lab.recova.slit.company` is intentionally not the live endpoint. Cloudflare Universal SSL covers `*.slit.company`, not the deeper `*.recova.slit.company` hostname without an advanced certificate.

## Agent Connection

Use streamable HTTP MCP with bearer auth.

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

For Hermes, Claude, OpenAI/ChatGPT-compatible MCP clients, and generic MCP clients, the contract is the same:

- transport: streamable HTTP
- endpoint: `https://recova-mcp-lab.slit.company/mcp`
- auth: `Authorization: Bearer <lab token>`
- exposed tools: exactly 16 Recova debt-brain tools
- blocked surface: generic TrustGraph tools and real-world execution actions

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

## Restart

On `mini`:

```sh
cd ~/recova-mcp-lab
if [ -f recova-mcp.pid ]; then kill "$(cat recova-mcp.pid)" || true; fi
set -a
. ./.env
set +a
PYTHONPATH="$PWD/app:$PWD/app/trustgraph-base:$PWD/app/trustgraph-mcp" \
  nohup .venv/bin/python -m trustgraph.mcp_server.legal_only \
  --host 127.0.0.1 \
  --port 8000 \
  --repo-root "$PWD/app" \
  --auth-issuer "https://recova-mcp-lab.slit.company" \
  --auth-resource-url "https://recova-mcp-lab.slit.company/mcp" \
  --no-loki-enabled > recova-mcp.log 2>&1 &
echo "$!" > recova-mcp.pid
```

Then restart or reload the tunnel if needed:

```sh
launchctl kickstart -k "gui/$(id -u)/com.slit.cliproxyapi-cloudflared"
```

## Logs

```sh
ssh mini 'tail -n 120 ~/recova-mcp-lab/recova-mcp.log'
ssh mini 'tail -n 120 ~/.cloudflared/cloudflared.log'
ssh mini 'launchctl print gui/$(id -u)/com.slit.cliproxyapi-cloudflared | head -80'
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
  --out .omo/evidence/recova-mcp-deployment/task-11-mcp-smoke.json
```

Expected:

- `status=ok`
- `tool_count=16`
- `generic_tools=[]`
- `decision` is one of `가능`, `보류`, `불가능`
- `trace_status=recorded`
- `evaluation_status=recorded`
- `judgment_status=recorded`

No-auth MCP client failure:

```sh
env -u MCP_LAB_BEARER_TOKEN /opt/homebrew/bin/python3 scripts/recova_mcp/mcp_lab_smoke.py \
  --url https://recova-mcp-lab.slit.company/mcp \
  --out .omo/evidence/recova-mcp-deployment/task-11-no-auth.json \
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

PII-shaped inserts should be rejected or redacted:

- `.omo/evidence/recova-mcp-deployment/task-10-rls-deny.txt`

## Token Rotation

1. Generate a new `MCP_LAB_BEARER_TOKEN`.
2. Update `~/recova-mcp-lab/.env` on `mini`.
3. Update the local ignored file `deploy/recova-mcp-lab/.env`.
4. Restart the MCP process.
5. Rerun `scripts/recova_mcp/check_lab_env.sh --redacted`.
6. Rerun the authenticated and unauthenticated MCP smokes.

If a Supabase service key is exposed, rotate it in Supabase, update server/local `.env`, then rerun the Supabase trace smoke.

## Rollback

Dry-run the rollback plan:

```sh
scripts/recova_mcp/rollback_lab.sh --dry-run
```

Rollback defaults:

- stop the native MCP process on `mini`
- remove or disable the `recova-mcp-lab.slit.company` Cloudflare Tunnel ingress
- remove the DNS route from Cloudflare after review
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
