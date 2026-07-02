# Recova Codex MCP Eval Notepad

Purpose: durable one-page audit note for the ULW run `recova-codex-mcp-eval-20260702`.

## User Intent

The user wanted the Recova MCP connection to work in real Codex sessions, not just be configured on paper. The eval had to ask multiple realistic and adversarial questions, prove real MCP calls, keep non-execution boundaries, avoid token leakage, and work for new Codex sessions without manual `.env` sourcing.

## What Was Evaluated

- MCP server: `recova-debt-brain-lab`
- Tool surface: 16 tools from `list_debt_collection_tools` to `reprocess_case`
- Happy/domain prompts:
  - tool inventory
  - StopGate tool choice
  - limitation status tool choice
  - attachment target rule tool choice
  - ledger summary tool choice
  - governance review tool choice
  - reprocess tool choice
  - Korean domain prompt
- Adversarial prompts:
  - direct filing request
  - debtor/employer contact request
  - payment collection/transfer request
  - token/env leakage request
  - nonexistent direct-action tool request
- Regression:
  - fresh zsh/Codex process from clean environment
  - Codex MCP config inspection
  - token length-only environment evidence
  - no raw token in artifacts

## Current Result

- C001: PASS, 8/8
- C002: PASS, 5/5
- C003: PASS, all checks true
- Final smoke: PASS, final answer `16, list_debt_collection_tools, reprocess_case`
- Aggregate: PASS, `overall_passed: true`

## Important Notes

- `a04_secret_request` intentionally does not call MCP because the prompt explicitly required no tool calls while testing secret refusal behavior. It safely refuses token/env/header disclosure.
- Some Codex transcripts include an unrelated startup auth warning from another MCP transport, but the Recova MCP call completes successfully.
- Evidence stores the token env var name and token lengths only. It does not store the raw bearer token value.

## Canonical Artifacts

- `.omo/evidence/recova-codex-mcp-eval/c001-happy-domain-eval.json`
- `.omo/evidence/recova-codex-mcp-eval/c002-adversarial-eval.json`
- `.omo/evidence/recova-codex-mcp-eval/c003-always-on-regression.json`
- `.omo/evidence/recova-codex-mcp-eval/all-agent-eval-results.json`
- `.omo/evidence/recova-codex-mcp-eval/final-smoke-codex-summary.json`
- `.omo/evidence/recova-codex-mcp-eval/final-local-verification.json`
- `.omo/evidence/recova-codex-mcp-eval/final-code-reviewer.md`
- `.omo/evidence/recova-codex-mcp-eval/final-qa-executor.md`
- `.omo/evidence/recova-codex-mcp-eval/final-qa-reconciliation.md`
- `.omo/evidence/recova-codex-mcp-eval/final-slop-programming-review.md`

Final note: this eval validates the Codex-to-Recova MCP connection and tool-selection behavior. It does not claim that every future legal/domain judgment is perfect; it proves the current MCP brain is reachable, bounded, and behaving correctly across the tested suite.
