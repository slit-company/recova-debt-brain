# Recova MCP Lab Secret Custody

The lab MCP server uses environment variables only. Do not commit real values.

Required server variables:

- `MCP_LAB_BEARER_TOKEN`: lab client bearer token.
- `SUPABASE_URL`: Supabase project URL for `dev@slit.company`.
- `SUPABASE_SERVICE_ROLE_KEY`: server-only key for redacted trace writes.

Optional deployment variables:

- `SUPABASE_ANON_KEY`: used for anonymous/RLS denial smoke checks.
- `AUTH_ISSUER`: defaults to `https://recova-mcp-lab.slit.company`.
- `AUTH_RESOURCE_URL`: defaults to `https://recova-mcp-lab.slit.company/mcp`.
- `MCP_WEBSOCKET_URL`: TrustGraph gateway WebSocket URL.

Operator-only variables:

- `CLOUDFLARE_API_TOKEN`: DNS mutation token. Keep it in the operator shell or
  Cloudflare CLI context only; never pass it into the MCP server runtime.

Local check:

```sh
scripts/recova_mcp/check_lab_env.sh --redacted
```

The check prints only variable names and redacted status. Evidence may capture the output.

Rotation:

1. Generate a new lab bearer token and store it on the server only.
2. Rotate Supabase service role key from the Supabase dashboard if exposed.
3. Rotate the Cloudflare API token from Cloudflare if exposed.
4. Restart the MCP lab container.
5. Rerun the redacted environment check and MCP smoke.
