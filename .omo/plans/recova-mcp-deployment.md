# recova-mcp-deployment - Work Plan

## TL;DR (For humans)
**What you'll get:** A live Recova debt-brain MCP lab at `https://recova-mcp-lab.slit.company/mcp`, plus a Supabase-backed experiment memory where agent judgments, tool traces, source refs, expected answers, and corrections are captured for fast tuning.

**Why this approach:** The MCP runtime runs on the existing `mini` host if it can support Docker/Caddy and network exposure, otherwise on a Hetzner CX22 Ubuntu VM provisioned with `hcloud` only when a local token exists. Supabase becomes the lab database, vector store, storage, auth metadata, and evaluation notebook rather than a forced runtime rewrite.

**What it will NOT do:** It will not expose the generic TrustGraph tool surface publicly. It will not let agents contact debtors, file court documents, initiate attachment/payment/collection, or store raw PII in evidence.

**Effort:** XL
**Risk:** High - external DNS, server deployment, auth, Supabase schema, and public MCP client compatibility all have to line up.
**Decisions to sanity-check:** Use `recova-mcp-lab.slit.company` because Cloudflare Universal SSL does not cover the deeper `mcp-lab.recova.slit.company` hostname without an advanced certificate; try `mini` first, fallback to Hetzner CX22 only if local `hcloud` auth exists; use Docker Compose + Caddy; use Supabase account `dev@slit.company`; start with lab bearer tokens; keep judgment bold but execution closed.

Your next move: run this plan with `$omo:start-work .omo/plans/recova-mcp-deployment.md` or keep it in ULW loop execution. Full execution detail follows below.

---

> TL;DR (machine): XL/high-risk deployment plan for a debt-only Recova MCP lab, Supabase experiment memory, DNS/TLS, client smokes, rollback, and evidence-bound QA.

## Scope
### Must have
- `recova-mcp-lab.slit.company` resolves and serves HTTPS `/mcp` via Caddy or equivalent reverse proxy.
- Runtime runs on a concrete host: primary target is existing Codex remote host `mini`; fallback target is Hetzner CX22 Ubuntu 24.04 via `hcloud` if `HCLOUD_TOKEN` is available locally. Docker Compose installs the Python/FastMCP TrustGraph MCP server plus Recova legal modules.
- Public MCP surface is debt-only: exactly the 16 Recova debt-brain tools from `trustgraph_legal.mcp_domain.TOOL_GROUPS`; generic TrustGraph tools are not externally visible.
- Supabase account/project for `dev@slit.company` provides lab tables, pgvector extension, storage buckets, trace/evaluation logs, and RLS/service-role boundaries.
- Auth uses lab bearer tokens through the existing MCP/gateway/IAM path; Supabase Auth may store lab users/sessions but must not silently replace TrustGraph gateway validation.
- Every tool response keeps the existing envelope: `schema_version`, `tool_name`, `group`, `scope`, `pii_profile`, `redaction`, `source_refs`, `warnings`, `result`.
- Judgment is assertive in the lab: StopGate/advisory flows must return `가능`, `보류`, or `불가능` plus confidence, source refs, failure labels, and expected/actual capture.
- External execution remains impossible: no filing, contacting, attachment, payment, collection, or final legal representation tools.
- Real clients get connection instructions and smoke evidence for Hermes/generic MCP, Claude, and OpenAI/ChatGPT-compatible MCP use.
- Rollback removes DNS/proxy/container/secrets safely while retaining Supabase evidence unless explicitly purged.

### Must NOT have (guardrails, anti-slop, scope boundaries)
- Do not run the MCP runtime inside Supabase Edge Functions; Supabase is the memory/evaluation platform, not the primary Python MCP host.
- Do not expose raw OCR text, full addresses, phone numbers, account numbers, resident IDs, bearer tokens, Supabase service keys, Cloudflare API tokens, or server `.env` contents in logs, reports, screenshots, or evidence.
- Do not publish the full `McpServer._register_tools()` generic TrustGraph surface to external agents.
- Do not create a fake success path that only runs unit tests; every deployment criterion needs a live HTTP/browser/CLI/DB evidence artifact.
- Do not proceed with DNS mutation until nameserver authority is observed and recorded.
- Do not let Supabase Auth conflict with the current gateway/IAM contract without an explicit token-bridge task and tests.
- Do not delete lab evidence during rollback unless the user explicitly asks for data purge.

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: tests-after for packaging/deployment/docs, TDD where debt-only mode or Supabase trace code changes behavior.
- Unit/integration baseline: `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py -q`.
- Contract baseline: `/opt/homebrew/bin/python3 scripts/legal_ontology/evaluate_packet.py --fixtures tests/fixtures/legal-ocr/manifest.json --out .omo/evidence/recova-mcp-deployment/task-00-baseline-eval.json`.
- Live HTTP surface: `curl -i https://recova-mcp-lab.slit.company/mcp` must reject missing auth and accept an authorized MCP initialization/list-tools request.
- Browser/account surfaces: use Aside only when account-backed Cloudflare/GoDaddy/Supabase confirmation is required; save screenshots/snapshots under `.omo/evidence/recova-mcp-deployment/`.
- DB surface: Supabase schema verification uses CLI stdout plus SQL row-count/state dumps with secrets redacted.
- Evidence root: `.omo/evidence/recova-mcp-deployment/`.

## Execution strategy
### Parallel execution waves
> Target 5-8 todos per wave. Fewer than 3 (except the final) means you under-split.
- Wave 1 - Preflight and contracts: confirm repo baseline, DNS authority, Supabase auth state, server access, and current debt MCP contract.
- Wave 2 - Buildable artifacts: implement/verify debt-only MCP mode, Docker Compose/Caddy packaging, Supabase migrations/storage/RLS, and redacted secret handling.
- Wave 3 - Deploy and connect: resolve/provision the concrete runtime target, wire DNS/TLS, deploy Supabase schema, seed lab tokens, and run live `/mcp` smokes.
- Wave 4 - Client and evaluation loop: connect agent clients, run bold judgment fixtures, capture traces to Supabase, and tune failure labels.
- Wave 5 - Operations and rollback: monitoring, restart persistence, backup/rollback, final quality gate, and handoff.

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1 | none | 2, 4, 8, 9 | 2, 3 |
| 2 | none | 4, 7, 9 | 1, 3 |
| 3 | none | 5, 6, 10 | 1, 2 |
| 4 | 1, 2 | 8, 9, 11 | 5, 6 |
| 5 | 3 | 10, 11 | 4, 6, 7 |
| 6 | 3 | 10, 11 | 4, 5, 7 |
| 7 | 2 | 8, 9, 11 | 4, 5, 6 |
| 8 | 1, 4, 7 | 9, 11, 12 | 10 |
| 9 | 1, 2, 4, 7, 8 | 11, 12 | 10 |
| 10 | 3, 5, 6 | 11, 12 | 8, 9 |
| 11 | 8, 9, 10 | 12 | none |
| 12 | 11 | final verification | none |

## Todos
> Implementation + Test = ONE todo. Never separate.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->
- [x] 1. Preflight repo, runtime, and baseline contract evidence
  What to do / Must NOT do: Capture exact git state, Python version, Docker availability, current MCP contract, current 16-tool result, fixture evaluation, and current lack/presence of deployment artifacts. Must not mutate DNS, Supabase, or server.
  Parallelization: Wave 1 | Blocked by: none | Blocks: 2, 4, 8, 9
  References (executor has NO interview context - be exhaustive): `.omo/drafts/recova-mcp-deployment.md`; `docs/product/debt-collection-ontology/mcp-domain-server-contract.md:14`; `docs/product/debt-collection-ontology/mcp-domain-server-contract.md:85`; `docs/product/debt-collection-ontology/mcp-domain-server-contract.md:245`; `trustgraph_legal/mcp_domain.py:21`; `trustgraph_legal/mcp_domain.py:97`; `tests/integration/legal_ontology/test_mcp_tools.py`; `containers/Containerfile.mcp:24`
  Acceptance criteria (agent-executable): `mkdir -p .omo/evidence/recova-mcp-deployment && git status --short --branch > .omo/evidence/recova-mcp-deployment/task-1-git.txt && /opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py -q | tee .omo/evidence/recova-mcp-deployment/task-1-pytest.txt && /opt/homebrew/bin/python3 scripts/legal_ontology/evaluate_packet.py --fixtures tests/fixtures/legal-ocr/manifest.json --out .omo/evidence/recova-mcp-deployment/task-1-eval.json`
  QA scenarios (name the exact tool + invocation): happy auxiliary CLI: `/opt/homebrew/bin/python3 -c 'import json; from pathlib import Path; from trustgraph_legal.mcp_domain import list_tools; tools=list_tools(); Path(".omo/evidence/recova-mcp-deployment").mkdir(parents=True, exist_ok=True); Path(".omo/evidence/recova-mcp-deployment/task-1-tool-list.json").write_text(json.dumps({"count": len(tools), "tool_names": [t["tool_name"] for t in tools]}, ensure_ascii=False, indent=2))'`, PASS if count is 16 and includes `list_debt_collection_tools`; failure auxiliary CLI: `/opt/homebrew/bin/python3 -c 'import json; from pathlib import Path; from trustgraph_legal.mcp_domain import invoke_tool; result=invoke_tool("direct_file_court_document", {}); Path(".omo/evidence/recova-mcp-deployment/task-1-unknown-tool.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))'`, PASS if envelope result status is `unknown_tool`.
  Commit: N | evidence-only preflight unless baseline docs need correction.

- [x] 2. DNS authority and account-access audit for `slit.company`
  What to do / Must NOT do: Determine whether Cloudflare is authoritative for `slit.company`; if not, use Aside/GoDaddy/cosmos Google only to confirm the registrar/DNS state and plan delegation. Must not create or update DNS records until server IP exists and rollback command is written.
  Parallelization: Wave 1 | Blocked by: none | Blocks: 4, 7, 9
  References (executor has NO interview context - be exhaustive): user supplied "Cloudflare stored key" and "domain is GoDaddy cosmos Google"; Cloudflare DNS Records API official docs `https://developers.cloudflare.com/api/resources/dns/subresources/records/methods/create/`; GoDaddy Domains API official docs `https://developer.godaddy.com/doc/endpoint/domains`; MCP endpoint must be HTTPS `/mcp`.
  Acceptance criteria (agent-executable): `dig +short NS slit.company | tee .omo/evidence/recova-mcp-deployment/task-2-ns.txt`; if Cloudflare token exists, `curl -sS -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" https://api.cloudflare.com/client/v4/zones?name=slit.company | jq '{success, result: [.result[] | {id,name,status}]}' > .omo/evidence/recova-mcp-deployment/task-2-cloudflare-zone-redacted.json`; if token absent or zone missing, use Aside REPL/exec to capture GoDaddy/Cloudflare logged-in state screenshot without secrets.
  QA scenarios (name the exact tool + invocation): happy browser/CLI: Aside `aside repl` opens Cloudflare or GoDaddy only if CLI authority cannot prove it, snapshot saved as `.omo/evidence/recova-mcp-deployment/task-2-dns-authority.txt`, PASS if one authoritative DNS owner is recorded; failure CLI: attempt a dry lookup for `recova-mcp-lab.slit.company` with `dig +short recova-mcp-lab.slit.company` and PASS if current absence/conflict is captured before mutation, evidence `.omo/evidence/recova-mcp-deployment/task-2-existing-record.txt`.
  Commit: N | external-state evidence only.

- [x] 3. Supabase lab project, schema, RLS, storage, and vector design
  What to do / Must NOT do: Create `supabase/` project artifacts for lab memory using account `dev@slit.company`: migrations for `case_packets`, `documents`, `tool_traces`, `judgment_runs`, `expected_answers`, `human_corrections`, `ontology_versions`, `rule_versions`, `evaluation_runs`, `agent_clients`, plus pgvector embeddings table and storage bucket policy notes. Must not store raw OCR/PII in unrestricted columns.
  Parallelization: Wave 1 | Blocked by: none | Blocks: 5, 6, 10
  References (executor has NO interview context - be exhaustive): Supabase CLI docs `https://supabase.com/docs/reference/cli/introduction`; Supabase migrations docs `https://supabase.com/docs/guides/deployment/database-migrations`; Supabase pgvector docs `https://supabase.com/docs/guides/database/extensions/pgvector`; Supabase RAG permissions docs `https://supabase.com/docs/guides/ai/rag-with-permissions`; current legal envelope `trustgraph_legal/mcp_domain.py:51`; redaction contract `docs/product/debt-collection-ontology/mcp-domain-server-contract.md:172`.
  Acceptance criteria (agent-executable): add SQL migrations under `supabase/migrations/`; `supabase db start` or local equivalent applies migrations; `supabase db diff --local --schema public` exits clean after migration; SQL smoke writes one redacted trace row and rejects/selectively hides raw PII by RLS or policy.
  QA scenarios (name the exact tool + invocation): happy auxiliary DB CLI: `supabase db reset --local --no-seed` then `psql "$LOCAL_SUPABASE_DB_URL" -f .omo/evidence/recova-mcp-deployment/task-3-smoke.sql`, PASS if trace/evaluation rows insert and query redacted fields; failure DB CLI: insert raw `resident_id`/phone-shaped value into prohibited field and PASS if check constraint/policy rejects or stores only hash/redacted form, evidence `.omo/evidence/recova-mcp-deployment/task-3-supabase-smoke.txt`.
  Commit: Y | `feat(lab): add Supabase experiment memory schema`

- [x] 4. Debt-only MCP public mode
  What to do / Must NOT do: Add a deployable mode or entrypoint that registers only the 16 Recova debt-brain tools externally. Current `McpServer._register_tools()` registers generic TrustGraph tools first, so the plan requires either a new legal-only server class/flag or a reverse-proxy/tool allowlist that is test-proven. Must not remove existing generic server behavior for upstream compatibility.
  Parallelization: Wave 2 | Blocked by: 1, 2 | Blocks: 8, 9, 11
  References (executor has NO interview context - be exhaustive): `trustgraph-mcp/trustgraph/mcp_server/mcp.py:331`; `trustgraph-mcp/trustgraph/mcp_server/mcp.py:364`; `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py:39`; `trustgraph_legal/mcp_domain.py:21`; `trustgraph_legal/mcp_domain.py:97`; `docs/product/debt-collection-ontology/mcp-domain-server-contract.md:83`
  Acceptance criteria (agent-executable): add failing-first coverage in `tests/integration/legal_ontology/test_mcp_debt_only_server.py` proving current public registration exposes generic tools or has no legal-only mode; then green with `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology/test_mcp_domain_tools.py tests/integration/legal_ontology/test_mcp_tools.py tests/integration/legal_ontology/test_mcp_debt_only_server.py -q`.
  QA scenarios (name the exact tool + invocation): happy auxiliary CLI/fake-MCP: instantiate legal-only registration and write `.omo/evidence/recova-mcp-deployment/task-4-registered-tools.json`, PASS if exactly 16 tools and no `embeddings`, `put_config`, `load_document`, `delete_kg_core`; failure auxiliary CLI: request generic `put_config` through the public legal-only facade and PASS if `unknown_tool`/not registered, evidence `.omo/evidence/recova-mcp-deployment/task-4-generic-block.json`.
  Commit: Y | `feat(legal-mcp): add debt-only lab server mode`

- [x] 5. Supabase trace writer and redacted evaluation sink
  What to do / Must NOT do: Implement a small adapter that records MCP lab runs to Supabase: client, tool name, arguments hash, source_refs, StopGate decision, confidence, result labels, expected answer, actual answer, correction status, and envelope hash. Must not write raw tool payloads, raw OCR text, or secrets.
  Parallelization: Wave 2 | Blocked by: 3 | Blocks: 10, 11
  References (executor has NO interview context - be exhaustive): `trustgraph_legal/mcp_domain.py:121`; `trustgraph_legal/mcp_envelope.py`; `trustgraph_legal/pii.py`; `docs/product/debt-collection-ontology/mcp-domain-server-contract.md:108`; `docs/product/debt-collection-ontology/mcp-domain-server-contract.md:154`; `docs/product/debt-collection-ontology/mcp-domain-server-contract.md:172`; Supabase API/key docs `https://supabase.com/docs/guides/getting-started/api-keys`
  Acceptance criteria (agent-executable): failing-first test proves a sample envelope is not recorded; green test records a redacted trace row through a fake Supabase client; PII scan over generated evidence has no findings: `rg -n "주민등록번호|[0-9]{6}-[0-9]{7}|Authorization: Bearer|service_role|CLOUDFLARE_API_TOKEN" .omo/evidence/recova-mcp-deployment trustgraph_legal tests || true` returns no sensitive findings except allowlisted docs/examples.
  QA scenarios (name the exact tool + invocation): happy auxiliary CLI: `/opt/homebrew/bin/python3 -m trustgraph_legal.lab_trace_smoke --fixtures tests/fixtures/legal-ocr/manifest.json --fake-supabase --out .omo/evidence/recova-mcp-deployment/task-5-trace.json`, PASS if row count > 0 and every record has `raw_text_included=false`; failure auxiliary CLI: `/opt/homebrew/bin/python3 -m trustgraph_legal.lab_trace_smoke --fake-supabase --payload-json '{"tool_name":"evaluate_stop_gates","arguments":{"memo":"resident id YYMMDD-XXXXXXX phone 010-XXXX-XXXX"}}' --expect-redacted --out .omo/evidence/recova-mcp-deployment/task-5-redaction.json`, PASS if output has redaction counts and `rg -n "YYMMDD-XXXXXXX|010-XXXX-XXXX" .omo/evidence/recova-mcp-deployment/task-5-redaction.json` returns no matches.
  Commit: Y | `feat(lab): record redacted MCP evaluation traces`

- [x] 6. Bold judgment evaluation harness
  What to do / Must NOT do: Extend or wrap fixture evaluation so lab runs capture assertive decisions, source refs, confidence, failure labels, expected answer, actual answer, and human correction placeholders. Must not collapse all uncertain cases to `보류`; must not execute real-world actions.
  Parallelization: Wave 2 | Blocked by: 3 | Blocks: 10, 11
  References (executor has NO interview context - be exhaustive): `scripts/legal_ontology/evaluate_packet.py`; `docs/product/debt-collection-ontology/mcp-domain-server-contract.md:142`; `docs/product/debt-collection-ontology/mcp-domain-server-contract.md:245`; `resources/legal_rules/debt_collection_stopgate_v0.json`; `trustgraph_legal/stop_gates.py`; `trustgraph_legal/check.py`
  Acceptance criteria (agent-executable): focused tests prove evaluation output includes `decision`, `confidence`, `source_refs`, `failure_labels`, `expected_answer`, `actual_answer`, `correction_status`; fixture evaluation still returns contract summary with 16 tools and failure probe `unknown_tool`.
  QA scenarios (name the exact tool + invocation): happy auxiliary CLI: `/opt/homebrew/bin/python3 scripts/legal_ontology/evaluate_packet.py --fixtures tests/fixtures/legal-ocr/manifest.json --out .omo/evidence/recova-mcp-deployment/task-6-bold-eval.json`, PASS if JSON includes required fields and at least one StopGate label; failure auxiliary CLI: `/opt/homebrew/bin/python3 -c 'import json; from pathlib import Path; from trustgraph_legal.mcp_domain import invoke_tool; probes=["direct_file_court_document","contact_debtor","initiate_attachment","collect_payment"]; out={name: invoke_tool(name, {"case_packet_id":"lab-fixture"}) for name in probes}; Path(".omo/evidence/recova-mcp-deployment/task-6-execution-block.json").write_text(json.dumps(out, ensure_ascii=False, indent=2)); assert all(v.get("result", {}).get("status") in {"unknown_tool","not_configured","blocked"} for v in out.values())'`, PASS if all execution probes are absent or blocked.
  Commit: Y | `feat(lab): capture bold judgment evaluation labels`

- [x] 7. Secret custody and redacted deployment configuration
  What to do / Must NOT do: Add deployment `.env.example`, secret checklist, local/server secret file paths, rotation commands, and validation script that confirms required variables exist without printing values. Must not commit real secrets.
  Parallelization: Wave 2 | Blocked by: 2 | Blocks: 8, 9, 11
  References (executor has NO interview context - be exhaustive): `docs/tech-specs/iam.md:116`; `docs/tech-specs/iam.md:125`; `trustgraph-mcp/trustgraph/mcp_server/auth.py:122`; `trustgraph-mcp/trustgraph/mcp_server/legal_tools.py:87`; `docs/product/debt-collection-ontology/mcp-domain-server-contract.md:34`
  Acceptance criteria (agent-executable): `scripts/recova_mcp/check_lab_env.sh --redacted` exits 0 when required env names are present and prints only key names/status; failure fixture with missing `MCP_LAB_BEARER_TOKEN` exits nonzero without printing any secret values.
  QA scenarios (name the exact tool + invocation): happy tmux/CLI: `env MCP_LAB_BEARER_TOKEN=x SUPABASE_URL=x SUPABASE_SERVICE_ROLE_KEY=x CLOUDFLARE_API_TOKEN=x scripts/recova_mcp/check_lab_env.sh --redacted | tee .omo/evidence/recova-mcp-deployment/task-7-env-pass.txt`, PASS if values are masked; failure CLI: unset one variable and PASS if nonzero + missing key name only, `.omo/evidence/recova-mcp-deployment/task-7-env-fail.txt`.
  Commit: Y | `chore(deploy): add redacted lab secret checks`

- [x] 8. Docker Compose, Caddy, and healthcheck packaging
  What to do / Must NOT do: Add deployable artifacts for the lab server: Compose file, Caddyfile, healthcheck script, container build using `containers/Containerfile.mcp` or improved derivative, volumes/log policy, restart policy, and local smoke instructions. Must not require Supabase Edge Functions to host the MCP runtime.
  Parallelization: Wave 3 | Blocked by: 1, 4, 7 | Blocks: 11, 12
  References (executor has NO interview context - be exhaustive): `containers/Containerfile.mcp:24`; `trustgraph-mcp/pyproject.toml:11`; `trustgraph-mcp/pyproject.toml:25`; `trustgraph-mcp/trustgraph/mcp_server/mcp.py:276`; `trustgraph-mcp/trustgraph/mcp_server/mcp.py:369`; `docs/product/debt-collection-ontology/mcp-domain-server-contract.md:40`
  Acceptance criteria (agent-executable): `docker compose -f deploy/recova-mcp-lab/docker-compose.yml config` exits 0; local build either succeeds or documented missing upstream dependency is captured; Caddy config validation passes.
  QA scenarios (name the exact tool + invocation): happy tmux/HTTP: `tmux new-session -d -s ulw-qa-recova-mcp-compose 'docker compose -f deploy/recova-mcp-lab/docker-compose.yml up --build'` then `curl -i http://127.0.0.1:8000/mcp | tee .omo/evidence/recova-mcp-deployment/task-8-local-mcp-http.txt`, PASS if MCP endpoint responds with auth rejection or MCP protocol error rather than connection failure; failure HTTP: `curl -i http://127.0.0.1:8000/mcp | tee .omo/evidence/recova-mcp-deployment/task-8-local-mcp-no-auth.txt` without auth returns 401/403 or MCP auth error; cleanup: `docker compose -f deploy/recova-mcp-lab/docker-compose.yml down -v && tmux kill-session -t ulw-qa-recova-mcp-compose`.
  Commit: Y | `build(deploy): package Recova MCP lab server`

- [x] 9. DNS, TLS, and live host deployment
  What to do / Must NOT do: Resolve the concrete runtime target before deploying. Primary: use existing Codex remote host `mini` if `ssh mini 'docker --version && caddy version'` or installable equivalents pass and it can expose via Cloudflare Tunnel or public IPv4. Fallback: provision Hetzner CX22 Ubuntu 24.04 only if `hcloud context active` and `HCLOUD_TOKEN` are available; before create, run `hcloud ssh-key list -o json | tee .omo/evidence/recova-mcp-deployment/task-9-hcloud-ssh-keys.json`, select the first usable key with `/opt/homebrew/bin/python3 -c 'import json; keys=json.load(open(".omo/evidence/recova-mcp-deployment/task-9-hcloud-ssh-keys.json")); names=[k["name"] for k in keys if k.get("name")]; raise SystemExit("no hcloud ssh keys") if not names else print(names[0])'`, store it as `HETZNER_SSH_KEY_NAME`, then run `hcloud server create --name recova-mcp-lab --type cx22 --image ubuntu-24.04 --location fsn1 --ssh-key "$HETZNER_SSH_KEY_NAME" -o json | tee .omo/evidence/recova-mcp-deployment/task-9-hcloud-create.json`. Write `.omo/evidence/recova-mcp-deployment/task-9-server-target.json` before any DNS mutation. Must not mutate GoDaddy/Cloudflare without rollback command and pre-change evidence.
  Parallelization: Wave 3 | Blocked by: 1, 2, 4, 7, 8 | Blocks: 11, 12
  References (executor has NO interview context - be exhaustive): `recova-mcp-lab.slit.company` approved endpoint; Cloudflare Create DNS Record docs `https://developers.cloudflare.com/api/resources/dns/subresources/records/methods/create/`; Cloudflare Update DNS Record docs `https://developers.cloudflare.com/api/resources/dns/subresources/records/methods/edit/`; GoDaddy Domains API docs `https://developer.godaddy.com/doc/endpoint/domains`; MCP transport docs `https://modelcontextprotocol.io/specification/2025-03-26/basic/transports`
  Acceptance criteria (agent-executable): `ssh mini 'hostname; docker --version || true; caddy version || true' | tee .omo/evidence/recova-mcp-deployment/task-9-mini-preflight.txt` OR `hcloud server describe recova-mcp-lab -o json > .omo/evidence/recova-mcp-deployment/task-9-hcloud-server.json`; `task-9-server-target.json` names `target_kind`, `host`, `ip_or_tunnel`, and `rollback`; `dig +short recova-mcp-lab.slit.company` returns the intended IP/CNAME after DNS mutation; `curl -I https://recova-mcp-lab.slit.company/mcp` returns HTTPS headers; Caddy cert log shows certificate issued or valid; rollback command saved in `.omo/evidence/recova-mcp-deployment/task-9-rollback.sh` with secrets redacted.
  QA scenarios (name the exact tool + invocation): happy HTTP: `curl -i https://recova-mcp-lab.slit.company/mcp -H 'Accept: application/json, text/event-stream'`, PASS if status is auth rejection not network/TLS failure; failure HTTP: `curl -i http://recova-mcp-lab.slit.company/mcp`, PASS if redirected to HTTPS or rejected safely, evidence `.omo/evidence/recova-mcp-deployment/task-9-live-http.txt`.
  Commit: N | external deployment evidence only unless deployment manifests changed in todo 8.

- [x] 10. Supabase remote deployment and lab trace proof
  What to do / Must NOT do: Link to the Supabase project under `dev@slit.company`, push migrations, create storage bucket/policies, seed nonsecret reference data, and prove lab trace insert/read. Must not print service-role key or raw PII.
  Parallelization: Wave 3 | Blocked by: 3, 5, 6 | Blocks: 11, 12
  References (executor has NO interview context - be exhaustive): Supabase CLI docs `https://supabase.com/docs/reference/cli/introduction`; Supabase managing environments docs `https://supabase.com/docs/guides/deployment/managing-environments`; Supabase API keys docs `https://supabase.com/docs/guides/getting-started/api-keys`; migrations from todo 3; trace writer from todo 5.
  Acceptance criteria (agent-executable): `supabase link --project-ref "$SUPABASE_PROJECT_REF"` completes for the lab project; `supabase db push --dry-run | tee .omo/evidence/recova-mcp-deployment/task-10-db-push-dry-run.txt` and `supabase db push | tee .omo/evidence/recova-mcp-deployment/task-10-db-push.txt` both captured when `SUPABASE_PROJECT_REF` and auth are present; SQL count proves trace/evaluation tables exist; storage bucket exists; RLS/policy smoke passes. If project ref/auth is absent, record BLOCKED with exact missing env names, not a fake pass.
  QA scenarios (name the exact tool + invocation): happy auxiliary DB CLI: `/opt/homebrew/bin/python3 scripts/recova_mcp/supabase_remote_smoke.py --mode service-write-read --url-env SUPABASE_URL --service-key-env SUPABASE_SERVICE_ROLE_KEY --run-id recova-task-10-smoke --out .omo/evidence/recova-mcp-deployment/task-10-supabase-remote.json`, PASS if the run id returns one redacted `judgment_runs` row and one redacted `tool_traces` row; failure DB CLI: `/opt/homebrew/bin/python3 scripts/recova_mcp/supabase_remote_smoke.py --mode anon-read-deny --url-env SUPABASE_URL --anon-key-env SUPABASE_ANON_KEY --run-id recova-task-10-smoke --out .omo/evidence/recova-mcp-deployment/task-10-rls-deny.json`, PASS if anonymous/read token gets denied or empty restricted trace rows.
  Commit: N | external Supabase evidence only unless migration fixes are needed.

- [x] 11. End-to-end MCP client smoke and bold judgment trace
  What to do / Must NOT do: Run real client-compatible MCP requests against `https://recova-mcp-lab.slit.company/mcp`: unauthenticated rejection, authenticated list tools, fixture StopGate/judgment run, execution-probe block, Supabase trace row capture. Must not use a tool argument named `authorization`, `token`, or `bearer`.
  Parallelization: Wave 4 | Blocked by: 8, 9, 10 | Blocks: 12
  References (executor has NO interview context - be exhaustive): `docs/product/debt-collection-ontology/mcp-domain-server-contract.md:53`; `docs/product/debt-collection-ontology/mcp-domain-server-contract.md:71`; `docs/product/debt-collection-ontology/mcp-domain-server-contract.md:85`; `docs/product/debt-collection-ontology/mcp-domain-server-contract.md:233`; OpenAI MCP docs `https://developers.openai.com/api/docs/mcp`; Anthropic MCP connector docs `https://platform.claude.com/docs/en/agents-and-tools/mcp-connector`
  Acceptance criteria (agent-executable): generated MCP client smoke script returns exactly 16 debt tools; no generic TrustGraph tools; StopGate response has source refs and decision; execution probe blocked; Supabase trace row exists for the run id.
  QA scenarios (name the exact tool + invocation): happy HTTP: `python scripts/recova_mcp/mcp_lab_smoke.py --url https://recova-mcp-lab.slit.company/mcp --token-env MCP_LAB_BEARER_TOKEN --out .omo/evidence/recova-mcp-deployment/task-11-mcp-smoke.json`, PASS if JSON includes `tool_count=16`, `generic_tools=[]`, `decision` in Korean, and Supabase `trace_status=recorded`; failure HTTP: `env -u MCP_LAB_BEARER_TOKEN python scripts/recova_mcp/mcp_lab_smoke.py --url https://recova-mcp-lab.slit.company/mcp --out .omo/evidence/recova-mcp-deployment/task-11-no-auth.json --expect-auth-failure`, PASS if rejected and no trace row stores token.
  Commit: Y | `test(deploy): add Recova MCP lab smoke`

- [x] 12. Operations, rollback, and handoff
  What to do / Must NOT do: Add operational runbook for restart, logs, backup, token rotation, DNS rollback, Supabase evidence retention, failure triage, and stable promotion criteria. Must not mark production-ready; this is lab-ready.
  Parallelization: Wave 5 | Blocked by: 11 | Blocks: final verification
  References (executor has NO interview context - be exhaustive): all prior evidence under `.omo/evidence/recova-mcp-deployment/`; `docs/tech-specs/iam.md:125`; `docs/product/debt-collection-ontology/mcp-domain-server-contract.md:212`; `docs/product/debt-collection-ontology/mcp-domain-server-contract.md:222`
  Acceptance criteria (agent-executable): runbook exists; commands are copy/paste executable; rollback script dry-run prints planned removals without deleting retained Supabase evidence; final live smoke evidence is linked.
  QA scenarios (name the exact tool + invocation): happy auxiliary CLI: `scripts/recova_mcp/rollback_lab.sh --dry-run | tee .omo/evidence/recova-mcp-deployment/task-12-rollback-dry-run.txt`, PASS if DNS/proxy/container/secrets rollback steps are listed and evidence-retention default is preserve; failure auxiliary CLI: `/opt/homebrew/bin/python3 scripts/recova_mcp/check_runbook.py --runbook docs/product/debt-collection-ontology/recova-mcp-lab-runbook.md --evidence-root .omo/evidence/recova-mcp-deployment --require task-11-mcp-smoke.json --simulate-missing task-11-mcp-smoke.json --out .omo/evidence/recova-mcp-deployment/task-12-runbook-check.json`, PASS if the checker exits nonzero and reports only the missing evidence filename.
  Commit: Y | `docs(deploy): document Recova MCP lab operations`

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.
- [x] F1. Plan compliance audit - verify every Todo has acceptance criteria, happy/failure QA, evidence path, dependency, and commit rule; evidence `.omo/evidence/recova-mcp-deployment/f1-plan-compliance.md`.
- [x] F2. Code quality review - review diff for debt-only mode, Supabase trace writer, deployment scripts, and migrations; run targeted tests; evidence `.omo/evidence/recova-mcp-deployment/f2-code-review.md`.
- [x] F3. Real manual QA - rerun live HTTPS `/mcp` unauth/auth, tool count, execution block, Supabase trace, DNS, TLS; evidence `.omo/evidence/recova-mcp-deployment/f3-real-qa.txt`.
- [x] F4. Scope fidelity - confirm no generic TrustGraph public surface, no raw PII/secrets in evidence, no execution actions, Supabase used as memory/eval not MCP runtime; evidence `.omo/evidence/recova-mcp-deployment/f4-scope-fidelity.md`.

## Commit strategy
- Commit each verified source/config/docs unit atomically with Conventional Commits.
- External-state evidence only tasks do not commit unless they create/fix tracked artifacts.
- Never stage real `.env`, tokens, Supabase service keys, Cloudflare tokens, screenshots showing secrets, or raw legal documents.
- Expected commits:
  - `feat(lab): add Supabase experiment memory schema`
  - `feat(legal-mcp): add debt-only lab server mode`
  - `feat(lab): record redacted MCP evaluation traces`
  - `feat(lab): capture bold judgment evaluation labels`
  - `chore(deploy): add redacted lab secret checks`
  - `build(deploy): package Recova MCP lab server`
  - `test(deploy): add Recova MCP lab smoke`
  - `docs(deploy): document Recova MCP lab operations`
- Final commit touching this plan should include footer: `Plan: .omo/plans/recova-mcp-deployment.md`.

## Success criteria
- `https://recova-mcp-lab.slit.company/mcp` resolves over HTTPS and rejects missing auth.
- An authorized MCP client gets exactly the 16 Recova debt-brain tools.
- No generic TrustGraph tools are externally visible from the lab endpoint.
- Fixture evaluation and live MCP smoke produce Korean decisions with source refs, confidence, failure labels, and evidence capture.
- Execution probes for filing/contacting/attachment/payment/collection are blocked as `unknown_tool` or rejected review-safe intent.
- Supabase contains redacted trace/evaluation rows for a live run and refuses/filters raw PII.
- Cloudflare/GoDaddy DNS authority and rollback are recorded with no secrets printed.
- Docker/Caddy restart survives process restart or reboot-level smoke.
- Client config notes exist for Hermes/generic MCP, Claude, and OpenAI/ChatGPT-compatible MCP clients.
- Final evidence bundle exists under `.omo/evidence/recova-mcp-deployment/` and all final verification wave items approve.
