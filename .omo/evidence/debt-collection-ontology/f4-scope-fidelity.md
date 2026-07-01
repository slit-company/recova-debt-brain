# F4 Scope Fidelity

Date: 2026-06-30

## Result

APPROVE.

## Confirmed Boundaries

- No Hermes-specific code, prompts, or runtime assumptions were added.
- The MCP domain server is agent-agnostic and registered into the existing `trustgraph-mcp` physical service.
- No person-facing SaaS UI or workflow screen was added.
- No direct legal filing, debtor contact, payment collection, attachment initiation, or irreversible business execution was implemented.
- Recommendations remain StopGate-bound and non-executing.
- Rule behavior uses curated v0 rule sources and governance review; no live statute crawler or automatic production rule updater was added.
- Client/native memory is not treated as source of truth; the MCP contract defines server source refs and reviewed rules as authoritative.
- Public path arguments are repo-root bounded and outside-root attempts return a stable redacted rejection.
- Bearer tokens are validated through the TrustGraph gateway before MCP tool handlers run and are handled through MCP auth context/token resolver, not public tool arguments.
- Gateway token validation plus internal IAM `authorise_many` scope authorization controls debt-tool scopes; reader-like authorization decisions can call read/graph tools but are rejected from governance-scope tools.
- Raw graph complexity is hidden behind the 16-tool domain contract.

## Final Scope Check Commands

- `python3 scripts/legal_ontology/evaluate_packet.py --fixtures tests/fixtures/legal-ocr/manifest.json --out .omo/evidence/debt-collection-ontology/task-10-eval.json`: passed.
- `/opt/homebrew/bin/python3 -m pytest tests/unit/legal_ontology -q`: 39 passed.
- `/opt/homebrew/bin/python3 -m pytest tests/integration/legal_ontology/test_mcp_tools.py -q`: 3 passed.
- Actual gateway-backed MCP HTTP smoke: passed with bad-token rejection, gateway `whoami` validation, no public WebSocket `iam/authorise-many`, internal scope-authorizer decisions, reader governance-scope rejection, and token non-echo.

## Notes

The implementation stays inside the ontology/domain brain scope requested by the user. It builds the head for an external agent to use, not the agent-specific body and not a human UI.
