# A Preflight Baseline Report

Member: A / preflight-baseline  
Thread: codex://threads/019f1def-0dfc-7e23-a9ae-5eec8a8dfe23  
Scope: Todo 1 from `.omo/plans/recova-mcp-deployment.md`  
Mode: evidence-only; no DNS, Supabase, server, source, or deployment mutation.

## Result

Todo 1 baseline passed.

- Git/runtime state captured.
- Legal ontology MCP pytest baseline passed: 9 tests.
- Fixture evaluation passed: 16 tools, decision `보류`, recommendation `hold_for_review`, direct execution probe `unknown_tool`, no issues.
- Plan-corrected auxiliary tool-list probe passed: count 16 and includes `list_debt_collection_tools`.
- Plan-corrected unknown-tool probe passed: `direct_file_court_document` returns an MCP envelope with result status `unknown_tool`.
- Current deployment artifact presence captured: `containers/Containerfile.mcp` exists; `deploy/`, Compose, Caddyfile, `scripts/recova_mcp`, and `supabase/` are absent in this checkout.
- Docker CLI and Compose are installed; Docker daemon socket is not reachable in this session.

## Evidence Files

Evidence root: `.omo/evidence/recova-mcp-deployment/`

- `task-1-git.txt`
- `task-1-runtime.txt`
- `task-1-pytest.txt`
- `task-1-eval.json`
- `task-1-tool-list.json`
- `task-1-unknown-tool.json`
- `task-1-contract-snapshot.txt`
- `task-1-deployment-artifacts.txt`

Note: concurrent `task-2-*` files exist in the evidence directory from another member's slice; this report covers only `task-1-*`.

## Commands Run

Acceptance command group from current Todo 1:

```sh
mkdir -p .omo/evidence/recova-mcp-deployment && git status --short --branch > .omo/evidence/recova-mcp-deployment/task-1-git.txt && /opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py -q | tee .omo/evidence/recova-mcp-deployment/task-1-pytest.txt && /opt/homebrew/bin/python3 scripts/legal_ontology/evaluate_packet.py --fixtures tests/fixtures/legal-ocr/manifest.json --out .omo/evidence/recova-mcp-deployment/task-1-eval.json
```

The acceptance checks were run as separate evidence-producing commands to keep independent outputs isolated; outputs match the required files.

Current happy auxiliary CLI:

```sh
/opt/homebrew/bin/python3 -c 'import json; from pathlib import Path; from trustgraph_legal.mcp_domain import list_tools; tools=list_tools(); Path(".omo/evidence/recova-mcp-deployment").mkdir(parents=True, exist_ok=True); Path(".omo/evidence/recova-mcp-deployment/task-1-tool-list.json").write_text(json.dumps({"count": len(tools), "tool_names": [t["tool_name"] for t in tools]}, ensure_ascii=False, indent=2))'
```

Current failure auxiliary CLI:

```sh
/opt/homebrew/bin/python3 -c 'import json; from pathlib import Path; from trustgraph_legal.mcp_domain import invoke_tool; result=invoke_tool("direct_file_court_document", {}); Path(".omo/evidence/recova-mcp-deployment/task-1-unknown-tool.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))'
```

## Key Observations

- MCP contract source remains the 16-tool debt collection surface in `trustgraph_legal.mcp_domain`.
- Evidence confirms the current baseline blocks direct filing as an unknown tool.
- The runtime can run Python tests and legal evaluation locally.
- Docker packaging/deployment work is not present yet beyond the existing MCP container file, so Todos 8/9 still need packaging/deployment artifacts.
- Docker daemon unavailability may matter for later local Compose/build validation, but it does not block Todo 1.

## Non-Mutations

- No DNS records queried through mutating APIs or changed.
- No Supabase project, schema, storage, or auth state changed.
- No server/VPS connection or deployment attempted.
- No source, docs, config, or tracked deployment files edited.
