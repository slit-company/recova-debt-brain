---
slug: recova-mcp-deployment
status: approved-plan-writing
intent: clear
pending-action: write .omo/plans/recova-mcp-deployment.md
approach: Package and deploy a Recova debt-brain streamable HTTP MCP testbed under slit.company, optimized for aggressive judgment generation, evidence capture, and fast tuning while keeping external real-world execution closed.
---

# Draft: recova-mcp-deployment

## Components (topology ledger)
<!-- Lock the SHAPE before depth. One row per top-level component that can succeed or fail independently. -->
<!-- id | outcome (one line) | status: active|deferred | evidence path -->
1. domain-dns | `recova-mcp-lab.slit.company` hosts the aggressive testbed; `mcp.recova.slit.company` is reserved for a later stable endpoint | active | user approval + docs/product/debt-collection-ontology/mcp-domain-server-contract.md
2. server-packaging | deployable MCP runtime with TrustGraph gateway/IAM/pubsub dependencies and repo resources | active | trustgraph-mcp/trustgraph/mcp_server/mcp.py, trustgraph-mcp/pyproject.toml
3. debt-brain-surface | external agent endpoint exposes Recova debt-brain tools tuned for classification, extraction, case graph, StopGate, and recommendation loops | active | docs/product/debt-collection-ontology/mcp-domain-server-contract.md
4. experiment-capture | every judgment records prompt/client, source_refs, confidence, StopGate result, tool trace, expected answer when available, and failure labels for tuning | active | user direction: set aside worry and design boldly
5. containment | real-world execution actions stay closed, but judgment paths are allowed to be assertive in the lab | active | trustgraph-mcp/trustgraph/mcp_server/auth.py, trustgraph-mcp/trustgraph/mcp_server/legal_tools.py
6. client-onboarding | Hermes, Claude, ChatGPT/OpenAI, and generic MCP clients connect to the lab endpoint and run repeatable smoke/evaluation scenarios | active | official OpenAI/Anthropic/MCP docs
7. operations | healthcheck, logs, evaluation corpus, token rotation notes, rollback, and lab-to-stable promotion rules | active | deployment planning requirement

## Open assumptions (announced defaults)
<!-- Record any default you adopt instead of asking, so the user can veto it at the gate. -->
<!-- assumption | adopted default | rationale | reversible? -->
- Domain decision | `recova-mcp-lab.slit.company` is the canonical v1 lab endpoint; reserve `mcp.recova.slit.company` for stable later | user approved this direction; the name makes the experiment-bed posture explicit | yes
- Transport default | Streamable HTTP at `/mcp` over HTTPS | MCP spec and existing FastMCP server already use streamable HTTP | yes
- Test strategy | tests-after plus real-surface HTTP smoke | deployment plan changes packaging/wiring more than pure library behavior; each todo still needs happy+failure QA | yes
- Risk posture | judgment-open, execution-closed | agents should make bold legal-workflow judgments in the lab, but must not trigger real external collection/legal actions | yes
- Evaluation default | capture wrong answers as first-class training/evaluation artifacts | the fastest path to domain expertise is many judged runs, not premature conservatism | yes
- Hosting decision | Primary target is existing Codex remote host `mini` if it can run Docker/Caddy and expose through Cloudflare Tunnel or public IPv4; fallback is Hetzner CX22 Ubuntu 24.04 via `hcloud` only if `HCLOUD_TOKEN` is already available locally | user approved "your decision"; this makes the server target executable instead of a vague VPS class | yes
- Supabase decision | use account `dev@slit.company` for lab DB/Auth/Storage/vector/evaluation memory, not MCP runtime | Supabase is the experience/log/memory layer; MCP runtime remains Python/Docker | yes
- DNS authority decision | use stored Cloudflare key if Cloudflare is authoritative; otherwise use GoDaddy/cosmos Google only to delegate/confirm `slit.company` DNS authority | user supplied both Cloudflare and GoDaddy context; executor must verify nameservers before mutation | yes

## Findings (cited - path:lines)
- Existing server registers Recova tools into FastMCP through `register_debt_collection_brain_tools`; current full server also registers many generic TrustGraph tools. Evidence: trustgraph-mcp/trustgraph/mcp_server/mcp.py:331-371.
- Debt MCP contract defines 16 canonical tools, groups/scopes, redaction envelope, non-execution boundary, and generic streamable HTTP client config. Evidence: docs/product/debt-collection-ontology/mcp-domain-server-contract.md.
- Auth boundary already expects Authorization header, gateway `whoami`, and IAM scope decisions; bearer token must not be a tool argument. Evidence: trustgraph-mcp/trustgraph/mcp_server/auth.py and trustgraph-mcp/trustgraph/mcp_server/legal_tools.py.
- OpenAI docs say remote MCP servers can be public Internet servers and ChatGPT Apps/custom MCP setup is admin/developer-mode gated for Business/Enterprise/Edu; data-only apps can expose tools without UI resources. Evidence: https://developers.openai.com/api/docs/mcp and https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt.
- Anthropic Messages API MCP connector uses `mcp_servers` plus a toolset; authenticated remote servers can pass `authorization_token`. Evidence: https://platform.claude.com/docs/en/agents-and-tools/mcp-connector.
- MCP streamable HTTP spec uses a single `/mcp` endpoint supporting POST/GET and recommends authentication and Origin validation for HTTP servers. Evidence: https://modelcontextprotocol.io/specification/2025-03-26/basic/transports and https://modelcontextprotocol.io/specification/draft/basic/authorization.

## Decisions (with rationale)
- Intent: CLEAR. User wants a concrete plan and execution track to put the Recova debt brain MCP lab server under `slit.company`; owner decisions have now been supplied.
- Review required: true for this session because the user asked to plan "빡세게" and run with ULW loop; plan gets Metis/Momus-style review before handoff.
- Skill usage: `omo:ulw-plan` for decision-complete planning; CodeGraph for repo grounding; web official docs for external MCP client/deployment constraints; no teammode/subagents yet because user did not explicitly request parallel agents for this planning turn.
- Recommendation: use `recova-mcp-lab.slit.company/mcp` before `mcp.recova.slit.company/mcp`. "staging" sounds like a cautious pre-production clone; "lab" better matches the goal: make many judgments, observe failures, and tune the debt brain quickly.
- Recommendation: start with VPS/VM + Docker Compose + Caddy/Traefik because this repo is still a composite TrustGraph-derived service with gateway/IAM/pubsub expectations; a plain VM keeps deployment transparent while the MCP contract stabilizes.
- Recommendation: expose the Recova debt-brain surface externally, not the full generic TrustGraph surface. For the lab this is not about being timid; it is about keeping the experiment signal clean. If an agent can call broad generic tools, failures become harder to attribute to the debt ontology.
- Recommendation: use simple lab bearer tokens first, carried through the existing TrustGraph gateway/IAM boundary. Supabase Auth may store lab users/sessions, but it must not silently replace MCP Bearer validation unless a later token bridge explicitly mints TrustGraph-compatible tokens.
- Recommendation: make judgments assertive inside the lab. The StopGate engine should return `가능/보류/불가` plus reasons instead of defaulting everything to `보류`; wrong calls should become labeled evidence.
- Recommendation: keep external execution closed in v1. This is not "worry"; it preserves iteration speed because a lab that can actually send notices, contact people, or file legal steps becomes politically and operationally heavy immediately.
- Recommendation: add an evaluation harness as a first-class deployment component. Every agent run should be reproducible from an input packet, tool trace, expected/actual judgment, and human correction.

## Scope IN
- Plan deployable MCP server packaging, lab/stable domains, HTTPS/reverse proxy, lightweight lab auth, client configs, smoke tests, evaluation capture, evidence paths, and commit strategy.
- Plan for Hermes, Claude, ChatGPT/OpenAI, and generic MCP clients to connect to the same endpoint.
- Plan must keep the non-execution boundary while making judgment/evaluation loops aggressive.

## Scope OUT (Must NOT have)
- Do not implement code during planning.
- Do not expose raw OCR text, PII, arbitrary repo paths, or execution actions.
- Do not publish the full generic TrustGraph tool surface to public agents unless the user explicitly chooses that.
- Do not design the lab so conservatively that every uncertain case becomes `보류` and no useful failure data is produced.
- Do not assume a DNS/provider/hosting account exists without recording it as a precondition.

## Open questions
1. Debt-only public mode is required because current `McpServer._register_tools()` registers generic TrustGraph tools before Recova tools. The execution plan must add a legal-only route/mode or prove a reverse-proxy allowlist blocks generic tools.
2. Supabase Auth is lab identity/evaluation metadata unless a later token bridge explicitly maps Supabase sessions into TrustGraph gateway/IAM Bearer tokens.
3. DNS mutation must first prove whether Cloudflare is authoritative for `slit.company`; if not, GoDaddy/cosmos Google is used only to delegate or edit the DNS authority safely.
4. Secrets are never pasted into plan/evidence. Cloudflare API token, Supabase service-role key, gateway secret, MCP lab token, and server `.env` live in local keychain/1Password/env or server secret files with redacted evidence only.
5. Deployment target resolution is explicit: write `task-9-server-target.json` before DNS/TLS. Prefer `mini`; if `mini` is not viable, provision Hetzner with `hcloud`; if neither target can be proven, checkpoint blocked rather than guessing.

## Approval gate
status: approved-plan-writing
pending action: write `.omo/plans/recova-mcp-deployment.md` using the lab-first approach above; user approved "your decision" and provided Supabase/Cloudflare/GoDaddy context
<!-- When exploration is exhausted and unknowns are answered, set status: awaiting-approval. -->
<!-- That durable record is the loop guard: on a later turn read it and resume at the gate instead of re-running exploration. -->
