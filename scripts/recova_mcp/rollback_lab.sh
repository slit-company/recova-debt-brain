#!/usr/bin/env sh
set -eu

if [ "${1:-}" != "--dry-run" ]; then
  printf '%s\n' "usage: scripts/recova_mcp/rollback_lab.sh --dry-run" >&2
  printf '%s\n' "This helper is intentionally dry-run only. Copy the printed commands after review." >&2
  exit 2
fi

cat <<'EOF'
recova_mcp_lab_rollback=dry_run

1. Stop the VPS Docker Compose stack:
   ssh "$RECOVA_MCP_HOST" 'cd /opt/recova-mcp-lab/app && docker compose -f deploy/recova-mcp-lab/docker-compose.yml down'

2. Preserve the remote app and env for inspection:
   ssh "$RECOVA_MCP_HOST" 'tar -czf /opt/recova-mcp-lab/rollback-snapshot.tgz -C /opt/recova-mcp-lab app'

3. Remove or disable the Cloudflare Worker route and DNS record for recova-mcp-lab.slit.company:
   Use Cloudflare dashboard or a reviewed API deletion. Preserve DNS and Worker evidence.

4. Preserve Supabase evidence by default:
   Do not delete the recova-mcp-lab Supabase project, migrations, tool_traces, or judgment_runs unless the user asks for a purge.

5. Rotate exposed lab credentials if rollback was caused by leakage:
   MCP_LAB_BEARER_TOKEN, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_ANON_KEY, and any Cloudflare token used for DNS mutation.

6. Verify rollback:
   curl -i https://recova-mcp-lab.slit.company/mcp
   Expected after DNS/proxy removal: no route, 404, 502, or auth rejection from a deliberately retained endpoint.
EOF
