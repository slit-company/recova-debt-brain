#!/usr/bin/env sh
set -eu

usage() {
  cat >&2 <<'EOF'
usage: scripts/recova_mcp/deploy_vps.sh [--dry-run] user@host

Deploy the Recova MCP lab bundle to an always-on Linux server.

Environment:
  RECOVA_MCP_REMOTE_DIR   Remote base dir, default /opt/recova-mcp-lab
  RECOVA_MCP_ENV_FILE     Local env file, default deploy/recova-mcp-lab/.env

Prerequisites on the remote host:
  - ssh access for user@host
  - docker with compose plugin
  - ports 80 and 443 reachable from Cloudflare/Internet

This script does not print secret values.
EOF
}

DRY_RUN=0
if [ "${1:-}" = "--dry-run" ]; then
  DRY_RUN=1
  shift
fi

REMOTE="${1:-}"
if [ -z "$REMOTE" ] || [ "${2:-}" ]; then
  usage
  exit 2
fi

REMOTE_DIR="${RECOVA_MCP_REMOTE_DIR:-/opt/recova-mcp-lab}"
ENV_FILE="${RECOVA_MCP_ENV_FILE:-deploy/recova-mcp-lab/.env}"
COMPOSE_FILE="deploy/recova-mcp-lab/docker-compose.yml"

if [ ! -f "$ENV_FILE" ]; then
  printf '%s\n' "missing env file: $ENV_FILE" >&2
  exit 1
fi

if printf '%s' "$REMOTE_DIR" | grep -q "'"; then
  printf '%s\n' "RECOVA_MCP_REMOTE_DIR must not contain single quotes" >&2
  exit 1
fi

run() {
  printf '+ %s\n' "$*"
  if [ "$DRY_RUN" -eq 0 ]; then
    "$@"
  fi
}

ssh_run() {
  printf '+ ssh %s %s\n' "$REMOTE" "$1"
  if [ "$DRY_RUN" -eq 0 ]; then
    ssh "$REMOTE" "$1"
  fi
}

printf '%s\n' "recova_mcp_vps_deploy=starting"
printf '%s\n' "remote=$REMOTE"
printf '%s\n' "remote_dir=$REMOTE_DIR"
printf '%s\n' "env_file=$ENV_FILE"

set -a
. "$ENV_FILE"
set +a
scripts/recova_mcp/check_lab_env.sh --redacted

ssh_run "mkdir -p '$REMOTE_DIR/app/deploy/recova-mcp-lab'"
ssh_run "command -v docker >/dev/null && docker compose version >/dev/null"

run rsync -az --delete \
  --exclude '.git/' \
  --exclude '.omo/' \
  --exclude '.venv/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude 'deploy/recova-mcp-lab/.env' \
  ./ "$REMOTE:$REMOTE_DIR/app/"

run scp "$ENV_FILE" "$REMOTE:$REMOTE_DIR/app/deploy/recova-mcp-lab/.env"

ssh_run "cd '$REMOTE_DIR/app' && docker compose -f '$COMPOSE_FILE' --env-file deploy/recova-mcp-lab/.env up -d --build"
ssh_run "cd '$REMOTE_DIR/app' && docker compose -f '$COMPOSE_FILE' --env-file deploy/recova-mcp-lab/.env ps"

cat <<EOF
recova_mcp_vps_deploy=done

Next DNS step:
  Point recova-mcp-lab.slit.company to this server's public IP in Cloudflare DNS.

Then verify:
  set -a
  . deploy/recova-mcp-lab/.env
  set +a
  /opt/homebrew/bin/python3 scripts/recova_mcp/mcp_lab_smoke.py \\
    --url https://recova-mcp-lab.slit.company/mcp \\
    --token-env MCP_LAB_BEARER_TOKEN \\
    --out .omo/evidence/recova-mcp-deployment/vps-mcp-smoke.json
EOF
