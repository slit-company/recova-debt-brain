# FINAL3 refresh manual QA report

VerificationClaim: F3 REFRESH APPROVED

Scope: verifier-only refresh after Todo 6/7 real-boundary fix and Todo 8 refresh. Product files were not edited.

Direct QA line:

`F3_REFRESH_MANUAL_QA_APPROVED scenarios=8 surfaces=direct,mcp unsafe_fields=absent authority_fields=absent`

Runtime note:

- `/usr/bin/python3` is still Python 3.9 and cannot import `typing.TypeAlias` from the repo test helper.
- The refresh verifier used the bundled workspace Python: `/Users/slit/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3`.

Checks performed:

- Loaded current `tests/fixtures/claim-domain-v1/synthetic_claim_states.json`.
- Loaded exact expectations from `tests/utils/workflow_scenario_expectations.py`.
- Drove all eight required scenarios through direct `evaluate_claim_domain_decision`.
- Drove all eight required scenarios through local MCP dispatcher `invoke_tool("evaluate_claim_domain_decision", ...)`.
- Verified direct and MCP summaries matched for each scenario.
- Verified exact expected workflow `current_stage`, first `next_best_actions[].action_type`, `posture`, and `remediation_loop`.
- Verified `non_execution_semantics == advisory_only_human_review_required` on decisions, workflow judgments, actions, operator next steps, and action packet candidates.
- Verified action packet candidates keep `direct_execution_allowed is False`.
- Scanned decision payloads for forbidden unsafe/authority fields: `raw_text`, `source_text`, `body`, `excerpt`, `source_path`, `debtor_contact_payload`, `filing_destination`, `court_destination`, `court_destination_payload`, `remaining_balance`, `collectable_balance_authority`.
- Scanned serialized outputs for local path and bearer/auth leakage tokens.

Observed direct/MCP-matching scenario outcomes:

| scenario_id | current_stage | action | posture | remediation_loop |
| --- | --- | --- | --- | --- |
| premature_litigation_review | title_acquisition | confirm_service_finality_execution_clause | resolve_title_service_finality_and_execution_clause_before_enforcement | legal_precondition_review_loop |
| evidence_completion_loop | evidence_completion | collect_missing_evidence | complete_source_backed_fact_package_before_escalation | evidence_completion_loop |
| title_acquisition_loop | title_acquisition | acquire_or_confirm_title | resolve_title_service_finality_and_execution_clause_before_enforcement | title_acquisition_loop |
| asset_discovery_loop | asset_discovery | enrich_asset_signals | enrich_asset_targets_and_exemption_risk_before_route_selection | asset_discovery_loop |
| enforcement_ready_review | enforcement_ready | prepare_advisory_packet | prepare_review_packet_only_after_route_and_guardrail_readiness | legal_precondition_review_loop |
| monitoring_low_yield | monitoring | monitor_retry | hold_low_yield_or_blocked_case_with_review_trigger | low_yield_monitoring_loop |
| finance_reconciliation_hold | evidence_completion | reconcile_finance | complete_source_backed_fact_package_before_escalation | finance_reconciliation_loop |
| insolvency_protected_asset_hold | insolvency_protected_asset_review | insolvency_protected_asset_review | hold_or_redirect_before_enforcement_ready_judgment | protected_asset_insolvency_hold |

Blockers: none.

Caveats:

- The strict refresh was run with the bundled workspace Python because the system Python cannot import the current test helper.
- This artifact is verifier-only evidence; it does not stage, commit, or modify product implementation files.
