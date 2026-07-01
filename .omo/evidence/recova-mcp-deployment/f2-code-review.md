# F2 Code Quality Review

Status: APPROVE

Reviewed areas:

- debt-only MCP server host validation
- lab bearer auth boundary
- MCP smoke script
- Supabase trace writer
- runbook and rollback helpers
- deployment docs and environment templates

Verification:

- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_auth_boundary.py tests/integration/legal_ontology/test_mcp_debt_only_server.py tests/unit/legal_ontology/test_lab_trace.py tests/integration/legal_ontology/test_mcp_tools.py -q` passed, 13 tests.
- `/usr/bin/python3 -m py_compile trustgraph-mcp/trustgraph/mcp_server/legal_only.py scripts/recova_mcp/mcp_lab_smoke.py scripts/recova_mcp/check_runbook.py tests/integration/legal_ontology/test_mcp_debt_only_server.py` passed.
- `git diff --check` passed.

Review findings:

- The public server now passes MCP transport security `allowed_hosts` based on the configured issuer/resource URL, which fixes the live host rejection.
- The smoke script checks both generic TrustGraph tool absence and execution-tool absence.
- Real bearer tokens remain outside tool arguments and are supplied through MCP HTTP auth context.
- `rollback_lab.sh` is dry-run only, which avoids destructive rollback while still recording exact operations.
