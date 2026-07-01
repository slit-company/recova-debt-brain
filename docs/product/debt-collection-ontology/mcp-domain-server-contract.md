# Debt Collection MCP Domain Server Contract

Status: v0 implementation contract
Domain: `recova-debt-collection`
Logical MCP surface: `debt-collection-brain-mcp`
Physical server: existing `trustgraph-mcp` server with debt-collection tools registered into the same FastMCP instance

## Purpose

The debt-collection MCP domain server is an agent-agnostic domain brain. It lets any MCP-capable client ask for source-grounded case structure, legal StopGate status, governance state, and review-safe next-action recommendations without understanding the raw TrustGraph graph shape.

The server is not a user interface and is not an execution system. It returns contracts, source refs, risk states, preconditions, review items, and recommendations. It must not file documents, contact debtors, collect funds, mutate external business systems, or claim final legal representation.

## Public Python Surface

The implementation exposes a domain facade that is importable without the global MCP SDK:

```python
from trustgraph_legal.mcp_domain import TOOL_DEFINITIONS, list_tools, invoke_tool
```

The existing MCP package registers the facade through a thin adapter:

```python
from trustgraph.mcp_server.legal_tools import register_debt_collection_brain_tools
```

Production registration passes the existing MCP auth-context resolver:

```python
register_debt_collection_brain_tools(self.mcp, token_resolver=require_token)
```

Registered tool functions accept `arguments` only. Bearer tokens are not tool arguments and must not appear in model/tool payloads.

## Runtime Dependency

`trustgraph-mcp/pyproject.toml` declares the `mcp` package dependency. The repository verification environment used for v0 does not globally provide that package, so automated Todo 9 and Todo 10 checks exercise the domain facade and fake-MCP adapter without requiring a live MCP SDK import.

For a real streamable HTTP MCP server smoke, create a runtime environment that installs `trustgraph-mcp` dependencies, then run:

```bash
PYTHONPATH=trustgraph-mcp:trustgraph-base:. python3 -m trustgraph.mcp_server.mcp \
  --host 127.0.0.1 \
  --port 8000 \
  --websocket-url ws://api-gateway:8088/api/v1/socket \
  --pubsub-backend pulsar \
  --pulsar-host pulsar://pulsar:6650
```

Client requests must send an HTTP `Authorization: Bearer ...` header. The MCP server validates the token through the TrustGraph gateway WebSocket, resolves the caller identity with `whoami`, then asks IAM for debt-collection tool-scope decisions through the internal request/response client. `authorise-many` is not sent through the gateway's public WebSocket operation registry. The gateway remains the source of truth for identity, and IAM remains the source of truth for permissions.

## Generic MCP Client Config

The exact client syntax depends on the client runtime. A generic streamable HTTP configuration should carry the server URL and bearer header outside the tool arguments:

```json
{
  "mcpServers": {
    "debt-collection-brain": {
      "transport": "streamable-http",
      "url": "http://127.0.0.1:8000/mcp",
      "headers": {
        "Authorization": "Bearer ${TRUSTGRAPH_TOKEN}"
      }
    }
  }
}
```

Do not configure any tool argument named `authorization`, `token`, or `bearer`.

## Tool Groups

| Group | Boundary |
| --- | --- |
| `read` | Read-only descriptions and summaries. |
| `ingest` | Dry-run or review-safe ingest status and registry preparation. |
| `graph` | Classification, extraction projection, and case graph access. |
| `stopgate` | Legal/compliance precondition checks and non-executing recommendations. |
| `governance` | Review-safe fact decisions, ontology candidates, and reprocess plans. |

There is no v0 public `admin` tool group in the corrected 16-tool contract.

## Canonical Tool List

| Tool | Group | Scope | Arguments |
| --- | --- | --- | --- |
| `list_debt_collection_tools` | `read` | `read:tools` | none |
| `ingest_legal_document` | `ingest` | `ingest:documents` | `zip_path`, `workspace`, `collection`, `limit` |
| `ingest_ocr_markdown` | `ingest` | `ingest:documents` | `markdown_text`, `document_id`, `source_ref`, `document_type` |
| `get_ingest_status` | `ingest` | `ingest:ingest-status` | `document_id`, `processing_id` |
| `classify_legal_document` | `graph` | `graph:document-classification` | `text`, `document_id`, `source_ref` |
| `extract_case_packet` | `graph` | `graph:case` | `text`, `manifest_path`, `document_id`, `document_type` |
| `get_case_graph` | `graph` | `graph:case` | `manifest_path`, `case_graph` |
| `check_case_stop_gates` | `stopgate` | `stopgate:check` | `case_graph`, `case_graph_path`, `manifest_path` |
| `check_limitation_status` | `stopgate` | `stopgate:check` | `case_graph`, `case_graph_path`, `manifest_path` |
| `check_attachment_target_rules` | `stopgate` | `stopgate:check` | `case_graph`, `case_graph_path`, `manifest_path` |
| `summarize_case_ledger` | `read` | `read:ledger` | `case_graph`, `case_graph_path`, `manifest_path` |
| `recommend_next_action` | `stopgate` | `stopgate:recommend` | `case_graph`, `case_graph_path`, `manifest_path` |
| `list_unknown_document_types` | `governance` | `governance:review` | `manifest_path` |
| `review_extracted_fact` | `governance` | `governance:review` | `fact_id`, `decision`, `reviewer`, `reason` |
| `promote_ontology_candidate` | `governance` | `governance:review` | `candidate_id`, `approval_metadata`, `ontology_path` |
| `reprocess_case` | `governance` | `governance:reprocess` | `case_packet_id`, `manifest_path` |

Tool contract metadata is returned by `list_debt_collection_tools` and `list_tools()` with schema version `trustgraph-legal-mcp-tool-contract/v1`.

## Response Envelope

Every tool response uses schema version `trustgraph-legal-mcp-tool-response/v1` and must include:

```json
{
  "schema_version": "trustgraph-legal-mcp-tool-response/v1",
  "tool_name": "check_case_stop_gates",
  "group": "stopgate",
  "scope": "stopgate:check",
  "pii_profile": {
    "raw_text_included": false,
    "source_text_included": false,
    "redacted": {
      "national_id": 0,
      "phone": 0,
      "account": 0,
      "address": 0
    }
  },
  "redaction": {
    "status": "redacted",
    "default": "redacted",
    "raw_text_included": false,
    "source_text_included": false
  },
  "source_refs": [],
  "warnings": [],
  "result": {}
}
```

Clients must read domain payloads from `result`. They must not depend on ad hoc top-level fields outside the envelope.

## Decision Contract

StopGate tools return Korean decision values:

| Decision | Meaning | Client behavior |
| --- | --- | --- |
| `가능` | No current StopGate blocks the advisory path. | Client may prepare a non-executing advisory package and still preserve source refs. |
| `보류` | Evidence is missing, conflicting, or legally risky. | Client must stop execution and request review, evidence, or reprocessing. |
| `불가능` | The curated rules or reviewed facts block the requested legal path. | Client must not recommend action except remediation or legal review. |

`recommend_next_action` is still non-executing. In the fixture evaluation it returns `hold_for_review` because StopGates remain open.

## Source Refs

Material graph facts and StopGate decisions must be source-backed. `source_refs` are pointers, not raw OCR text:

```json
{
  "document_id": "legal-ocr-synth-asset-evidence-001",
  "source_ref": "fixture:tests/fixtures/legal-ocr/snippets/asset_evidence.md",
  "chunk_id": "line-12",
  "line_start": 12,
  "line_end": 12,
  "confidence": 0.84,
  "fact_type": "legal-check"
}
```

Default source refs must not include raw excerpts, raw OCR text, national identifiers, phone numbers, account numbers, or full addresses.

## Redaction Policy

Default outputs must keep:

- `pii_profile.raw_text_included = false`
- `pii_profile.source_text_included = false`
- `redaction.default = redacted`
- `redaction.status = redacted`

Path inputs are bounded to `repo_root`. Absolute or traversal paths outside that root return:

```json
{
  "status": "rejected",
  "reason": "path_outside_repo_root"
}
```

The rejection must not echo the attempted path or file contents.

## Hybrid Case Identity

The server owns `case_packet_id` resolution. Clients may send hints, but must treat the server response as the packet identity boundary.

Evidence keys include:

- `court_case_number`
- `claim_id`
- `enforcement_title_id`
- `party_identity_key`
- `document_hash`

No client may merge cases or parties on a display name alone. If a client memory entry conflicts with the server case graph, the server graph and its source refs win until governance review changes the graph.

## Curated Rule Sources

StopGate behavior is backed by curated, versioned v0 rule sources under `resources/legal_rules/`. Rule refs must carry rule IDs, statute refs when available, effective dates, and approval status.

Client agents must not treat live web search, native memory, or free-form LLM legal analysis as a production rule source. New or changed legal rules must enter governance review and reprocessing before they affect production recommendations.

## Memory Conflict Policy

If an agent's native memory disagrees with the MCP domain server:

1. Prefer the MCP response when it has source refs and rule refs.
2. If the agent has newer evidence, ingest it or create a review item instead of overriding the graph locally.
3. If the MCP response is missing evidence, use `reprocess_case`, `review_extracted_fact`, or governance tools.
4. Do not clear StopGates from native memory alone.
5. Do not store legal rules only in agent memory.

## Failure States

| State | Meaning |
| --- | --- |
| `unknown_tool` | Requested tool is not in the 16-tool contract. |
| `path_outside_repo_root` | Public path argument points outside the allowed repository root. |
| `not_configured` | A production backend is not attached to the v0 domain tool layer. |
| `queued_for_review` | Write-like request is recorded as review-safe intent, not a production mutation. |
| `planned` | Reprocess plan is returned without starting a production job. |
| `rejected` | Request failed a contract or governance precondition. |

## Non-Execution Boundary

These tools must never:

- file or submit court documents
- contact debtors, guarantors, courts, banks, employers, insurers, or registries
- initiate attachment, seizure, settlement, payment, transfer, or collection
- mark a legal/business action as completed
- claim final legal advice or representation

A direct execution request must be blocked. The v0 evaluation probes a nonexistent direct filing tool and expects `unknown_tool`.

## Evaluation

Run the fixture packet evaluation:

```bash
/opt/homebrew/bin/python3 scripts/legal_ontology/evaluate_packet.py \
  --fixtures tests/fixtures/legal-ocr/manifest.json \
  --out .omo/evidence/debt-collection-ontology/task-10-eval.json
```

Expected summary:

```json
{
  "status": "passed",
  "tool_count": 16,
  "decision": "보류",
  "recommendation": "hold_for_review",
  "failure_probe": "unknown_tool",
  "issues": []
}
```

This evaluation is the hermetic contract proof for environments where the global MCP SDK is not installed.
