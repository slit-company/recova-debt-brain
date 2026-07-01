# F2 Code Quality Review

Status: APPROVE after corrective review fixes

Current final code-review approval:

- `.omo/evidence/recova-mcp-deployment/final-code-reviewer-2.md` supersedes the stale `final-code-reviewer.md` blocker report.
- `final-code-reviewer-2.md` explicitly applied the `omo:programming` and `omo:remove-ai-slops` review perspectives, including pure LOC, bounded broad-exception handling, test quality, non-tautological config tests, and implementation-mirroring/slop checks.
- Result: `codeQualityStatus: CLEAR`, `recommendation: APPROVE`, `blockers: none`.

Failing-first evidence:

- `.omo/evidence/recova-mcp-deployment/corrective-red-first.txt` reproduces RED behavior by applying the new corrective tests to base `349b9b884e61c0a2787a603afa741aa7771a44be`.
- RED 1: the new linked evaluation/judgment/tool trace test fails on the previous `trustgraph_legal.lab_trace` because `evaluation_run_row` is missing.
- RED 2: the new smoke auth/trace validation tests fail on the previous `mcp_lab_smoke.py` because `auth_error_details` and public `validate_result` behavior are missing.
- RED 3: the new deployment config tests fail on the previous compose/env contract because `CLOUDFLARE_API_TOKEN` is still in runtime config and `8000:8000` is publicly exposed.

Reviewed areas:

- debt-only MCP server host validation
- lab bearer auth boundary
- MCP smoke script
- Supabase trace/evaluation/judgment writer
- runbook and rollback helpers
- deployment docs and environment templates

Verification:

- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_auth_boundary.py tests/integration/legal_ontology/test_mcp_debt_only_server.py tests/unit/legal_ontology/test_lab_trace.py tests/integration/legal_ontology/test_mcp_tools.py -q` passed, 13 tests.
- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_domain_tools.py tests/unit/legal_ontology/test_mcp_auth_boundary.py tests/integration/legal_ontology/test_mcp_debt_only_server.py tests/integration/legal_ontology/test_mcp_tools.py tests/unit/legal_ontology/test_lab_trace.py tests/unit/legal_ontology/test_mcp_lab_smoke.py tests/unit/legal_ontology/test_recova_mcp_deployment_config.py -q` passed, 25 tests.
- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology tests/integration/legal_ontology -q` passed, 58 tests.
- `/usr/bin/python3 -m py_compile trustgraph-mcp/trustgraph/mcp_server/legal_only.py scripts/recova_mcp/mcp_lab_smoke.py scripts/recova_mcp/check_runbook.py tests/integration/legal_ontology/test_mcp_debt_only_server.py` passed.
- `/opt/homebrew/bin/python3 -m py_compile scripts/recova_mcp/mcp_lab_smoke.py scripts/recova_mcp/mcp_smoke_auth.py trustgraph_legal/lab_trace.py trustgraph_legal/lab_trace_supabase.py tests/unit/legal_ontology/test_lab_trace.py tests/unit/legal_ontology/test_mcp_lab_smoke.py tests/unit/legal_ontology/test_recova_mcp_deployment_config.py` passed.
- `git diff --check` passed.
- Pure LOC check is below the 250-line ceiling for changed Python modules: `mcp_lab_smoke.py` 233, `lab_trace.py` 212, `lab_trace_supabase.py` 75, `mcp_smoke_auth.py` 41.

Review findings:

- The public server now passes MCP transport security `allowed_hosts` based on the configured issuer/resource URL, which fixes the live host rejection.
- The smoke script checks both generic TrustGraph tool absence and execution-tool absence.
- The smoke script now accepts expected auth failure only when the exception chain contains auth/401 evidence.
- The authenticated smoke now requires `trace_status`, `evaluation_status`, and `judgment_status` to be `recorded` unless an explicit offline flag is used.
- The Docker Compose package binds the MCP origin to loopback only and does not pass `CLOUDFLARE_API_TOKEN` into the MCP runtime.
- Real bearer tokens remain outside tool arguments and are supplied through MCP HTTP auth context.
- `rollback_lab.sh` is dry-run only, which avoids destructive rollback while still recording exact operations.
