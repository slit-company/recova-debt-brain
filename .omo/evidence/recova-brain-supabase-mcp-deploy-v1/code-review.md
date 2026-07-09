# Code Review - Recova Brain MCP Cloud Run Staging

Status: APPROVE

Scope reviewed:
- `containers/Containerfile.mcp`
- `trustgraph-mcp/trustgraph/mcp_server/legal_only.py`
- `scripts/recova_mcp/mcp_lab_smoke.py`
- `tests/unit/legal_ontology/test_mcp_lab_smoke.py`
- `tests/integration/legal_ontology/test_mcp_debt_only_server.py`
- Cloud Run deployment docs and evidence under `.omo/evidence/recova-brain-supabase-mcp-deploy-v1/`

Findings:
- No blockers.
- Cloud Run container now honors the platform `PORT` value and includes the `scripts/legal_ontology` package needed by runtime imports.
- MCP smoke expects the current 25-tool debt-brain contract and verifies generic/execution tools are absent.
- Host/resource settings are derived from the Cloud Run URL without adding new public admin/write tools.
- No secret value, raw OCR/legal text, debtor PII, filing/contact destination, or authoritative finance balance was added to deliverables.

Validation:
- Focused pytest: 7 passed.
- Compileall: passed.
- Ruff: passed.
- Basedpyright scoped check: 0 errors, 0 warnings, 0 notes.
- JSON validation: passed for 3 deployment evidence files.
- Safety scan: passed for 6 deliverable files.

Caveat:
- `scripts/recova_mcp/mcp_lab_smoke.py` is at 232 pure LOC. It is below the 250-line ceiling but should be split before further expansion.
