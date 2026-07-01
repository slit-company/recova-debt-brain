# Recova MCP Client Connection Guide

Status: lab quickstart

Use this when connecting the Recova debt-brain MCP lab endpoint from an external agent client such as Hermes, Claude, ChatGPT/OpenAI-compatible MCP clients, Cursor-style MCP clients, or any generic streamable HTTP MCP runtime.

## Connection Values

Use the same values in every client:

```text
name: recova-debt-brain-lab
transport: streamable HTTP
url: https://recova-mcp-lab.slit.company/mcp
auth header: Authorization: Bearer <MCP_LAB_BEARER_TOKEN>
```

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

- Confirm the URL is exactly `https://recova-mcp-lab.slit.company/mcp`.
- Confirm the transport is streamable HTTP, not stdio.
- Confirm the auth header is exactly `Authorization: Bearer <token>`.
- Confirm the bearer token is not being sent as a tool argument.

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
  --out .omo/evidence/recova-mcp-deployment/task-11-mcp-smoke.json
```

Expected:

- `status=ok`
- `tool_count=16`
- `generic_tools=[]`
- `execution_tools=[]`
- `trace_status=recorded`
- `evaluation_status=recorded`
- `judgment_status=recorded`

## Related Docs

- `docs/product/debt-collection-ontology/recova-mcp-lab-runbook.md`
- `docs/product/debt-collection-ontology/mcp-domain-server-contract.md`
- `docs/product/debt-collection-ontology/recova-mcp-lab-secrets.md`
