from __future__ import annotations

from pathlib import Path

from tests.utils.claim_domain_pipeline_support import (
    REPO_ROOT,
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
from trustgraph_legal.domain_decisions import DomainDecisionRequest, evaluate_claim_domain_decision
from trustgraph_legal.mcp_domain import invoke_tool


def test_domain_ontology_v1_pipeline_runs_synthetic_claim_scenarios(tmp_path: Path) -> None:
    # Given: the minimized manual fixture and synthetic claim-domain scenario bundle.
    bundle = load_bundle()
    scenarios = scenario_list(bundle)
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
    assert json_object(inventory["counts"])["route_candidates"] == len(scenarios)
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
