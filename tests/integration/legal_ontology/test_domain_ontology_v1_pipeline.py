from __future__ import annotations

from pathlib import Path

from trustgraph_legal.debtor_context_types import JsonObject
from trustgraph_legal.domain_decisions import DomainDecisionRequest, evaluate_claim_domain_decision
from trustgraph_legal.mcp_domain import invoke_tool
from tests.utils.claim_domain_pipeline_support import (
    REPO_ROOT,
    Scenario,
    adapter_payload,
    adapt_synthetic_debtor_graph,
    assert_fixture_safe,
    assert_no_leakage,
    domain_source_ids,
    finance_review_codes,
    int_value,
    json_object,
    load_bundle,
    mcp_result,
    object_list,
    only,
    run_manual_inventory,
    run_resource_validators,
    scenario_list,
)
from tests.utils.workflow_scenario_expectations import REQUIRED_SEMIREAL_SCENARIOS, WorkflowExpectation, workflow_expectations


def test_domain_ontology_v1_pipeline_runs_synthetic_claim_scenarios(tmp_path: Path) -> None:
    # Given: the minimized manual fixture and synthetic claim-domain scenario bundle.
    bundle = load_bundle()
    scenarios = scenario_list(bundle)
    workflow_expectation_by_id = workflow_expectations(bundle)
    assert set(REQUIRED_SEMIREAL_SCENARIOS) <= set(workflow_expectation_by_id)
    assert_fixture_safe(bundle, domain_source_ids())

    # When: the manual extractor and cross-resource validators run on committed resources.
    inventory = run_manual_inventory(tmp_path)
    validator_outputs = run_resource_validators()
    adapter_projection = adapt_synthetic_debtor_graph()
    review_codes = finance_review_codes()
    decisions = {
        scenario.scenario_id: evaluate_claim_domain_decision(
            DomainDecisionRequest(
                adapter_payload(scenario),
                workflow_state=scenario.workflow_state,
                finance_review_codes=scenario.finance_review_codes,
            ),
        )
        for scenario in scenarios
    }
    mcp_decisions = {
        scenario.scenario_id: mcp_result(
            invoke_tool(
                "evaluate_claim_domain_decision",
                {
                    "claim_domain_payload": adapter_payload(scenario),
                    "workflow_state": scenario.workflow_state,
                    "finance_review_codes": list(scenario.finance_review_codes),
                },
                REPO_ROOT,
            ),
        )
        for scenario in scenarios
    }

    # Then: every layer is exercised with route diversity and advisory-only outputs.
    manual_route_count = int_value(json_object(inventory["counts"])["route_candidates"])
    assert manual_route_count > 0
    assert len(scenarios) >= manual_route_count
    assert all(output.startswith("PASS ") for output in validator_outputs)
    assert int_value(json_object(adapter_projection["summary"])["route_candidates"]) > 0
    assert {"statutory_or_complex_interest", "payment_allocation_conflict"} <= set(review_codes)
    assert {str(only(object_list(decision["route_decisions"]))["status"]) for decision in decisions.values()} == {
        "possible",
        "missing_facts",
        "blocked",
        "review_required",
    }
    for scenario in scenarios:
        decision = decisions[scenario.scenario_id]
        route_decision = only(object_list(decision["route_decisions"]))
        action_packet = only(object_list(decision["action_packet_candidates"]))
        assert route_decision["route_id"] == scenario.route_id
        assert route_decision["status"] == scenario.expected_status
        assert action_packet["packet_type"] == scenario.expected_packet_type
        assert action_packet["direct_execution_allowed"] is False
        assert "filing_destination" not in action_packet
        assert "debtor_contact_payload" not in action_packet
        assert scenario.expected_review_codes <= tuple(
            str(item["code"]) for item in object_list(decision["review_items"])
        )
        assert_workflow_envelope(decision)
        assert_workflow_envelope(mcp_decisions[scenario.scenario_id])
        workflow_expectation = workflow_expectation_by_id.get(scenario.scenario_id)
        if workflow_expectation is not None:
            assert_workflow_expectation(decision, workflow_expectation)
            assert_workflow_expectation(mcp_decisions[scenario.scenario_id], workflow_expectation)
        assert mcp_decisions[scenario.scenario_id]["schema_version"] == "trustgraph-claim-domain-decision/v1"
        assert_no_leakage(decision)
        assert_no_leakage(mcp_decisions[scenario.scenario_id])

    packet_types = {scenario.expected_packet_type for scenario in scenarios}
    for packet_type in packet_types:
        packet = mcp_result(invoke_tool("explain_claim_action_packet", {"packet_type": packet_type}, REPO_ROOT))
        assert packet["packet_type"] == packet_type
        assert packet["direct_execution_allowed"] is False
        assert_no_leakage(packet)


def test_claim_domain_fixture_safety_rejects_raw_fields_and_unknown_sources() -> None:
    # Given: a generated fixture copy with an unsafe raw field and an unknown legal source.
    bundle = load_bundle()
    scenarios = object_list(bundle["scenarios"])
    first = json_object(scenarios[0])
    first["raw_text"] = "unsafe synthetic raw marker"
    first["legal_source_refs"] = ["unknown-legal-source"]

    # When / Then: the fixture safety gate rejects it before domain evaluation.
    try:
        assert_fixture_safe(bundle, domain_source_ids())
    except AssertionError as error:
        assert "raw_text" in str(error) or "unknown legal source" in str(error)
    else:
        raise AssertionError("unsafe fixture was accepted")


def test_claim_domain_workflow_support_survives_without_projection() -> None:
    # Given: semireal scenarios whose structured support remains nested in workflow_support.
    bundle = load_bundle()
    scenarios = {scenario.scenario_id: scenario for scenario in scenario_list(bundle)}
    expectations = workflow_expectations(bundle)

    # When / Then: the direct domain and MCP surfaces still produce exact workflow outcomes.
    for scenario_id in REQUIRED_SEMIREAL_SCENARIOS:
        scenario = scenarios[scenario_id]
        payload = _nested_workflow_support_payload(scenario)
        direct_decision = evaluate_claim_domain_decision(
            DomainDecisionRequest(
                payload,
                workflow_state=scenario.workflow_state,
                route_ids=(scenario.route_id,),
                finance_review_codes=scenario.finance_review_codes,
            ),
        )
        mcp_decision = mcp_result(
            invoke_tool(
                "evaluate_claim_domain_decision",
                {
                    "claim_domain_payload": payload,
                    "workflow_state": scenario.workflow_state,
                    "route_ids": [scenario.route_id],
                    "finance_review_codes": list(scenario.finance_review_codes),
                },
                REPO_ROOT,
            ),
        )
        assert_workflow_expectation(direct_decision, expectations[scenario_id])
        assert_workflow_expectation(mcp_decision, expectations[scenario_id])
        assert_no_leakage(direct_decision)
        assert_no_leakage(mcp_decision)


def assert_workflow_envelope(decision: JsonObject) -> None:
    workflow = json_object(decision["workflow_judgment"])
    operator_next_steps = object_list(decision["operator_next_steps"])

    assert workflow["schema_version"] == "trustgraph-collection-workflow-judgment/v1"
    assert workflow["current_stage"]
    assert workflow["next_best_actions"] or workflow["remediation_loop"]
    assert workflow["source_refs"]
    assert workflow["non_execution_semantics"] == "advisory_only_human_review_required"
    assert operator_next_steps
    assert operator_next_steps[0]["review_status"] == "human_review_required"
    assert operator_next_steps[0]["non_execution_semantics"] == "advisory_only_human_review_required"


def assert_workflow_expectation(decision: JsonObject, expectation: WorkflowExpectation) -> None:
    workflow = json_object(decision["workflow_judgment"])
    action = only(object_list(workflow["next_best_actions"]))

    assert workflow["current_stage"] == expectation.stage
    assert action["action_type"] == expectation.action
    assert workflow["posture"] == expectation.posture
    assert workflow["remediation_loop"] == expectation.remediation_loop


def _nested_workflow_support_payload(scenario: Scenario) -> JsonObject:
    payload = adapter_payload(scenario)
    for key in ("evidence_checkpoint", "finance_bridge", "legal_checkpoints"):
        _ = payload.pop(key, None)
    if scenario.workflow_support is not None:
        payload["workflow_support"] = scenario.workflow_support
    return payload
