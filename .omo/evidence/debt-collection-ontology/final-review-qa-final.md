# Final QA Rerun: debt-collection ontology

Verdict: PASS

Date: 2026-06-30
Workspace: `/Users/cosmos/dev/ontology/trustgraph`

## Exact Commands

```bash
/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology -q
/opt/homebrew/bin/python3 -m pytest tests/integration/legal_ontology/test_mcp_tools.py -q
python3 scripts/legal_ontology/evaluate_packet.py --fixtures tests/fixtures/legal-ocr/manifest.json --out /tmp/final-review-task10-eval-final.json
python3 -m venv /tmp/final-review-task10-mcp-venv
/tmp/final-review-task10-mcp-venv/bin/python -m pip install mcp websockets prometheus-client
/tmp/final-review-task10-mcp-venv/bin/python /tmp/final-review-task10-gateway.py 18765 /tmp/final-review-task10-gateway.log
PYTHONPATH=trustgraph-mcp:trustgraph-base:. /tmp/final-review-task10-mcp-venv/bin/python -m trustgraph.mcp_server.mcp --host 127.0.0.1 --port 18766 --websocket-url ws://127.0.0.1:18765/api/v1/socket --auth-issuer http://127.0.0.1:18766 --auth-resource-url http://127.0.0.1:18766
/tmp/final-review-task10-mcp-venv/bin/python /tmp/final-review-task10-client.py http://127.0.0.1:18766/mcp /tmp/final-review-task10-smoke.json
```

## manualQa

### surfaceEvidence

| scenario id | criterion reference | surface | exact invocation | verdict | artifactRefs |
|---|---|---|---|---|---|
| S1 | C1 unit ontology suite passes | local CLI / pytest | `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology -q` | PASS: 38 passed, exit code 0 | A1 |
| S2 | C2 integration MCP tool suite passes | local CLI / pytest | `/opt/homebrew/bin/python3 -m pytest tests/integration/legal_ontology/test_mcp_tools.py -q` | PASS: 3 passed, exit code 0 | A2 |
| S3 | C3 evaluator writes JSON output | local CLI / evaluator | `python3 scripts/legal_ontology/evaluate_packet.py --fixtures tests/fixtures/legal-ocr/manifest.json --out /tmp/final-review-task10-eval-final.json` | PASS: exit code 0, `/tmp/final-review-task10-eval-final.json` existed and was non-empty before cleanup; copied to evidence | A3, A4 |
| S4 | C4 MCP streamable HTTP smoke | local streamable HTTP MCP + fake WebSocket gateway | `PYTHONPATH=trustgraph-mcp:trustgraph-base:. /tmp/final-review-task10-mcp-venv/bin/python -m trustgraph.mcp_server.mcp --host 127.0.0.1 --port 18766 --websocket-url ws://127.0.0.1:18765/api/v1/socket --auth-issuer http://127.0.0.1:18766 --auth-resource-url http://127.0.0.1:18766` and SDK client `/tmp/final-review-task10-client.py http://127.0.0.1:18766/mcp /tmp/final-review-task10-smoke.json` | PASS: bad token rejected, good token accepted, `list_debt_collection_tools` listed, tool call returned, token not echoed | A5, A6 |
| S5 | C5 cleanup completed | filesystem cleanup | `rm -rf /tmp/final-review-task10-*` targeted resources listed in cleanup artifact | PASS: temp venv, scripts, logs, pid files, health file, smoke JSON, pip log, and evaluator `/tmp` JSON removed | A7 |

### adversarialCases

| scenario id | criterion reference | adversarial class | expected behavior | verdict | artifactRefs |
|---|---|---|---|---|---|
| A-S4-1 | C4 auth boundary | bad bearer token | Streamable HTTP MCP request is rejected before tool access | PASS: SDK call failed with 401-backed `ExceptionGroup`; gateway recorded `auth_failed` | A5, A6 |
| A-S4-2 | C4 auth boundary | good bearer token | Streamable HTTP MCP session initializes and can list/call tools | PASS: good token accepted; 47 tools listed; debt tools sample includes `list_debt_collection_tools`, `get_case_graph`, `recommend_next_action` | A5, A6 |
| A-S4-3 | C4 secret handling | token echo leakage | Tool list/call response and retained artifacts must not include raw test tokens | PASS: smoke JSON reports `token_not_echoed=true`; retained evidence grep found no raw test token strings | A5, A6 |
| A-S3-1 | C3 output existence | missing or empty evaluator JSON | Evaluator must create a non-empty JSON file at the requested `/tmp` path | PASS: command log recorded `/tmp/final-review-task10-eval-final.json` at 264287 bytes before cleanup; copied artifact parses as JSON | A3, A4 |

### artifactRefs

| id | kind | description | path |
|---|---|---|---|
| A1 | command transcript | Unit legal ontology pytest output with exit code | `.omo/evidence/debt-collection-ontology/final-unit-pytest.txt` |
| A2 | command transcript | Integration MCP tools pytest output with exit code | `.omo/evidence/debt-collection-ontology/final-integration-mcp-tools-pytest.txt` |
| A3 | command transcript | Evaluator stdout/stderr, exit code, and `/tmp` JSON existence/size check | `.omo/evidence/debt-collection-ontology/final-evaluate-packet.txt` |
| A4 | JSON evidence | Copied evaluator output from `/tmp/final-review-task10-eval-final.json` before cleanup | `.omo/evidence/debt-collection-ontology/final-review-task10-eval-final.json` |
| A5 | command transcript | MCP smoke commands, SDK result, gateway events, server log tail | `.omo/evidence/debt-collection-ontology/final-mcp-smoke.txt` |
| A6 | JSON evidence | Structured MCP smoke result with auth and token-echo assertions | `.omo/evidence/debt-collection-ontology/final-mcp-smoke.json` |
| A7 | cleanup transcript | Removed `/tmp/final-review-task10-*` temp resources and post-cleanup checks | `.omo/evidence/debt-collection-ontology/final-cleanup.txt` |

## Cleanup

Removed all temporary resources created for this rerun:

```text
/tmp/final-review-task10-mcp-venv
/tmp/final-review-task10-gateway.py
/tmp/final-review-task10-client.py
/tmp/final-review-task10-gateway.log
/tmp/final-review-task10-gateway.stdout
/tmp/final-review-task10-server.log
/tmp/final-review-task10-smoke.json
/tmp/final-review-task10-gateway.pid
/tmp/final-review-task10-server.pid
/tmp/final-review-task10-health.out
/tmp/final-review-task10-pip.log
/tmp/final-review-task10-eval-final.json
```

Retained only PII-safe evidence artifacts under `.omo/evidence/debt-collection-ontology/`.
