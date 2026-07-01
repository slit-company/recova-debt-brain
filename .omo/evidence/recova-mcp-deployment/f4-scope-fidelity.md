# F4 Scope Fidelity

Status: APPROVE

Scope promises checked:

- The public endpoint is debt-only.
- The live MCP smoke reports exactly 16 Recova tools.
- Generic TrustGraph tools are absent from the live tool list.
- Execution-style tools for court filing, debtor contact, attachment, and payment collection are absent from the live tool list.
- Supabase is used for memory/evaluation traces, not as the MCP runtime.
- The MCP runtime is Python FastMCP on `mini` behind Cloudflare Tunnel.
- Missing auth is rejected.
- Trace rows are redacted and recorded in Supabase.
- The runbook states lab-ready, not production-ready.

Secret/PII review:

- Real `.env` files remain ignored.
- `.omo/teams/*/worktrees/` is ignored to avoid committing duplicate worktree contents.
- `task-10-api-keys-redacted.json` keeps secret values, hashes, and key prefixes redacted.
- Remaining `Authorization: Bearer ...` matches are documentation examples, not live tokens.
- `f4-sensitive-scan.txt` reports `NO_FINDINGS` for strict token, key, and resident-ID-shaped patterns.

Non-execution boundary:

- The lab is intentionally assertive for legal judgment.
- The lab does not expose real-world execution tools.
- Rollback preserves Supabase evidence by default and does not perform destructive actions automatically.
