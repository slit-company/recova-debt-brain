# Final ULW Notepad

Date: 2026-07-01
Session: debt-collection-ontology-final-20260701
Plan: .omo/plans/debt-collection-ontology.md

## Tier

HEAVY.

Reasons:
- Auth/security boundary changed in the MCP server.
- External integration surface is MCP streamable HTTP plus TrustGraph gateway auth.
- The user explicitly requested ULW and asked whether teammode was being used correctly.
- The final result decides whether the ontology brain can be safely attached to external agents.

## Teammode Decision

Existing implementation waves already used durable teammode worktrees and member threads.
For this resume, the remaining work is not a new parallel implementation wave. It is a narrow final gate:
security authz review, code/regression review, goal review, and observable evidence refresh.

Decision: do not create a new durable team. Use focused final-review subagents instead.

## Success Criteria

- C1: MCP streamable HTTP smoke proves gateway token validation, internal IAM scope decisions, no public WebSocket `iam/authorise-many`, bad-token rejection, reader governance denial, and no token echo.
- C2: Adversarial boundary proof covers repo-root path rejection, no authorization as a tool argument, pointer-only source refs, and no raw PII/token/path leakage.
- C3: Regression proof covers legal ontology unit suite, MCP integration tests, Python py_compile, evaluator CLI, diff checks, sensitive scan, and cleanup receipts.

## Current Evidence

- .omo/evidence/debt-collection-ontology/final-mcp-scope-smoke.txt
- .omo/evidence/debt-collection-ontology/final-verification-20260701.txt

## Pending

- Final security reviewer approval.
- Final code quality reviewer approval.
- Final goal gate reviewer approval.
- Mark F1-F4 complete after reviewer gate.
- Update start-work ledger and boulder status.
- Commit the verified source/docs/tests work unit.
