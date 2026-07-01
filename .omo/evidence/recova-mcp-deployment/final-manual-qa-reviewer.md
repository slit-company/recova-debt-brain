# Final Manual QA Reviewer - Recova MCP Deployment

Verdict: APPROVE

Review timestamp: 2026-07-02 KST
Scope: `/Users/cosmos/dev/ontology/trustgraph`
Plan: `.omo/plans/recova-mcp-deployment.md`
Criteria reviewed: C001, C002, C003

## Commands Run

Read-only inspection:

```sh
pwd && git status --short && ls -l .omo/plans/recova-mcp-deployment.md .omo/evidence/recova-mcp-deployment/task-11-mcp-smoke.json .omo/evidence/recova-mcp-deployment/task-11-no-auth.json .omo/evidence/recova-mcp-deployment/task-10-trace-count.json .omo/evidence/recova-mcp-deployment/task-12-rollback-dry-run.txt .omo/evidence/recova-mcp-deployment/f4-sensitive-scan.txt
rg -n "C001|C002|C003|Criteria|Acceptance|Completion|rollback|MCP|Supabase|auth" .omo/plans/recova-mcp-deployment.md
sed -n '1,220p' .omo/evidence/recova-mcp-deployment/task-11-mcp-smoke.json
sed -n '1,220p' .omo/evidence/recova-mcp-deployment/task-11-no-auth.json
sed -n '1,220p' .omo/evidence/recova-mcp-deployment/task-10-trace-count.json
sed -n '1,260p' .omo/evidence/recova-mcp-deployment/task-12-rollback-dry-run.txt
sed -n '1,80p' .omo/evidence/recova-mcp-deployment/f4-sensitive-scan.txt
sed -n '1,220p' .omo/evidence/recova-mcp-deployment/ulw-record-c001.json
sed -n '1,220p' .omo/evidence/recova-mcp-deployment/ulw-record-c002.json
sed -n '1,220p' .omo/evidence/recova-mcp-deployment/ulw-record-c003.json
jq '{status, auth_failure, tool_count, expected_tool_count, generic_tools, execution_tools, decision, trace_status}' .omo/evidence/recova-mcp-deployment/task-11-mcp-smoke.json
jq '{status, auth_failure, error_type}' .omo/evidence/recova-mcp-deployment/task-11-no-auth.json
jq '{status, recent_count, recent_tools}' .omo/evidence/recova-mcp-deployment/task-10-trace-count.json
wc -c .omo/evidence/recova-mcp-deployment/task-11-mcp-smoke.json .omo/evidence/recova-mcp-deployment/task-11-no-auth.json .omo/evidence/recova-mcp-deployment/task-10-trace-count.json .omo/evidence/recova-mcp-deployment/task-12-rollback-dry-run.txt .omo/evidence/recova-mcp-deployment/f4-sensitive-scan.txt .omo/evidence/recova-mcp-deployment/final-review-https-unauth.txt .omo/evidence/recova-mcp-deployment/final-review-http-unauth.txt
```

Fresh live unauthenticated HTTP checks:

```sh
curl -i -sS --max-time 20 -H 'Accept: application/json, text/event-stream' https://recova-mcp-lab.slit.company/mcp | tee .omo/evidence/recova-mcp-deployment/final-review-https-unauth.txt
curl -i -sS --max-time 20 http://recova-mcp-lab.slit.company/mcp | tee .omo/evidence/recova-mcp-deployment/final-review-http-unauth.txt
```

## Evidence Summary

- C001 PASS: fresh HTTPS unauth probe returned `HTTP/2 401` with `invalid_token`; existing authenticated smoke evidence reports `status=ok`, `tool_count=16`, `generic_tools=[]`, `execution_tools=[]`, Korean `decision=보류`, and `trace_status=recorded`.
- C002 PASS: existing unauth client smoke reports `status=auth_rejected`; authenticated smoke confirms no generic or execution tools on the public surface; sensitive scan reports `NO_FINDINGS`.
- C003 PASS: rollback dry-run lists native MCP stop, tunnel ingress disable, Cloudflare DNS route removal, Supabase evidence preservation, credential rotation guidance, and rollback verification command. Supabase trace evidence reports `recent_count=5`.

## manualQa

### surfaceEvidence

| scenario id | criterion reference | surface | exact invocation | verdict | artifactRefs |
|---|---|---|---|---|---|
| S1 | C001 | Live HTTPS MCP endpoint, unauthenticated | `curl -i -sS --max-time 20 -H 'Accept: application/json, text/event-stream' https://recova-mcp-lab.slit.company/mcp` | PASS: returned `HTTP/2 401` and `Authentication required` rather than network/TLS failure | A1 |
| S2 | C001 | Existing authenticated MCP smoke evidence | `jq '{status, auth_failure, tool_count, expected_tool_count, generic_tools, execution_tools, decision, trace_status}' .omo/evidence/recova-mcp-deployment/task-11-mcp-smoke.json` | PASS: 16 expected tools, no generic/execution tools, Korean decision, trace recorded | A3 |
| S3 | C001 | Existing Supabase trace-count evidence | `jq '{status, recent_count, recent_tools}' .omo/evidence/recova-mcp-deployment/task-10-trace-count.json` | PASS: `status=ok`, `recent_count=5`, recent tools include debt MCP tools | A5 |
| S4 | C003 | Rollback dry-run evidence | `sed -n '1,260p' .omo/evidence/recova-mcp-deployment/task-12-rollback-dry-run.txt` | PASS: rollback commands and Supabase evidence-preservation default are documented | A6 |
| S5 | C003 | Sensitive scan evidence | `sed -n '1,80p' .omo/evidence/recova-mcp-deployment/f4-sensitive-scan.txt` | PASS: file contains `NO_FINDINGS` | A7 |

### adversarialCases

| scenario id | criterion reference | adversarial class | expected behavior | verdict | artifactRefs |
|---|---|---|---|---|---|
| ACASE1 | C002 | Missing bearer token over HTTPS | Reject request without exposing tools or accepting MCP session | PASS: fresh HTTPS probe returned `401` with `invalid_token` and `Authentication required` | A1 |
| ACASE2 | C002 | Plain HTTP request to MCP path | Redirect or reject safely; no successful unauthenticated access | PASS: fresh HTTP probe returned `401 Unauthorized` with bearer challenge | A2 |
| ACASE3 | C002 | Client smoke with token env unset | Reject unauthenticated client smoke and do not record an authenticated trace | PASS: evidence reports `status=auth_rejected`, `auth_failure=true` | A4 |
| ACASE4 | C002 | Generic TrustGraph or execution tool exposure | Public tool list must contain no generic TrustGraph tools and no execution actions | PASS: authenticated smoke reports `generic_tools=[]` and `execution_tools=[]` | A3 |
| ACASE5 | C003 | Evidence hygiene for secrets/raw PII | Sensitive scan must report no findings in deployment evidence | PASS: sensitive scan artifact reports `NO_FINDINGS` | A7 |

### artifactRefs

| id | kind | description | path |
|---|---|---|---|
| A1 | HTTP transcript | Fresh unauthenticated HTTPS `/mcp` probe, captured with headers and body | `.omo/evidence/recova-mcp-deployment/final-review-https-unauth.txt` |
| A2 | HTTP transcript | Fresh unauthenticated plain HTTP `/mcp` probe, captured with headers and body | `.omo/evidence/recova-mcp-deployment/final-review-http-unauth.txt` |
| A3 | JSON evidence | Existing authenticated MCP smoke: 16 debt tools, no generic/execution tools, Korean decision, trace recorded | `.omo/evidence/recova-mcp-deployment/task-11-mcp-smoke.json` |
| A4 | JSON evidence | Existing unauthenticated MCP smoke: auth rejection | `.omo/evidence/recova-mcp-deployment/task-11-no-auth.json` |
| A5 | JSON evidence | Existing Supabase trace-count proof | `.omo/evidence/recova-mcp-deployment/task-10-trace-count.json` |
| A6 | Text evidence | Existing rollback dry-run receipt and evidence-retention default | `.omo/evidence/recova-mcp-deployment/task-12-rollback-dry-run.txt` |
| A7 | Text evidence | Existing sensitive scan result | `.omo/evidence/recova-mcp-deployment/f4-sensitive-scan.txt` |
| A8 | Plan evidence | Existing criterion record for C001 | `.omo/evidence/recova-mcp-deployment/ulw-record-c001.json` |
| A9 | Plan evidence | Existing criterion record for C002 | `.omo/evidence/recova-mcp-deployment/ulw-record-c002.json` |
| A10 | Plan evidence | Existing criterion record for C003 | `.omo/evidence/recova-mcp-deployment/ulw-record-c003.json` |

## Cleanup Receipt

- No `.env` files were read or printed.
- No DNS, Supabase, server, Cloudflare, GoDaddy, tunnel, or runtime mutation commands were run.
- No local dev server, tmux session, browser, or desktop automation was started for this review.
- New artifacts written by this review:
  - `.omo/evidence/recova-mcp-deployment/final-review-https-unauth.txt`
  - `.omo/evidence/recova-mcp-deployment/final-review-http-unauth.txt`
  - `.omo/evidence/recova-mcp-deployment/final-manual-qa-reviewer.md`
- Artifact non-empty check passed for all reviewed required evidence and fresh HTTP artifacts.

## Final Decision

APPROVE: C001-C003 have enough live and recorded evidence for the Recova MCP deployment completion gate. No blocker was found in the requested unauthenticated live checks or required evidence inspection.
