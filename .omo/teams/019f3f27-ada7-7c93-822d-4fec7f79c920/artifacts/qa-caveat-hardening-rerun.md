# QA Caveat Hardening Rerun

Verdict: APPROVE

## manualQa

```json
{
  "surfaceEvidence": [
    {
      "scenario_id": "premature_litigation_review",
      "criterion_ref": "C001 nested workflow support exact direct decision",
      "surface": "direct evaluate_claim_domain_decision",
      "exact_invocation": "evaluate_claim_domain_decision(DomainDecisionRequest(payload_with_nested_workflow_support, workflow_state=scenario.workflow_state, route_ids=(scenario.route_id,), finance_review_codes=scenario.finance_review_codes))",
      "verdict": "PASS",
      "artifactRefs": [
        "qa-rerun-direct-json"
      ]
    },
    {
      "scenario_id": "evidence_completion_loop",
      "criterion_ref": "C001 nested workflow support exact direct decision",
      "surface": "direct evaluate_claim_domain_decision",
      "exact_invocation": "evaluate_claim_domain_decision(DomainDecisionRequest(payload_with_nested_workflow_support, workflow_state=scenario.workflow_state, route_ids=(scenario.route_id,), finance_review_codes=scenario.finance_review_codes))",
      "verdict": "PASS",
      "artifactRefs": [
        "qa-rerun-direct-json"
      ]
    },
    {
      "scenario_id": "title_acquisition_loop",
      "criterion_ref": "C001 nested workflow support exact direct decision",
      "surface": "direct evaluate_claim_domain_decision",
      "exact_invocation": "evaluate_claim_domain_decision(DomainDecisionRequest(payload_with_nested_workflow_support, workflow_state=scenario.workflow_state, route_ids=(scenario.route_id,), finance_review_codes=scenario.finance_review_codes))",
      "verdict": "PASS",
      "artifactRefs": [
        "qa-rerun-direct-json"
      ]
    },
    {
      "scenario_id": "asset_discovery_loop",
      "criterion_ref": "C001 nested workflow support exact direct decision",
      "surface": "direct evaluate_claim_domain_decision",
      "exact_invocation": "evaluate_claim_domain_decision(DomainDecisionRequest(payload_with_nested_workflow_support, workflow_state=scenario.workflow_state, route_ids=(scenario.route_id,), finance_review_codes=scenario.finance_review_codes))",
      "verdict": "PASS",
      "artifactRefs": [
        "qa-rerun-direct-json"
      ]
    },
    {
      "scenario_id": "enforcement_ready_review",
      "criterion_ref": "C001 nested workflow support exact direct decision",
      "surface": "direct evaluate_claim_domain_decision",
      "exact_invocation": "evaluate_claim_domain_decision(DomainDecisionRequest(payload_with_nested_workflow_support, workflow_state=scenario.workflow_state, route_ids=(scenario.route_id,), finance_review_codes=scenario.finance_review_codes))",
      "verdict": "PASS",
      "artifactRefs": [
        "qa-rerun-direct-json"
      ]
    },
    {
      "scenario_id": "monitoring_low_yield",
      "criterion_ref": "C001 nested workflow support exact direct decision",
      "surface": "direct evaluate_claim_domain_decision",
      "exact_invocation": "evaluate_claim_domain_decision(DomainDecisionRequest(payload_with_nested_workflow_support, workflow_state=scenario.workflow_state, route_ids=(scenario.route_id,), finance_review_codes=scenario.finance_review_codes))",
      "verdict": "PASS",
      "artifactRefs": [
        "qa-rerun-direct-json"
      ]
    },
    {
      "scenario_id": "finance_reconciliation_hold",
      "criterion_ref": "C001 nested workflow support exact direct decision",
      "surface": "direct evaluate_claim_domain_decision",
      "exact_invocation": "evaluate_claim_domain_decision(DomainDecisionRequest(payload_with_nested_workflow_support, workflow_state=scenario.workflow_state, route_ids=(scenario.route_id,), finance_review_codes=scenario.finance_review_codes))",
      "verdict": "PASS",
      "artifactRefs": [
        "qa-rerun-direct-json"
      ]
    },
    {
      "scenario_id": "insolvency_protected_asset_hold",
      "criterion_ref": "C001 nested workflow support exact direct decision",
      "surface": "direct evaluate_claim_domain_decision",
      "exact_invocation": "evaluate_claim_domain_decision(DomainDecisionRequest(payload_with_nested_workflow_support, workflow_state=scenario.workflow_state, route_ids=(scenario.route_id,), finance_review_codes=scenario.finance_review_codes))",
      "verdict": "PASS",
      "artifactRefs": [
        "qa-rerun-direct-json"
      ]
    },
    {
      "scenario_id": "premature_litigation_review",
      "criterion_ref": "C002 nested workflow support exact MCP decision",
      "surface": "MCP invoke_tool(\"evaluate_claim_domain_decision\")",
      "exact_invocation": "invoke_tool(\"evaluate_claim_domain_decision\", {\"claim_domain_payload\": payload_with_nested_workflow_support, \"workflow_state\": scenario.workflow_state, \"route_ids\": [scenario.route_id], \"finance_review_codes\": list(scenario.finance_review_codes)}, REPO_ROOT)",
      "verdict": "PASS",
      "artifactRefs": [
        "qa-rerun-mcp-json"
      ]
    },
    {
      "scenario_id": "evidence_completion_loop",
      "criterion_ref": "C002 nested workflow support exact MCP decision",
      "surface": "MCP invoke_tool(\"evaluate_claim_domain_decision\")",
      "exact_invocation": "invoke_tool(\"evaluate_claim_domain_decision\", {\"claim_domain_payload\": payload_with_nested_workflow_support, \"workflow_state\": scenario.workflow_state, \"route_ids\": [scenario.route_id], \"finance_review_codes\": list(scenario.finance_review_codes)}, REPO_ROOT)",
      "verdict": "PASS",
      "artifactRefs": [
        "qa-rerun-mcp-json"
      ]
    },
    {
      "scenario_id": "title_acquisition_loop",
      "criterion_ref": "C002 nested workflow support exact MCP decision",
      "surface": "MCP invoke_tool(\"evaluate_claim_domain_decision\")",
      "exact_invocation": "invoke_tool(\"evaluate_claim_domain_decision\", {\"claim_domain_payload\": payload_with_nested_workflow_support, \"workflow_state\": scenario.workflow_state, \"route_ids\": [scenario.route_id], \"finance_review_codes\": list(scenario.finance_review_codes)}, REPO_ROOT)",
      "verdict": "PASS",
      "artifactRefs": [
        "qa-rerun-mcp-json"
      ]
    },
    {
      "scenario_id": "asset_discovery_loop",
      "criterion_ref": "C002 nested workflow support exact MCP decision",
      "surface": "MCP invoke_tool(\"evaluate_claim_domain_decision\")",
      "exact_invocation": "invoke_tool(\"evaluate_claim_domain_decision\", {\"claim_domain_payload\": payload_with_nested_workflow_support, \"workflow_state\": scenario.workflow_state, \"route_ids\": [scenario.route_id], \"finance_review_codes\": list(scenario.finance_review_codes)}, REPO_ROOT)",
      "verdict": "PASS",
      "artifactRefs": [
        "qa-rerun-mcp-json"
      ]
    },
    {
      "scenario_id": "enforcement_ready_review",
      "criterion_ref": "C002 nested workflow support exact MCP decision",
      "surface": "MCP invoke_tool(\"evaluate_claim_domain_decision\")",
      "exact_invocation": "invoke_tool(\"evaluate_claim_domain_decision\", {\"claim_domain_payload\": payload_with_nested_workflow_support, \"workflow_state\": scenario.workflow_state, \"route_ids\": [scenario.route_id], \"finance_review_codes\": list(scenario.finance_review_codes)}, REPO_ROOT)",
      "verdict": "PASS",
      "artifactRefs": [
        "qa-rerun-mcp-json"
      ]
    },
    {
      "scenario_id": "monitoring_low_yield",
      "criterion_ref": "C002 nested workflow support exact MCP decision",
      "surface": "MCP invoke_tool(\"evaluate_claim_domain_decision\")",
      "exact_invocation": "invoke_tool(\"evaluate_claim_domain_decision\", {\"claim_domain_payload\": payload_with_nested_workflow_support, \"workflow_state\": scenario.workflow_state, \"route_ids\": [scenario.route_id], \"finance_review_codes\": list(scenario.finance_review_codes)}, REPO_ROOT)",
      "verdict": "PASS",
      "artifactRefs": [
        "qa-rerun-mcp-json"
      ]
    },
    {
      "scenario_id": "finance_reconciliation_hold",
      "criterion_ref": "C002 nested workflow support exact MCP decision",
      "surface": "MCP invoke_tool(\"evaluate_claim_domain_decision\")",
      "exact_invocation": "invoke_tool(\"evaluate_claim_domain_decision\", {\"claim_domain_payload\": payload_with_nested_workflow_support, \"workflow_state\": scenario.workflow_state, \"route_ids\": [scenario.route_id], \"finance_review_codes\": list(scenario.finance_review_codes)}, REPO_ROOT)",
      "verdict": "PASS",
      "artifactRefs": [
        "qa-rerun-mcp-json"
      ]
    },
    {
      "scenario_id": "insolvency_protected_asset_hold",
      "criterion_ref": "C002 nested workflow support exact MCP decision",
      "surface": "MCP invoke_tool(\"evaluate_claim_domain_decision\")",
      "exact_invocation": "invoke_tool(\"evaluate_claim_domain_decision\", {\"claim_domain_payload\": payload_with_nested_workflow_support, \"workflow_state\": scenario.workflow_state, \"route_ids\": [scenario.route_id], \"finance_review_codes\": list(scenario.finance_review_codes)}, REPO_ROOT)",
      "verdict": "PASS",
      "artifactRefs": [
        "qa-rerun-mcp-json"
      ]
    },
    {
      "scenario_id": "mcp-tool-order",
      "criterion_ref": "C004 MCP tool order count=25",
      "surface": "MCP list_tools()",
      "exact_invocation": "list_tools()",
      "verdict": "PASS",
      "artifactRefs": [
        "qa-rerun-tool-order-json"
      ]
    }
  ],
  "adversarialCases": [
    {
      "scenario_id": "premature_litigation_review",
      "criterion_ref": "C003 stripped support fallback advisory-only unsafe-field absence",
      "adversarial_class": "support_fields_stripped",
      "expected_behavior": "direct and MCP decisions remain advisory-only, no top-level/nested support in request, unsafe fields absent from outputs",
      "verdict": "PASS",
      "artifactRefs": [
        "qa-rerun-stripped-fallback-json"
      ]
    },
    {
      "scenario_id": "evidence_completion_loop",
      "criterion_ref": "C003 stripped support fallback advisory-only unsafe-field absence",
      "adversarial_class": "support_fields_stripped",
      "expected_behavior": "direct and MCP decisions remain advisory-only, no top-level/nested support in request, unsafe fields absent from outputs",
      "verdict": "PASS",
      "artifactRefs": [
        "qa-rerun-stripped-fallback-json"
      ]
    },
    {
      "scenario_id": "title_acquisition_loop",
      "criterion_ref": "C003 stripped support fallback advisory-only unsafe-field absence",
      "adversarial_class": "support_fields_stripped",
      "expected_behavior": "direct and MCP decisions remain advisory-only, no top-level/nested support in request, unsafe fields absent from outputs",
      "verdict": "PASS",
      "artifactRefs": [
        "qa-rerun-stripped-fallback-json"
      ]
    },
    {
      "scenario_id": "asset_discovery_loop",
      "criterion_ref": "C003 stripped support fallback advisory-only unsafe-field absence",
      "adversarial_class": "support_fields_stripped",
      "expected_behavior": "direct and MCP decisions remain advisory-only, no top-level/nested support in request, unsafe fields absent from outputs",
      "verdict": "PASS",
      "artifactRefs": [
        "qa-rerun-stripped-fallback-json"
      ]
    },
    {
      "scenario_id": "enforcement_ready_review",
      "criterion_ref": "C003 stripped support fallback advisory-only unsafe-field absence",
      "adversarial_class": "support_fields_stripped",
      "expected_behavior": "direct and MCP decisions remain advisory-only, no top-level/nested support in request, unsafe fields absent from outputs",
      "verdict": "PASS",
      "artifactRefs": [
        "qa-rerun-stripped-fallback-json"
      ]
    },
    {
      "scenario_id": "monitoring_low_yield",
      "criterion_ref": "C003 stripped support fallback advisory-only unsafe-field absence",
      "adversarial_class": "support_fields_stripped",
      "expected_behavior": "direct and MCP decisions remain advisory-only, no top-level/nested support in request, unsafe fields absent from outputs",
      "verdict": "PASS",
      "artifactRefs": [
        "qa-rerun-stripped-fallback-json"
      ]
    },
    {
      "scenario_id": "finance_reconciliation_hold",
      "criterion_ref": "C003 stripped support fallback advisory-only unsafe-field absence",
      "adversarial_class": "support_fields_stripped",
      "expected_behavior": "direct and MCP decisions remain advisory-only, no top-level/nested support in request, unsafe fields absent from outputs",
      "verdict": "PASS",
      "artifactRefs": [
        "qa-rerun-stripped-fallback-json"
      ]
    },
    {
      "scenario_id": "insolvency_protected_asset_hold",
      "criterion_ref": "C003 stripped support fallback advisory-only unsafe-field absence",
      "adversarial_class": "support_fields_stripped",
      "expected_behavior": "direct and MCP decisions remain advisory-only, no top-level/nested support in request, unsafe fields absent from outputs",
      "verdict": "PASS",
      "artifactRefs": [
        "qa-rerun-stripped-fallback-json"
      ]
    }
  ],
  "artifactRefs": [
    {
      "id": "qa-rerun-direct-json",
      "kind": "json",
      "description": "Direct evaluate_claim_domain_decision evidence for all eight semireal scenarios with nested workflow_support only.",
      "path": ".omo/teams/019f3f27-ada7-7c93-822d-4fec7f79c920/artifacts/qa-caveat-hardening-rerun-direct.json"
    },
    {
      "id": "qa-rerun-mcp-json",
      "kind": "json",
      "description": "MCP invoke_tool(\"evaluate_claim_domain_decision\") evidence for all eight semireal scenarios with nested workflow_support only.",
      "path": ".omo/teams/019f3f27-ada7-7c93-822d-4fec7f79c920/artifacts/qa-caveat-hardening-rerun-mcp.json"
    },
    {
      "id": "qa-rerun-stripped-fallback-json",
      "kind": "json",
      "description": "Direct and MCP fallback evidence with all support fields stripped.",
      "path": ".omo/teams/019f3f27-ada7-7c93-822d-4fec7f79c920/artifacts/qa-caveat-hardening-rerun-stripped-fallback.json"
    },
    {
      "id": "qa-rerun-tool-order-json",
      "kind": "json",
      "description": "MCP list_tools order/count evidence.",
      "path": ".omo/teams/019f3f27-ada7-7c93-822d-4fec7f79c920/artifacts/qa-caveat-hardening-rerun-tool-order.json"
    },
    {
      "id": "qa-rerun-summary-json",
      "kind": "json",
      "description": "QA rerun aggregate summary and failure list.",
      "path": ".omo/teams/019f3f27-ada7-7c93-822d-4fec7f79c920/artifacts/qa-caveat-hardening-rerun-summary.json"
    }
  ]
}
```

## Observed Summary

- Direct scenarios: 8/8 PASS
- MCP scenarios: 8/8 PASS
- Stripped fallback scenarios: 8/8 PASS
- MCP tool order: count=25, tail=['list_claim_domain_routes', 'explain_collection_workflow_state', 'evaluate_claim_domain_decision', 'explain_claim_action_packet'], verdict=PASS

## Scenario Fields

| scenario_id | direct stage/action/posture/remediation_loop | MCP stage/action/posture/remediation_loop |
|---|---|---|
| premature_litigation_review | title_acquisition/confirm_service_finality_execution_clause/resolve_title_service_finality_and_execution_clause_before_enforcement/legal_precondition_review_loop | title_acquisition/confirm_service_finality_execution_clause/resolve_title_service_finality_and_execution_clause_before_enforcement/legal_precondition_review_loop |
| evidence_completion_loop | evidence_completion/collect_missing_evidence/complete_source_backed_fact_package_before_escalation/evidence_completion_loop | evidence_completion/collect_missing_evidence/complete_source_backed_fact_package_before_escalation/evidence_completion_loop |
| title_acquisition_loop | title_acquisition/acquire_or_confirm_title/resolve_title_service_finality_and_execution_clause_before_enforcement/title_acquisition_loop | title_acquisition/acquire_or_confirm_title/resolve_title_service_finality_and_execution_clause_before_enforcement/title_acquisition_loop |
| asset_discovery_loop | asset_discovery/enrich_asset_signals/enrich_asset_targets_and_exemption_risk_before_route_selection/asset_discovery_loop | asset_discovery/enrich_asset_signals/enrich_asset_targets_and_exemption_risk_before_route_selection/asset_discovery_loop |
| enforcement_ready_review | enforcement_ready/prepare_advisory_packet/prepare_review_packet_only_after_route_and_guardrail_readiness/legal_precondition_review_loop | enforcement_ready/prepare_advisory_packet/prepare_review_packet_only_after_route_and_guardrail_readiness/legal_precondition_review_loop |
| monitoring_low_yield | monitoring/monitor_retry/hold_low_yield_or_blocked_case_with_review_trigger/low_yield_monitoring_loop | monitoring/monitor_retry/hold_low_yield_or_blocked_case_with_review_trigger/low_yield_monitoring_loop |
| finance_reconciliation_hold | evidence_completion/reconcile_finance/complete_source_backed_fact_package_before_escalation/finance_reconciliation_loop | evidence_completion/reconcile_finance/complete_source_backed_fact_package_before_escalation/finance_reconciliation_loop |
| insolvency_protected_asset_hold | insolvency_protected_asset_review/insolvency_protected_asset_review/hold_or_redirect_before_enforcement_ready_judgment/protected_asset_insolvency_hold | insolvency_protected_asset_review/insolvency_protected_asset_review/hold_or_redirect_before_enforcement_ready_judgment/protected_asset_insolvency_hold |
