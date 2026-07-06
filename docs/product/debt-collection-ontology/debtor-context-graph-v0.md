# Debtor Context Graph v0

Status: v0 operator/developer contract
Primary code: `trustgraph_legal.document_assembly`, `trustgraph_legal.debtor_context`, `trustgraph_legal.route_candidates`, `trustgraph_legal.mcp_domain`, `trustgraph_legal.debtor_governance`
Evidence root: `.omo/evidence/debtor-context-graph-v0/`

## Purpose

Debtor Context Graph v0 turns page-level OCR into a redacted, source-backed graph that can answer one question safely: what do we know about this debtor or receivables packet, and which advisory collection routes are currently possible, missing evidence, or blocked?

It does not file documents, contact debtors, collect money, mutate production legal resources, or expose raw OCR text. The graph is an evidence and decision-support contract for agents and services.

## Graph Model

The logical `DebtorContextGraph` is implemented as `DebtorGraphPayload`.

```text
OCR page files
  -> DocumentPage
  -> DocumentAssembly
  -> DebtorGraphPayload
  -> GraphSnapshot
  -> RouteCandidate
  -> DebtorGovernancePayload
```

The pipeline starts with page-level markdown or text. `DocumentAssemblyPayload` groups pages into documents and records page order, source refs, source hashes, review status, and sensitive-shape counts without storing page text in JSON output. `build_debtor_context` then creates:

| Object | What it means | Important fields |
| --- | --- | --- |
| `DocumentPage` | One OCR page known to the graph. | `page_id`, `source_ref`, `source_hash`, `relative_path`, `classifier_document_type`, `review_status` |
| `DocumentAssembly` | A deterministic document grouping over pages. | `assembly_id`, `document_id`, `canonical_document_type`, `page_ids`, `source_refs`, `confidence`, `review_status` |
| `FactAssertion` | One source-backed fact extracted or derived from a page/document. | `fact_id`, `predicate`, `object_value`, `confidence`, `source_refs`, `source_hash`, `chunk_id`, `review_status`, `derived` |
| `GraphSnapshot` | Stable replay/provenance boundary for the graph. | `graph_snapshot_id`, `source_bundle_hash`, extractor/ontology/route versions, included fact and route ids |
| `RouteCandidate` | One advisory route template evaluated against graph facts and rule sources. | `route_id`, `status`, `required_facts`, `missing_facts`, `blocking_facts`, `legal_source_refs`, `no_direct_execution` |
| `DebtorGovernancePayload` | Service-side review records for graph and route risk. | `records`, `production_*_modified = false`, `pii_profile` |

Every `FactAssertion` must have a non-placeholder `source_ref`. The builder rejects placeholder refs such as `todo`, `unknown`, or `placeholder:*` so a graph cannot silently depend on unsourced facts.

Identity resolution is deliberately conservative. If debtor identity evidence exists, the graph records an `identity_evidence_hash`. If not, it uses a source-bundle fallback and emits an `identity_unresolved` review item. A display name alone is not enough to merge debtor context across source bundles.

## CLI Usage

Run all commands from the repository root.

### Assemble OCR Pages

Use this when you want a full DocumentAssembly JSON file that can later feed the graph builder.

```bash
python3 -m trustgraph_legal.document_assembly \
  --ocr-root tests/fixtures/legal-ocr-pages \
  --repo-root . \
  --out .omo/evidence/debtor-context-graph-v0/task-14-document-assembly.json
```

For a PII-safe aggregate only:

```bash
python3 -m trustgraph_legal.document_assembly \
  --ocr-root tests/fixtures/legal-ocr-pages \
  --repo-root . \
  --summary-only \
  --out .omo/evidence/debtor-context-graph-v0/task-14-document-assembly-summary.json
```

The graph CLI requires full assembly JSON. Summary-only assembly JSON is intentionally rejected because it omits pages and assemblies.

### Build a Full Synthetic Debtor Graph

```bash
python3 -m trustgraph_legal.debtor_context \
  --ocr-root tests/fixtures/legal-ocr-pages \
  --repo-root . \
  --route-resources resources/legal_routes/debt_collection_routes_v0.json \
  --legal-sources resources/legal_rules/debt_collection_route_sources_v0.json \
  --out .omo/evidence/debtor-context-graph-v0/task-14-synthetic-full-graph.json
```

Expected stdout is a compact JSON summary with `debtor_graph_id`, `evidence`, `route_candidates`, and `summary_only`.

### Build from a Saved Assembly

```bash
python3 -m trustgraph_legal.debtor_context \
  --assembly .omo/evidence/debtor-context-graph-v0/task-14-document-assembly.json \
  --repo-root . \
  --route-resources resources/legal_routes/debt_collection_routes_v0.json \
  --legal-sources resources/legal_rules/debt_collection_route_sources_v0.json \
  --out .omo/evidence/debtor-context-graph-v0/task-14-synthetic-from-assembly.json
```

Exactly one of `--ocr-root` or `--assembly` is required. Passing both, passing neither, or passing a missing OCR root exits with code `2` and writes a controlled `error:` line to stderr.

### Build a PII-Safe Real OCR Summary

Use summary mode for real OCR material. Real OCR paths stay local and operator-provided; do not write full local corpus paths into docs, examples, committed evidence, or MCP payloads. Do not commit full real OCR graph outputs.

```bash
export RECOVA_REAL_OCR_ROOT=<redacted-real-ocr-root>

python3 -m trustgraph_legal.debtor_context \
  --ocr-root "$RECOVA_REAL_OCR_ROOT" \
  --repo-root . \
  --summary-only \
  --limit 3 \
  --out .omo/evidence/debtor-context-graph-v0/task-14-real-ocr-summary.json
```

Summary output includes counts, route status counts, snapshot replay id, and provenance validity. It omits `document_pages`, `document_assemblies`, `fact_assertions`, and raw OCR text.

## MCP Debtor Graph Tools

The MCP domain facade is importable without the global MCP SDK:

```python
from trustgraph_legal.mcp_domain import invoke_tool, list_tools
```

Current v0 exposes 21 tools: the existing 16 debt-collection tools plus five additive `debtor_graph` tools.

| Tool | Scope | Arguments | Use |
| --- | --- | --- | --- |
| `assemble_debtor_documents` | `debtor_graph:assembly` | `ocr_root`, `summary_only` | Build DocumentAssembly JSON from OCR pages. |
| `build_debtor_context_graph` | `debtor_graph:build` | `ocr_root`, `assembly_path`, `route_resources`, `legal_sources` | Build a full redacted graph and advisory routes. |
| `get_debtor_graph_snapshot` | `debtor_graph:read` | `graph`, `graph_path`, `ocr_root`, `assembly_path` | Return snapshot replay and provenance metadata. |
| `list_debtor_route_candidates` | `debtor_graph:routes` | `graph`, `graph_path`, `ocr_root`, `assembly_path` | List route candidates already attached to a graph. |
| `explain_debtor_route_candidate` | `debtor_graph:routes` | `graph`, `graph_path`, `ocr_root`, `assembly_path`, `route_id` | Explain one route candidate, including missing and blocking facts. |

Example SDK-free smoke:

```bash
python3 - <<'PY'
from pathlib import Path
from trustgraph_legal.mcp_domain import invoke_tool

root = Path.cwd()
graph = invoke_tool(
    "build_debtor_context_graph",
    {"ocr_root": "tests/fixtures/legal-ocr-pages"},
    root,
)
routes = invoke_tool("list_debtor_route_candidates", {"graph": graph["result"]}, root)
explain = invoke_tool(
    "explain_debtor_route_candidate",
    {"graph": graph["result"], "route_id": "bank_account_attachment"},
    root,
)

print(routes["result"]["route_count"])
print(explain["result"]["status"])
print(graph["pii_profile"]["raw_text_included"])
PY
```

Tool authentication is context-only. Public tool arguments must not include `authorization`, `token`, or `bearer`. Path arguments are bounded to the repo root. An absolute or traversal path outside the repo returns:

```json
{"status": "rejected", "reason": "path_outside_repo_root"}
```

The rejection does not echo the attempted path or file contents.

## Route Status Semantics

Route candidates are advisory. They never authorize execution and always set `no_direct_execution = true`.

| Route status | Meaning | Operator behavior |
| --- | --- | --- |
| `possible` | Required fact handles are present, no blocking handles were found, and legal source metadata is approved for v0 use. | Prepare a non-executing advisory packet with source refs. Still preserve review trail. |
| `missing_facts` | One or more required fact handles are absent. | Collect more evidence, re-run OCR/assembly, or add reviewed facts. |
| `review_required` | A blocker, low-review fact, global StopGate reason, unapproved/future legal source, or route review state needs human/service review. | Stop route recommendation until review or reprocessing clears the condition. |
| `blocked` | A blocking fact handle is present and is not merely a review marker. | Do not recommend the route except as a remediation/review item. |

The older StopGate tools return Korean decision values `가능`, `보류`, and `불가능`. The debtor route layer uses the English statuses above and includes StopGate reason codes in `blocking_facts` when they affect a route.

Route templates live in `resources/legal_routes/debt_collection_routes_v0.json`. Legal source metadata lives in `resources/legal_rules/debt_collection_route_sources_v0.json`. v0 currently has 18 route templates and 18 legal source entries. Source refs include law id, MST, article, effective date, retrieval status, and review status.

## Governance Hooks

Governance is service-side. It records review work; it does not mutate production ontology, routes, legal sources, or graph facts.

```python
from trustgraph_legal.debtor_governance import (
    ManualFactReviewDecision,
    build_debtor_governance_payload,
)
```

`build_debtor_governance_payload(graph, manual_decisions=())` emits records for:

| Record kind | Trigger |
| --- | --- |
| `unknown_assembly` | A document assembly has canonical type `unknown`. |
| `identity_unresolved` | The graph lacks debtor identity evidence. |
| `conflicting_fact_signal` | Multiple source-backed values exist for the same predicate. |
| `blocked_route` | A route candidate is blocked. |
| `route_review_required` | A route candidate needs review. |
| `legal_source_review` | Route legal-source metadata is missing, future, draft, deprecated, or otherwise review-marked. |
| `manual_fact_review` | A service records a manual fact decision. |

Manual approvals must include `approval_evidence_ref`. If an approval-like decision omits that reference, v0 records `missing_manual_fact_approval_metadata` and marks the manual decision as rejected.

All governance payloads include:

```json
{
  "production_resources_modified": false,
  "production_ontology_modified": false,
  "production_routes_modified": false,
  "production_legal_sources_modified": false,
  "pii_profile": {
    "raw_text_included": false,
    "source_text_included": false
  }
}
```

## Redaction and No Raw OCR Policy

Default CLI and MCP outputs must keep:

```json
{
  "raw_text_included": false,
  "source_text_included": false
}
```

For MCP envelopes this appears under both `pii_profile` and `redaction`:

```json
{
  "pii_profile": {
    "raw_text_included": false,
    "source_text_included": false
  },
  "redaction": {
    "status": "redacted",
    "default": "redacted",
    "raw_text_included": false,
    "source_text_included": false
  }
}
```

Allowed evidence pointers:

- `source_ref`
- `source_refs`
- `source_hash`
- `source_document_id`
- `chunk_id`
- line numbers
- route/legal source ids
- graph and snapshot ids

Do not commit raw real OCR text, excerpts, national identifiers, phone numbers, account numbers, full addresses, or full local real-OCR graph outputs. For real OCR, use `--summary-only` and bounded `--limit` evidence unless a reviewed redaction gate explicitly approves more.

## Evidence Paths

Task evidence for this rollout is under `.omo/evidence/debtor-context-graph-v0/`.

Important upstream evidence:

| Path | What it proves |
| --- | --- |
| `task-2-document-assembly-happy.json` | Document assembly happy path. |
| `task-3-fixture-ocr-pages-summary.json` | Synthetic OCR page fixture shape. |
| `task-6-debtor-graph-happy.json` | Debtor graph builder happy path. |
| `task-7-snapshot-diff-happy.json` | Snapshot replay/diff/provenance path. |
| `task-8-routes-happy.json` | Route candidate matcher output. |
| `task-9-legal-route-happy.json` | Route legal-source/StopGate integration. |
| `task-10-synthetic-full-graph.json` | End-to-end synthetic CLI graph. |
| `task-10-real-ocr-debtor-summary.json` | Real OCR summary-only graph output. |
| `task-11-mcp-happy.json` | Additive MCP debtor graph happy path. |
| `task-11-mcp-path-failure.json` | Repo-root path rejection. |
| `task-12-governance-happy.json` | Governance hook happy path. |
| `task-12-manual-rejection.json` | Manual approval missing evidence rejection. |

Task 14 evidence:

| Path | What it proves |
| --- | --- |
| `task-14-docs-smoke.txt` | Documented CLI and MCP commands run against the synthetic fixture. |
| `task-14-docs-pii.txt` | Documentation and task-14 evidence do not contain raw OCR or common sensitive shapes. |

## Known Limitations

- Real OCR input is still page-oriented. v0 can assemble deterministic page fixtures, but production-quality document and episode assembly will need more corpus-specific review.
- The graph is local and deterministic. It does not persist snapshots to Supabase, TrustGraph storage, or a remote graph database in v0.
- Route candidates are not route rankings. They are status-bearing advisory candidates over extracted fact handles and curated legal-source metadata.
- Fact extraction is intentionally narrow. If a handle is missing, the route becomes `missing_facts` even when a human could infer the fact from raw documents.
- Identity merge is conservative. Without identity evidence, the graph uses source-bundle fallback and emits governance review work.
- Live MCP server smoke requires the `trustgraph-mcp` runtime dependencies. The domain facade and fake MCP adapter tests do not require a global `mcp` package.
- Legal rule sources are curated static v0 resources. Live law crawling, future-effective law selection, and production legal-source promotion are governance tasks, not automatic behavior.
- No v0 tool performs legal execution. Any UI or agent using this graph must treat `possible` as "may prepare reviewed advisory material", not as permission to execute.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `error: input: provide exactly one of --ocr-root or --assembly` | Both inputs were passed, or neither was passed. | Pass exactly one source. |
| `error: <path>: OCR root not found` | The OCR root path does not exist from the repo root. | Use `tests/fixtures/legal-ocr-pages` for local smoke, or an absolute real OCR root. |
| `full DocumentAssembly JSON is required` | A summary-only assembly JSON was passed to the graph CLI. | Build full assembly JSON without `--summary-only`. |
| MCP returns `path_outside_repo_root` | A path argument resolved outside the registered repo root. | Use repo-relative fixture paths or files under the repo root. |
| Route is `missing_facts` | The graph lacks required fact handles for that route. | Collect evidence, re-run assembly/graph build, or add reviewed facts through service-side governance. |
| Route is `review_required` | A blocker, source review state, low-review fact, or StopGate reason needs review. | Use governance records to decide what evidence or approval is missing. |
