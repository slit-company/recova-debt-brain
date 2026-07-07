# Recova MCP Client Connection Guide

Status: lab quickstart

Use this when connecting the Recova debt-brain MCP lab endpoint from an external agent client that can send custom MCP HTTP headers, such as Hermes, Claude Code or Desktop-style MCP runtimes, ChatGPT/OpenAI-compatible MCP clients with header support, Cursor-style MCP clients, or any generic streamable HTTP MCP runtime.

Claude web custom connectors are different: the Claude web UI does not provide a raw header field. It asks for an MCP URL and optional OAuth client credentials. The current Recova lab endpoint is a fixed Bearer-token protected MCP server, not a full OAuth authorization server, so Claude web needs an OAuth bridge before it can connect directly.

## Connection Values

Use the same values in every client:

```text
name: recova-debt-brain-lab
transport: streamable HTTP
url: https://recova-mcp-lab.slit.company/mcp
auth header: Authorization: Bearer <MCP_LAB_BEARER_TOKEN>
```

The direct Vercel origin remains available as a fallback:
`https://recova-debt-brain-lab.vercel.app/mcp`.

The bearer token belongs in the MCP HTTP connection context. Do not pass it as a tool argument.

## Generic Config Shape

Many MCP clients use a JSON shape close to this:

```json
{
  "mcpServers": {
    "recova-debt-brain-lab": {
      "transport": "streamable-http",
      "url": "https://recova-mcp-lab.slit.company/mcp",
      "headers": {
        "Authorization": "Bearer ${MCP_LAB_BEARER_TOKEN}"
      }
    }
  }
}
```

If the client UI asks for fields instead of JSON, enter:

- Server name: `recova-debt-brain-lab`
- Transport: `streamable HTTP`
- URL: `https://recova-mcp-lab.slit.company/mcp`
- Header key: `Authorization`
- Header value: `Bearer <lab token>`

Do not configure fields named `authorization`, `token`, or `bearer` inside tool arguments.

## Claude Web Status

Claude web custom connectors are blocked until the lab has OAuth-compatible auth in front of the MCP server.

Current lab auth:

```text
Authorization: Bearer <MCP_LAB_BEARER_TOKEN>
```

Claude web connector form:

```text
Name
MCP URL
OAuth client ID
OAuth client secret
```

Those fields are not a place to paste `MCP_LAB_BEARER_TOKEN`. To support Claude web, add one of these:

1. An OAuth bridge in front of the MCP endpoint that implements discovery, authorize, and token exchange, then forwards a server-side Bearer token to Recova MCP.
2. Native OAuth support in the Recova MCP server.
3. A separate no-auth or network-restricted test endpoint, only for disposable demos.

Preferred path: OAuth bridge. It keeps the MCP server's current Bearer-token boundary while giving Claude web the OAuth flow it expects.

## Codex CLI

Codex CLI can connect directly because it supports streamable HTTP MCP plus a bearer-token environment variable.

Register the server once:

```sh
codex mcp add recova-debt-brain-lab \
  --url https://recova-mcp-lab.slit.company/mcp \
  --bearer-token-env-var MCP_LAB_BEARER_TOKEN
```

Start Codex with the lab env loaded:

```sh
set -a
. /Users/cosmos/dev/ontology/trustgraph/deploy/recova-mcp-lab/.env
set +a
codex
```

Verify:

```text
Use the recova-debt-brain-lab MCP server.
Call list_debt_collection_tools and tell me how many tools are available.
```

Expected: `16` tools, matching the canonical tool list below.

The current Codex session may not hot-reload newly added MCP servers. If the server was just added, start a new Codex session or use `codex exec` after loading the env.

## First Smoke Test

After connecting, ask the client to list the MCP tools from `recova-debt-brain-lab`.

Expected result: exactly these 16 tools.

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

Generic TrustGraph tools such as `embeddings`, `load_document`, `put_config`, or `delete_kg_core` should not appear.

## First Agent Prompt

Use a small, synthetic test request before trying real case material:

```text
Use the recova-debt-brain-lab MCP server.
First call list_debt_collection_tools.
Then explain which tool should be used to check whether a debt-collection case is blocked by legal StopGates.
Do not execute any filing, contact, payment, attachment, or collection action.
```

Expected behavior:

- The agent discovers the 16 Recova tools.
- The agent selects `check_case_stop_gates` or `recommend_next_action` for legal precondition review.
- The agent treats the server as a domain brain, not an execution system.
- The agent does not invent direct filing, contact, payment, or collection tools.

## Real Case Test Pattern

For a real test packet, keep the flow narrow:

1. Ingest or classify the document with `ingest_ocr_markdown` or `classify_legal_document`.
2. Build or fetch the packet view with `extract_case_packet` or `get_case_graph`.
3. Run legal checks with `check_case_stop_gates`, `check_limitation_status`, and `check_attachment_target_rules`.
4. Ask for a non-executing recommendation with `recommend_next_action`.
5. Treat `보류` or `불가능` as a stop signal requiring review or more evidence.

The MCP server returns source refs and rule-grounded statuses. The client agent should not override those from native memory alone.

## Expected Response Contract

Every tool response should use this envelope shape:

```json
{
  "schema_version": "trustgraph-legal-mcp-tool-response/v1",
  "tool_name": "recommend_next_action",
  "group": "stopgate",
  "scope": "stopgate:recommend",
  "pii_profile": {
    "raw_text_included": false,
    "source_text_included": false
  },
  "redaction": {
    "default": "redacted",
    "raw_text_included": false,
    "source_text_included": false
  },
  "source_refs": [],
  "warnings": [],
  "result": {}
}
```

The client should read domain answers from `result` and use `source_refs` for traceability.

## Troubleshooting

If the client cannot connect:

- Confirm the URL is exactly `https://recova-mcp-lab.slit.company/mcp`
  for the current lab endpoint.
- Confirm the transport is streamable HTTP, not stdio.
- Confirm the auth header is exactly `Authorization: Bearer <token>`.
- Confirm the bearer token is not being sent as a tool argument.
- If Cloudflare returns `530` with `error code: 1033`, the client config is
  not the main problem. The old tunnel/origin path is leaking back in; check the
  Cloudflare DNS record and Worker route before rotating tokens.
- If the response has `x-recova-edge: cloudflare-worker`, traffic reached the
  current company-domain edge path.

If no-auth access succeeds, stop testing and rotate the lab token.

If the tool list is not exactly 16 tools, stop testing and compare against `docs/product/debt-collection-ontology/recova-mcp-lab-runbook.md`.

If the agent tries to file, contact, collect, attach, or mark an action complete, tell it:

```text
The Recova MCP server is a non-execution domain brain. Use it only for case structure, legal preconditions, StopGate checks, source refs, and review-safe recommendations.
```

## Local Verification From This Repo

The repo smoke test proves the same connection path without exposing the bearer token:

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
- `execution_tools=[]`
- `trace_status=not_recorded` when Supabase env is not loaded with
  `--allow-missing-trace`

## Related Docs

- `docs/product/debt-collection-ontology/recova-mcp-lab-runbook.md`
- `docs/product/debt-collection-ontology/mcp-domain-server-contract.md`
- `docs/product/debt-collection-ontology/recova-mcp-lab-secrets.md`
