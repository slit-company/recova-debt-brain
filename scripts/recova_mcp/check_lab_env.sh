#!/usr/bin/env sh
set -eu

if [ "${1:-}" != "--redacted" ]; then
  printf '%s\n' "usage: scripts/recova_mcp/check_lab_env.sh --redacted" >&2
  exit 2
fi

missing=0
for key in MCP_LAB_BEARER_TOKEN SUPABASE_URL SUPABASE_SERVICE_ROLE_KEY; do
  value="$(printenv "$key" || true)"
  if [ -z "$value" ]; then
    printf '%s=missing\n' "$key"
    missing=1
  else
    printf '%s=present value=[REDACTED]\n' "$key"
  fi
done

if [ "$missing" -ne 0 ]; then
  exit 1
fi

printf '%s\n' "recova_mcp_lab_env=ready"
