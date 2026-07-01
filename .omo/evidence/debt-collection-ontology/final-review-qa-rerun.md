# Final Review QA Rerun

Overall verdict: **FAIL**

Reason: the required pytest surfaces passed, but the required evaluator invocation failed exactly as requested because `scripts/legal_ontology/evaluate_packet.py` rejects `/tmp/final-review-task10-eval-rerun.json` as outside `repo_root`. The actual MCP gateway-backed smoke was also blocked by a missing local prerequisite: importing `trustgraph-mcp/trustgraph/mcp_server/mcp.py` fails with `ModuleNotFoundError: No module named 'mcp'`.

## Commands

Surface `pytest legal ontology unit`:

```bash
/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology -q
```

Result excerpt:

```text
collected 37 items
tests/unit/legal_ontology/test_case_graph_builder.py ....                [ 10%]
tests/unit/legal_ontology/test_document_classifier.py ......             [ 27%]
tests/unit/legal_ontology/test_field_extractors.py ....                  [ 37%]
tests/unit/legal_ontology/test_ingest.py ...                             [ 45%]
tests/unit/legal_ontology/test_mcp_domain_tools.py .....                 [ 59%]
tests/unit/legal_ontology/test_ontology_governance.py .....              [ 72%]
tests/unit/legal_ontology/test_stop_gates.py ........                    [ 94%]
tests/unit/legal_ontology/test_validate_ontology.py ..                   [100%]
============================== 37 passed in 0.47s ==============================
EXIT_CODE=0
```

Surface `pytest legal ontology MCP integration`:

```bash
/opt/homebrew/bin/python3 -m pytest tests/integration/legal_ontology/test_mcp_tools.py -q
```

Result excerpt:

```text
collected 3 items
tests/integration/legal_ontology/test_mcp_tools.py ...                   [100%]
============================== 3 passed in 2.07s ===============================
EXIT_CODE=0
```

Surface `packet evaluation CLI`:

```bash
python3 scripts/legal_ontology/evaluate_packet.py --fixtures tests/fixtures/legal-ocr/manifest.json --out /tmp/final-review-task10-eval-rerun.json
```

Result excerpt:

```text
path outside repo_root: /tmp/final-review-task10-eval-rerun.json
EXIT_CODE=1
```

Surface `MCP gateway-backed smoke`:

```bash
python3 - <<'PY'
# Temporary inline smoke attempted:
# - start local fake WebSocket gateway
# - import GatewayTokenVerifier from trustgraph.mcp_server.mcp
# - reject bad token, accept good token
# - register debt tools and call list_debt_collection_tools
# - assert no token appears in response JSON
PY
```

Result excerpt:

```text
Traceback (most recent call last):
  File "<stdin>", line 16, in <module>
  File "/Users/cosmos/dev/ontology/trustgraph/trustgraph-mcp/trustgraph/mcp_server/mcp.py", line 15, in <module>
    from mcp.server.fastmcp import FastMCP, Context
ModuleNotFoundError: No module named 'mcp'
EXIT_CODE=1
```

## manualQa

### surfaceEvidence

| scenario id | criterion reference | surface | exact invocation | verdict | artifactRefs |
|---|---|---|---|---|---|
| S1 | VERIFY unit legal ontology tests | Pytest unit | `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology -q` | PASS | A1 |
| S2 | VERIFY MCP integration tests | Pytest integration | `/opt/homebrew/bin/python3 -m pytest tests/integration/legal_ontology/test_mcp_tools.py -q` | PASS | A1 |
| S3 | VERIFY packet evaluator exact command | CLI | `python3 scripts/legal_ontology/evaluate_packet.py --fixtures tests/fixtures/legal-ocr/manifest.json --out /tmp/final-review-task10-eval-rerun.json` | FAIL | A1 |
| S4 | VERIFY actual MCP gateway-backed smoke if feasible | Inline Python smoke using fake WebSocket gateway plus MCP server import | `python3 - <<'PY' ... PY` | FAIL | A1 |

### adversarialCases

| scenario id | criterion reference | adversarial class | expected behavior | verdict | artifactRefs |
|---|---|---|---|---|---|
| A-C1 | MCP fake gateway rejects bad token | Auth rejection | Bad bearer token is rejected by gateway verifier | FAIL: actual MCP server module could not import because `mcp` SDK is missing | A1 |
| A-C2 | MCP fake gateway accepts good token | Auth acceptance | Good bearer token is accepted and converted to gateway-verified auth context | FAIL: actual MCP server module could not import because `mcp` SDK is missing | A1 |
| A-C3 | MCP lists debt tool and does not echo token | Secret handling | `list_debt_collection_tools` appears and response JSON does not contain the bearer token | FAIL: actual MCP server module could not import, so the gateway-backed smoke could not reach tool invocation | A1 |
| A-C4 | Evaluator output path outside repo | Path boundary | Required `/tmp/final-review-task10-eval-rerun.json` output is accepted per task command | FAIL: script rejects `/tmp/...` with `path outside repo_root` | A1 |

### artifactRefs

| id | kind | description | path |
|---|---|---|---|
| A1 | markdown report | Non-empty final QA report containing command invocations, excerpts, verdicts, and cleanup status | `.omo/evidence/debt-collection-ontology/final-review-qa-rerun.md` |

## Cleanup

Temporary resources created under `/tmp` during the run:

```text
/tmp/final-review-task10-qa/
/tmp/final-review-task10-eval-rerun.json
```

Cleanup command run after report assembly:

```bash
rm -rf /tmp/final-review-task10-qa /tmp/final-review-task10-eval-rerun.json
```
