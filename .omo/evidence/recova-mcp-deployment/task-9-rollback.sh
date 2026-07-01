#!/usr/bin/env sh
set -eu
ssh mini 'if [ -f ~/recova-mcp-lab/recova-mcp.pid ]; then kill $(cat ~/recova-mcp-lab/recova-mcp.pid) 2>/dev/null || true; fi'
ssh mini 'latest=$(ls -1t ~/.cloudflared/config.yml.recova-mcp-backup-* 2>/dev/null | head -n 1); if [ -n "$latest" ]; then cp "$latest" ~/.cloudflared/config.yml; launchctl kickstart -k gui/$(id -u)/com.slit.cliproxyapi-cloudflared || true; fi'
echo 'Remove recova-mcp-lab.slit.company tunnel DNS route in Cloudflare if full rollback is required.'
