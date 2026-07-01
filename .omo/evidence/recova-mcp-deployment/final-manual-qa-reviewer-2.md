APPROVE

Final manual QA reviewer 2 verdict: APPROVE. I reviewed only the requested public/no-auth evidence and ran fresh no-auth curls against the public MCP endpoint. I did not read `.env`, request bearer tokens, or print secrets.

## manualQa

### surfaceEvidence

| scenario id | criterion reference | surface | exact invocation | verdict | artifactRefs |
|---|---|---|---|---|---|
| SE-01 | task-11-mcp-smoke.json status/tool inventory/decision/status fields | Filesystem JSON evidence | `jq '{status, tool_count, generic_tools, execution_tools, decision: (.decision // .korean_decision // .decision_ko), trace_status, evaluation_status, judgment_status}' .omo/evidence/recova-mcp-deployment/task-11-mcp-smoke.json` | PASS: status `ok`, tool_count `16`, generic_tools `[]`, execution_tools `[]`, Korean decision `보류`, trace/evaluation/judgment statuses all `recorded`. | ART-01 |
| SE-02 | task-11-no-auth.json auth rejection | Filesystem JSON evidence | `jq '{status, auth_error_detected, error_summary}' .omo/evidence/recova-mcp-deployment/task-11-no-auth.json` | PASS: status `auth_rejected`, auth_error_detected `true`, error_summary contains `401 Unauthorized` for `https://recova-mcp-lab.slit.company/mcp`. | ART-02 |
| SE-03 | final-review HTTPS/HTTP unauth artifacts show 401 | Filesystem HTTP transcripts | `sed -n '1,120p' .omo/evidence/recova-mcp-deployment/final-review-https-unauth.txt` and `sed -n '1,120p' .omo/evidence/recova-mcp-deployment/final-review-http-unauth.txt` | PASS: HTTPS transcript shows `HTTP/2 401`; HTTP transcript shows `HTTP/1.1 401 Unauthorized`; both include `www-authenticate`/`Www-Authenticate` Bearer invalid_token and `Authentication required`. | ART-03, ART-04 |
| SE-04 | task-9 mini native restart evidence | Filesystem text evidence | `sed -n '1,160p' .omo/evidence/recova-mcp-deployment/task-9-mini-native-restart.txt` | PASS: contains `old_pid=85097`, `new_pid=89515`, `local_origin_http_status=401`, and invalid_token auth-required response body. | ART-05 |
| SE-05 | task-10 trace count consistency | Filesystem JSON evidence | `jq '.' .omo/evidence/recova-mcp-deployment/task-10-trace-count.json` | PASS: status `ok`; `tables.evaluation_runs.recent_count` is `1`; `tables.judgment_runs.recent_count` is `1`; `tables.tool_traces.recent_count` is `5`; latest trace links to evaluation_run_id `d931d7ea-9a06-44ac-b299-baa0be68dc53` and judgment_run_id `6f8c4c55-aa06-476b-ac82-b9b3fcc4a3b1`. | ART-06 |
| SE-06 | live public HTTPS no-auth behavior | Public HTTPS endpoint | `curl -i --max-time 20 https://recova-mcp-lab.slit.company/mcp` | PASS: fresh run returned `HTTP/2 401`, Bearer `invalid_token`, `Authentication required`, and JSON body `{"error": "invalid_token", "error_description": "Authentication required"}`. | ART-07 |
| SE-07 | live public HTTP no-auth behavior | Public HTTP endpoint | `curl -i --max-time 20 http://recova-mcp-lab.slit.company/mcp` | PASS: fresh run returned `HTTP/1.1 401 Unauthorized`, Bearer `invalid_token`, `Authentication required`, and JSON body `{"error": "invalid_token", "error_description": "Authentication required"}`. | ART-07 |

### adversarialCases

| scenario id | criterion reference | adversarial class | expected behavior | verdict | artifactRefs |
|---|---|---|---|---|---|
| AC-01 | Public/no-auth HTTPS behavior | Missing bearer token over HTTPS | Reject before MCP access with 401 Unauthorized and Bearer auth challenge. | PASS: fresh HTTPS curl returned 401 with Bearer invalid_token/authentication-required evidence. | ART-07 |
| AC-02 | Public/no-auth HTTP behavior | Missing bearer token over HTTP | Reject before MCP access with 401 Unauthorized and Bearer auth challenge. | PASS: fresh HTTP curl returned 401 Unauthorized with Bearer invalid_token/authentication-required evidence. | ART-07 |
| AC-03 | Tool surface hardening | Generic or execution tool exposure in smoke evidence | No generic tools and no execution tools exposed. | PASS: `generic_tools` and `execution_tools` are both empty arrays while expected domain tool_count remains 16. | ART-01 |
| AC-04 | Persistence linkage | Orphaned trace/judgment/evaluation evidence after smoke | Recent evaluation, judgment, and tool trace rows exist, with at least one linked trace tying evaluation_run_id and judgment_run_id together. | PASS: latest tool trace links the recent evaluation run and recent judgment run IDs. | ART-06 |
| AC-05 | Artifact consistency | Stored unauth transcripts disagree with fresh public curls | Stored HTTPS/HTTP artifacts and fresh curls should all show auth rejection, not redirect/open access/success. | PASS: stored transcripts and fresh curls consistently show 401 auth rejection. | ART-03, ART-04, ART-07 |

### artifactRefs

| id | kind | description | path |
|---|---|---|---|
| ART-01 | JSON evidence | task-11 smoke evidence, 930 bytes, status/tool/decision/recording fields verified. | `/Users/cosmos/dev/ontology/trustgraph/.omo/evidence/recova-mcp-deployment/task-11-mcp-smoke.json` |
| ART-02 | JSON evidence | task-11 no-auth evidence, 468 bytes, auth rejection and 401 Unauthorized summary verified. | `/Users/cosmos/dev/ontology/trustgraph/.omo/evidence/recova-mcp-deployment/task-11-no-auth.json` |
| ART-03 | HTTP transcript | Stored HTTPS unauth transcript, 818 bytes, HTTP/2 401 Bearer invalid_token verified. | `/Users/cosmos/dev/ontology/trustgraph/.omo/evidence/recova-mcp-deployment/final-review-https-unauth.txt` |
| ART-04 | HTTP transcript | Stored HTTP unauth transcript, 860 bytes, HTTP/1.1 401 Unauthorized Bearer invalid_token verified. | `/Users/cosmos/dev/ontology/trustgraph/.omo/evidence/recova-mcp-deployment/final-review-http-unauth.txt` |
| ART-05 | Text evidence | mini native restart evidence, 131 bytes, old_pid/new_pid/local 401 verified. | `/Users/cosmos/dev/ontology/trustgraph/.omo/evidence/recova-mcp-deployment/task-9-mini-native-restart.txt` |
| ART-06 | JSON evidence | trace count evidence, 2307 bytes, recent evaluation/judgment/tool_trace rows and linkage verified. | `/Users/cosmos/dev/ontology/trustgraph/.omo/evidence/recova-mcp-deployment/task-10-trace-count.json` |
| ART-07 | Review artifact | This final manual QA artifact contains the fresh public no-auth curl invocations and observed verdicts without storing secrets or tokens. | `/Users/cosmos/dev/ontology/trustgraph/.omo/evidence/recova-mcp-deployment/final-manual-qa-reviewer-2.md` |

## Fresh curl observations

- HTTPS no-auth, `curl -i --max-time 20 https://recova-mcp-lab.slit.company/mcp`: returned `HTTP/2 401`, `www-authenticate: Bearer error="invalid_token", error_description="Authentication required"`, and JSON body `{"error": "invalid_token", "error_description": "Authentication required"}`.
- HTTP no-auth, `curl -i --max-time 20 http://recova-mcp-lab.slit.company/mcp`: returned `HTTP/1.1 401 Unauthorized`, `Www-Authenticate: Bearer error="invalid_token", error_description="Authentication required"`, and JSON body `{"error": "invalid_token", "error_description": "Authentication required"}`.

## Notes

- `task-10-trace-count.json` does not use top-level `recent_evaluation_runs`, `recent_judgment_runs`, or `linked_tool_traces` field names. Its `tables.*` schema still satisfies the criterion: it shows recent `evaluation_runs`, recent `judgment_runs`, and linked `tool_traces`.
- No authenticated path was exercised. No bearer token was used or requested.
