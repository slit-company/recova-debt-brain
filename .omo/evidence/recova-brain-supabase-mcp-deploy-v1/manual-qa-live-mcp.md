# Manual QA - Live Cloud Run MCP

Status: passed

Surface:
- Cloud Run service: `recova-brain-mcp-staging`
- Project: `slit-497603`
- Region: `asia-northeast3`
- Revision: `recova-brain-mcp-staging-00003-qbb`
- MCP URL: `https://recova-brain-mcp-staging-i3pqv2n2rq-du.a.run.app/mcp`

Authenticated MCP smoke:
- Result: `PASS mcp_lab_smoke ok`
- Evidence: `.omo/evidence/recova-brain-supabase-mcp-deploy-v1/cloud-run-mcp-smoke.json`
- Observed `tool_count=25`
- Observed `generic_tools=[]`
- Observed `execution_tools=[]`

Unauthenticated MCP smoke:
- Result: `PASS mcp_lab_smoke auth_rejected`
- Evidence: `.omo/evidence/recova-brain-supabase-mcp-deploy-v1/cloud-run-mcp-no-auth.json`
- Observed `401 Unauthorized` through the MCP streamable HTTP client.

Auth fix note:
- Initial live smoke reached Cloud Run but returned 401.
- Root cause was a trailing newline in Secret Manager version 1 of `recova-mcp-lab-bearer-token`.
- Version 2 stores the same bearer token shape without a trailing newline; token value was not printed or recorded.
