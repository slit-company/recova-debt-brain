# Recova MCP Lab Deployment

This compose bundle runs the debt-only Recova MCP server and Caddy reverse proxy
on an always-on Linux server.

Current live lab endpoint:

```text
https://recova-mcp-lab.slit.company/mcp
```

Direct Vercel origin/fallback endpoint:

```text
https://recova-debt-brain-lab.vercel.app/mcp
```

The lab must not depend on the old Mac mini origin. The current company-domain
path is Cloudflare Worker `recova-mcp-lab-proxy` forwarding to the Vercel
origin. The future durable deployment can be a Linux VPS/container host running
this Docker Compose bundle.

Prepare local env:

```sh
cp deploy/recova-mcp-lab/.env.example deploy/recova-mcp-lab/.env
scripts/recova_mcp/check_lab_env.sh --redacted
```

Validate configuration:

```sh
docker compose -f deploy/recova-mcp-lab/docker-compose.yml config
```

Run local smoke:

```sh
docker compose -f deploy/recova-mcp-lab/docker-compose.yml up --build
curl -i http://127.0.0.1:8000/mcp
docker compose -f deploy/recova-mcp-lab/docker-compose.yml down -v
```

Deploy to a Linux VPS after DNS/server selection:

```sh
scripts/recova_mcp/deploy_vps.sh user@server.example
```

The script copies the repo to `/opt/recova-mcp-lab/app`, copies the ignored
lab `.env` separately, and runs Docker Compose on the remote host. It never
prints secret values.

The old tunnel-backed Cloudflare DNS route has been replaced by a proxied CNAME
plus Worker route. Keeping the dead tunnel route would produce Cloudflare `530`
/ `error code: 1033`.

The public service must use `mcp-debt-collection-server`, not the generic
`mcp-server`.

Live operations are documented in
`docs/product/debt-collection-ontology/recova-mcp-lab-runbook.md`.
