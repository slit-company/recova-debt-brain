from __future__ import annotations

import json

from trustgraph_legal.workflow_judgments import evaluate_workflow_judgment
from tests.utils.claim_domain_pipeline_support import load_bundle, scenario_list
from tests.utils.workflow_scenario_expectations import (
    REQUIRED_SEMIREAL_SCENARIOS,
    workflow_expectations,
)
from tests.unit.legal_ontology.workflow_scenario_requests import scenario_workflow_request
from tests.unit.legal_ontology.workflow_judgment_helpers import (
    action_types,
    encoded_without_unsafe_fields,
    evidence_request,
    fact,
    payload,
    reason_codes,
    route_request,
    route_decision,
    signal,
    string_list,
    title_request,
    unsafe_guardrail_request,
)

def test_evidence_completion_routes_weak_or_conflicted_evidence_to_completion_loop() -> None:
    # Given: evidence review signals are present before any legal or route readiness can be trusted.
    workflow_request = evidence_request(
        {
            "schema_version": "trustgraph-evidence-quality-check/v1",
            "decision": "review_required",
            "workflow_signals": [
                signal("placeholder_source_ref", "evidence", ("fixture:evidence#placeholder",)),
            ],
            "pii_profile": {"raw_text_included": False, "source_text_included": False},
        },
    )

    # When: the workflow judgment engine consumes the support surfaces.
    judgment = evaluate_workflow_judgment(workflow_request)

    # Then: it keeps the operator in evidence completion and does not expose raw source text.
    assert judgment["schema_version"] == "trustgraph-collection-workflow-judgment/v1"
    assert judgment["current_stage"] == "evidence_completion"
    assert judgment["posture"] == "complete_source_backed_fact_package_before_escalation"
    assert action_types(judgment) == ["collect_missing_evidence"]
    assert "evidence_missing_or_conflicted" in string_list(judgment, "premature_actions")
    assert "evidence_quality" in string_list(judgment, "missing_inputs")
    assert judgment["remediation_loop"] == "evidence_completion_loop"
    assert judgment["source_refs"] == [
        "fixture:claim#root",
        "fixture:evidence#placeholder",
        "playbook:stage:evidence_completion",
    ]
    assert encoded_without_unsafe_fields(judgment)


def test_title_acquisition_routes_missing_title_to_title_loop() -> None:
    # Given: legal checkpoints report the title gate as missing.
    workflow_request = title_request()

    # When: workflow judgment is evaluated.
    judgment = evaluate_workflow_judgment(workflow_request)

    # Then: title acquisition is the next operator loop.
    assert judgment["current_stage"] == "title_acquisition"
    assert action_types(judgment) == ["acquire_or_confirm_title"]
    assert judgment["remediation_loop"] == "title_acquisition_loop"
    assert "enforcement_title" in string_list(judgment, "missing_inputs")
    assert "enforcement_title_missing" in string_list(judgment, "premature_actions")
    assert reason_codes(judgment) == ["missing_enforcement_title"]


def test_asset_discovery_routes_missing_asset_signal_before_execution_choice() -> None:
    # Given: legal/evidence/finance are clear but route judgment lacks an asset target.
    workflow_request = route_request(
        (
            route_decision(
                "missing_facts",
                missing_fact_handles=("bank_account_hint",),
                reason_code="required_fact_missing",
            ),
        ),
    )

    # When: workflow judgment is evaluated.
    judgment = evaluate_workflow_judgment(workflow_request)

    # Then: the case moves to asset discovery instead of premature route selection.
    assert judgment["current_stage"] == "asset_discovery"
    assert action_types(judgment) == ["enrich_asset_signals"]
    assert judgment["remediation_loop"] == "asset_discovery_loop"
    assert "asset_signal" in string_list(judgment, "missing_inputs")
    assert "asset_signal_missing_or_low_yield" in string_list(judgment, "premature_actions")


def test_enforcement_ready_returns_advisory_packet_without_balance_authority() -> None:
    # Given: all support surfaces are clear and a route is advisory-possible.
    workflow_request = route_request(
        (
            route_decision(
                "possible",
                reason_code="required_facts_present",
            ),
        ),
        payload(
            fact("fact:title", "enforceable_title", True),
            fact("fact:asset", "bank_account_hint", True),
        ),
    )

    # When: workflow judgment is evaluated.
    judgment = evaluate_workflow_judgment(workflow_request)

    # Then: it prepares only an advisory packet and never claims executable balance authority.
    assert judgment["current_stage"] == "enforcement_ready"
    assert action_types(judgment) == ["prepare_advisory_packet"]
    assert judgment["premature_actions"] == []
    assert judgment["missing_inputs"] == []
    assert judgment["remediation_loop"] == "legal_precondition_review_loop"
    assert judgment["review_items"] == []
    assert judgment["non_execution_semantics"] == "advisory_only_human_review_required"
    encoded = json.dumps(judgment, ensure_ascii=False)
    assert "collectable_balance_authority" not in encoded
    assert "remaining_balance" not in encoded
    assert encoded_without_unsafe_fields(judgment)


def test_low_yield_monitoring_uses_monitoring_loop() -> None:
    # Given: the payload contains a source-backed low-yield signal.
    workflow_request = route_request(
        (
            route_decision(
                "missing_facts",
                missing_fact_handles=("bank_account_hint",),
                reason_code="asset_signal_missing_or_low_yield",
            ),
        ),
        payload(
            fact("fact:low-yield", "low_yield_collection_signal", True),
        ),
    )

    # When: workflow judgment is evaluated.
    judgment = evaluate_workflow_judgment(workflow_request)

    # Then: the next action is monitoring, not direct execution or debtor contact.
    assert judgment["current_stage"] == "monitoring"
    assert action_types(judgment) == ["monitor_retry"]
    assert judgment["remediation_loop"] == "low_yield_monitoring_loop"
    assert judgment["non_execution_semantics"] == "advisory_only_human_review_required"


def test_guardrails_reject_raw_excerpts_and_preserve_advisory_only_semantics() -> None:
    # Given: every input surface tries to carry unsafe raw text or execution-looking fields.
    workflow_request = unsafe_guardrail_request()

    # When: workflow judgment is evaluated.
    judgment = evaluate_workflow_judgment(workflow_request)

    # Then: output remains structured, advisory-only, and unsafe-field free.
    encoded = json.dumps(judgment, ensure_ascii=False)
    assert judgment["non_execution_semantics"] == "advisory_only_human_review_required"
    assert judgment["pii_profile"] == {
        "raw_text_included": False,
        "source_text_included": False,
        "debtor_contact_payload_included": False,
        "filing_destination_included": False,
        "court_destination_payload_included": False,
    }
    assert "raw debtor statement" not in encoded
    assert "do not include me" not in encoded
    assert "collectable_balance_authority" not in encoded
    assert "remaining_balance" not in encoded


def test_review_items_scrub_nested_unsafe_support_fields() -> None:
    # Given: support review signals carry nested raw text, contact, filing, and balance authority fields.
    workflow_request = evidence_request(
        {
            "schema_version": "trustgraph-evidence-quality-check/v1",
            "decision": "review_required",
            "workflow_signals": [
                {
                    **signal("nested_unsafe_probe", "evidence", ("fixture:evidence#nested",)),
                    "details": {
                        "raw_text": "nested raw text must not leave the workflow engine",
                        "debtor_contact_payload": {"phone": "010-0000-0000"},
                        "children": [
                            {
                                "filing_destination": "court endpoint",
                                "source_path": "/Users/slit/private/source.pdf",
                                "remaining_balance": {"amount": 123},
                                "safe_code": "keep-me",
                            },
                        ],
                    },
                },
            ],
            "pii_profile": {"raw_text_included": False, "source_text_included": False},
        },
    )

    # When: the workflow judgment engine reflects review items for operator attention.
    judgment = evaluate_workflow_judgment(workflow_request)

    # Then: nested unsafe keys are removed while safe structured fields can remain.
    encoded = json.dumps(judgment, ensure_ascii=False)
    assert "nested raw text must not leave the workflow engine" not in encoded
    assert "010-0000-0000" not in encoded
    assert "/Users/slit/private/source.pdf" not in encoded
    assert '"raw_text":' not in encoded
    assert '"debtor_contact_payload":' not in encoded
    assert '"filing_destination":' not in encoded
    assert '"source_path":' not in encoded
    assert '"remaining_balance":' not in encoded
    assert "safe_code" in encoded


def test_semireal_fixture_workflow_expectations_cover_practical_operator_judgment() -> None:
    bundle = load_bundle()
    scenarios = {scenario.scenario_id: scenario for scenario in scenario_list(bundle)}
    expectations = workflow_expectations(bundle)

    assert set(REQUIRED_SEMIREAL_SCENARIOS) <= set(expectations)
    for scenario_id in REQUIRED_SEMIREAL_SCENARIOS:
        scenario = scenarios[scenario_id]
        expectation = expectations[scenario_id]
        judgment = evaluate_workflow_judgment(scenario_workflow_request(scenario))

        assert judgment["current_stage"] == expectation.stage
        assert action_types(judgment) == [expectation.action]
        assert judgment["posture"] == expectation.posture
        assert judgment["remediation_loop"] == expectation.remediation_loop
        assert judgment["non_execution_semantics"] == "advisory_only_human_review_required"
        assert encoded_without_unsafe_fields(judgment)
