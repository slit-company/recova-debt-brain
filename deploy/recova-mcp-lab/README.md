# Recova MCP Lab Deployment

This compose bundle runs the debt-only Recova MCP server and Caddy reverse proxy.

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

The public service must use `mcp-debt-collection-server`, not the generic `mcp-server`.
