# F1 Plan Compliance

Status: APPROVE

Checked plan: `.omo/plans/recova-mcp-deployment.md`

Result:

- Todos 1 through 12 have evidence under `.omo/evidence/recova-mcp-deployment/`.
- Todo 1, 2, and 3 were split to team members and have reports under `.omo/teams/team-89938d95/artifacts/`.
- Todo 4 through 12 have code, config, live evidence, or operation evidence in this checkout.
- The canonical endpoint was corrected to `https://recova-mcp-lab.slit.company/mcp` after TLS evidence showed the deeper `mcp-lab.recova.slit.company` hostname is not covered by standard Cloudflare Universal SSL.
- The final endpoint, live smoke, Supabase trace proof, rollback dry-run, and runbook checks are all recorded.

Key evidence:

- `task-1-pytest.txt`
- `task-2-dns-authority.txt`
- `task-3-supabase-smoke.txt`
- `task-8-local-mcp-no-auth.txt`
- `task-9-live-http.txt`
- `task-10-db-push.txt`
- `task-10-trace-count.json`
- `task-11-mcp-smoke.json`
- `task-12-rollback-dry-run.txt`
- `task-12-runbook-check-pass.json`
