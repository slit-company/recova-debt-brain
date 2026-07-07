# Recova MCP Vercel Endpoint

This is a serverless fallback for the Recova debt-brain MCP lab endpoint.

Use it when the Mac mini or any Cloudflare Tunnel origin is unavailable and no
VPS is ready yet. It exposes the same 16 debt-collection domain tools through a
minimal Streamable HTTP JSON-RPC surface:

- `initialize`
- `notifications/initialized`
- `tools/list`
- `tools/call`

The implementation wraps `trustgraph_legal.mcp_domain` directly and does not
expose generic TrustGraph tools.

Build the deploy bundle from the repo root:

```sh
deploy/vercel-mcp/prepare_bundle.sh /tmp/recova-vercel-mcp
```

Deploy the generated bundle with Vercel and runtime env:

```sh
set -a
. deploy/recova-mcp-lab/.env
set +a
vercel deploy /tmp/recova-vercel-mcp --prod --yes \
  -e MCP_LAB_BEARER_TOKEN="$MCP_LAB_BEARER_TOKEN"
```

The current company-domain path is Cloudflare Worker
`recova-mcp-lab-proxy`, which forwards
`https://recova-mcp-lab.slit.company/mcp` to this Vercel origin. Keep Vercel's
direct URL as the fallback origin URL.

The VPS Docker Compose deployment remains the preferred durable origin. This
Vercel endpoint is intentionally narrow and exists to remove dependence on the
retired Mac mini while a VPS is being provisioned.
