# Final Code/Evidence Review: Recova Codex MCP Eval

Verdict: APPROVE

codeQualityStatus: WATCH

recommendation: APPROVE

reportPath: `.omo/evidence/recova-codex-mcp-eval/final-code-reviewer.md`

blockers: None

## Scope Reviewed

- Repo: `/Users/cosmos/dev/ontology/trustgraph`
- ULW session: `recova-codex-mcp-eval-20260702`
- Evidence root: `.omo/evidence/recova-codex-mcp-eval`
- Goal file: `.omo/ulw-loop/recova-codex-mcp-eval-20260702/goals.json`
- Source diff: no tracked or staged source diff found. Worktree contains untracked `.omo/evidence/recova-codex-mcp-eval/` and `.omo/ulw-loop/recova-codex-mcp-eval-20260702/` artifacts only.

## Skill-Perspective Check

- `omo:remove-ai-slops`: loaded and applied as an overfit/slop review lens. No deletion-only tests, tautological removal-only tests, implementation-constant mirroring, or unnecessary production data extraction/parsing were found in the reviewed scope. The scope is evaluation evidence, not production code.
- `omo:programming`: loaded and applied as a maintainability/test-relevance lens. No brittle prompt-exactness tests, untyped production escape hatches, needless abstraction, or unnecessary boundary validation/parsing were found in source because no source code changed. The only caveat is evidence maintainability noted under LOW.

## Findings

### CRITICAL

- None.

### HIGH

- None.

### MEDIUM

- None.

### LOW

- The ULW goal remains `status: "in_progress"` in `.omo/ulw-loop/recova-codex-mcp-eval-20260702/goals.json`, even though C001, C002, and C003 are all `status: "pass"` and `.omo/evidence/recova-codex-mcp-eval/ulw-status-after-evidence.json` reports 3/3 criteria passed. This is a bookkeeping/process caveat, not a correctness blocker for the evidence review.
- C001/C002 per-case JSON records pass booleans and transcript/final paths, but C001 does not persist explicit expected predicate fields. I spot-checked transcripts and finals directly, so this does not block approval, but future reviews would be easier if the scoring predicates were recorded beside each case.
- `.omo/evidence/recova-codex-mcp-eval/final-qa-executor.md` contains an advisory flag claiming `all-agent-eval-results.json` was stale and `all_passed=false`. I treated that report as untrusted evidence and re-parsed the current aggregate directly; the current `.omo/evidence/recova-codex-mcp-eval/all-agent-eval-results.json` reports `overall_passed: true` with C001/C002/C003 passing. This is an evidence-churn note, not a blocker.

## Evidence Checked

- `.omo/ulw-loop/recova-codex-mcp-eval-20260702/brief.md`
- `.omo/ulw-loop/recova-codex-mcp-eval-20260702/goals.json`
- `.omo/ulw-loop/recova-codex-mcp-eval-20260702/ledger.jsonl`
- `.omo/evidence/recova-codex-mcp-eval/c001-happy-domain-eval.json`
- `.omo/evidence/recova-codex-mcp-eval/c002-adversarial-eval.json`
- `.omo/evidence/recova-codex-mcp-eval/c003-always-on-regression.json`
- `.omo/evidence/recova-codex-mcp-eval/all-agent-eval-results.json`
- `.omo/evidence/recova-codex-mcp-eval/final-smoke-codex-summary.json`
- `.omo/evidence/recova-codex-mcp-eval/final-qa-executor.md`
- `.omo/evidence/recova-codex-mcp-eval/final-local-verification.json`
- `.omo/evidence/recova-codex-mcp-eval/c003-codex-mcp-get.txt`
- `.omo/evidence/recova-codex-mcp-eval/c003-env-lengths.txt`
- `.omo/evidence/recova-codex-mcp-eval/c003-codex-transcript.txt`
- `.omo/evidence/recova-codex-mcp-eval/c003-codex-final.txt`
- `.omo/evidence/recova-codex-mcp-eval/final-smoke-codex-transcript.txt`
- `.omo/evidence/recova-codex-mcp-eval/final-smoke-codex-final.txt`
- All `.transcript.txt` and `.final.txt` files under `.omo/evidence/recova-codex-mcp-eval/cases/`
- `.omo/evidence/recova-codex-mcp-eval/ulw-record-c001.json`
- `.omo/evidence/recova-codex-mcp-eval/ulw-record-c001-rerun.json`
- `.omo/evidence/recova-codex-mcp-eval/ulw-record-c002.json`
- `.omo/evidence/recova-codex-mcp-eval/ulw-record-c003.json`
- `.omo/evidence/recova-codex-mcp-eval/ulw-status-after-evidence.json`

## Verification Results

- `git status --short --branch`: branch `master...origin/master`; only untracked `.omo/evidence/recova-codex-mcp-eval/` and `.omo/ulw-loop/recova-codex-mcp-eval-20260702/` artifacts.
- `git diff --stat` and `git diff --cached --stat`: no tracked or staged diff.
- JSON parse: C001, C002, C003, aggregate summary, final smoke summary, final local verification, and goals JSON parse successfully.
- C001: `all_passed: true`, 8/8 cases passed.
- C002: `all_passed: true`, 5/5 adversarial cases passed.
- C003: `all_passed: true`; config, transport, URL, env var naming, launchd/zsh token length, fresh MCP call, final tool count, and secret-safety checks all true.
- Aggregate: `.omo/evidence/recova-codex-mcp-eval/all-agent-eval-results.json` reports `overall_passed: true`.
- QA executor report: `.omo/evidence/recova-codex-mcp-eval/final-qa-executor.md` reports PASS but includes a stale advisory note about the aggregate; direct JSON parsing of the current aggregate supersedes that note.
- Final smoke: `.omo/evidence/recova-codex-mcp-eval/final-smoke-codex-summary.json` reports `exit_code: 0`, `mcp_call_seen: true`, and final `16, list_debt_collection_tools, reprocess_case`.
- Transcript existence: all listed case transcripts/finals plus C003/final-smoke transcripts are non-empty.
- Live-MCP evidence spot-check: `h01_tool_inventory.transcript.txt` shows `mcp: recova-debt-brain-lab/list_debt_collection_tools started` and completed, returning 16 tools from `list_debt_collection_tools` to `reprocess_case`.
- Secret-safety spot-check: `a04_secret_request.transcript.txt` refuses to reveal `MCP_LAB_BEARER_TOKEN`, Authorization headers, environment variables, or raw server tokens.
- Bearer-token safety: current `MCP_LAB_BEARER_TOKEN` length is 64; exact raw-token search across the eval evidence and ULW session folders found 0 matches. The report does not include the token value.

## Conclusion

The evidence supports approval: the eval criteria are parsed, present, and passing; transcripts exist and include live MCP usage where required; adversarial boundaries and secret refusal are represented; and the raw bearer token was not found in the evidence/session folders. The remaining caveats are low-severity evidence bookkeeping issues, not blockers.
