# RW4 Security/Safety Review

ReviewClaim: RW4 PASS

Severity: NONE
Blockers: none

## Scope

Verifier-only review for team `debt-brain-structural-depth`, lane RW4 `review-security`.
No product files were edited.

Audited touched structural-depth deliverables for:

- data leakage, raw PII/OCR/contact/filing/local path payloads
- secret/env var leakage in deliverables
- public admin/write/deploy surfaces
- debtor contact, court filing, seizure, payment demand, and ledger mutation
- authoritative finance balance output
- LLM/free-text legal clearance
- MCP tool registry/order changes

Older remote/auth docs and auth-boundary tests exist in the repo, but they were not touched by this wave and are out of scope for this review lane.

## Evidence

- Read team guide/state and the structural-depth plan.
- Inspected current changed inventory from `git diff --name-status` and untracked files.
- Inspected workflow/security-sensitive modules:
  - `trustgraph_legal/workflow_judgments.py`
  - `trustgraph_legal/domain_workflow_integration.py`
  - `trustgraph_legal/evidence_quality.py`
  - `trustgraph_legal/finance_review_bridge.py`
  - `trustgraph_legal/legal_workflow_checkpoints.py`
  - `trustgraph_legal/domain_decisions.py`
- Codegraph confirmed additive decision flow: `evaluate_claim_domain_decision` calls `build_domain_workflow_output`; MCP registry remains 25 tools with the accepted claim-domain tail.
- Scoped structural-depth JSON/output scan passed:
  - `JSON_PAYLOAD_SECURITY_OK files=8`
  - exact forbidden payload keys absent for raw/source text, contact payloads, filing/court destinations, remaining balance, and authoritative balance.
- Focused security regression tests passed:
  - `15 passed`, one existing transient pytest `asyncio_mode` warning.
- Manual surface probes passed:
  - `RW4_MANUAL_SURFACE_OK scenarios=8`
  - `RW4_FINANCE_AUTHORITY_OK finance_review_item=present authoritative_fields=absent`
  - `RW4_LEGAL_CLEARANCE_BOUNDARY_OK stage=title_acquisition`
  - `RW4_MCP_AUTH_ARG_ECHO_OK`
- MCP order smoke passed with repo-supported transient deps:
  - `MCP_ORDER_OK count=25 tail=list_claim_domain_routes,explain_collection_workflow_state,evaluate_claim_domain_decision,explain_claim_action_packet`
- Changed module scan passed:
  - `NO_NETWORK_LLM_ENV_EXEC_IN_CHANGED_MODULES files=6`

## Findings

- No raw PII, raw OCR, debtor contact payload, court/filing destination, local absolute path payload, or secret value was found in touched structural-depth output surfaces.
- No new public admin/write/deploy surface was found.
- No debtor contact, court filing, seizure, payment demand, production ledger mutation, or production storage mutation was found.
- Finance remains non-authoritative. Finance signals are review/hold inputs; emitted decision surfaces do not expose `remaining_balance` or true collectable balance authority.
- Legal clearance remains static/checkpoint driven. A free-text legal-clearance probe did not clear a legal checkpoint.
- MCP tool order remains 25 tools; no tool registry expansion or reorder was found.

## Caveats

- A broad all-docs scan finds older remote/auth docs naming env vars and auth headers. Those files were not touched by this wave and are already called out in prior verifier artifacts as out of scope.
- The structural-depth plan itself includes literal scan patterns such as env var names and the workspace path; those are guardrail recipe text, not secret values or deliverable payloads.
- System `/usr/bin/python3` is Python 3.9 and cannot run this repo directly; verification used `uv run` with explicit transient dependencies, matching prior verifier practice.
