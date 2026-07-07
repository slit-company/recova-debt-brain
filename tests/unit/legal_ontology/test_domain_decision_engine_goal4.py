from __future__ import annotations

import json
from pathlib import Path

import pytest

from trustgraph_legal.domain_decisions import (
    DomainDecisionError,
    DomainDecisionRequest,
    evaluate_claim_domain_decision,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject = dict[str, JsonValue]


@pytest.mark.parametrize(
    ("route_id", "workflow_state", "fact_handles", "blocker"),
    (
        (
            "bank_account_attachment",
            "execution_route_selection",
            ("enforceable_title", "financial_account_hint", "exempt_claim_or_property_risk"),
            "exempt_claim_or_property_risk",
        ),
        (
            "bank_account_attachment",
            "execution_route_selection",
            ("enforceable_title", "financial_account_hint", "insolvency_stay"),
            "insolvency_stay",
        ),
        (
            "property_disclosure_inquiry_registry",
            "asset_discovery",
            (
                "enforceable_title",
                "asset_disclosure_preconditions",
                "asset_inquiry_preconditions",
                "default_registry_preconditions",
                "service_finality_unproven",
            ),
            "service_finality_unproven",
        ),
        (
            "property_disclosure_inquiry_registry",
            "asset_discovery",
            (
                "enforceable_title",
                "asset_disclosure_preconditions",
                "asset_inquiry_preconditions",
                "default_registry_preconditions",
                "execution_clause_missing",
            ),
            "execution_clause_missing",
        ),
    ),
)
def test_engine_blocks_goal4_stopgate_safety_fact_handles(
    route_id: str,
    workflow_state: str,
    fact_handles: tuple[str, ...],
    blocker: str,
) -> None:
    # Given: an otherwise route-ready adapter payload includes one StopGate safety blocker.
    payload = _adapter_payload((route_id,), fact_handles)

    # When: the deterministic domain decision engine evaluates the route.
    decision = evaluate_claim_domain_decision(
        DomainDecisionRequest(payload, workflow_state=workflow_state),
    )

    # Then: the route remains blocked and any action candidate remains human-review-only.
    route_decision = _only_object(decision["route_decisions"])
    action_candidate = _only_object(decision["action_packet_candidates"])
    assert route_decision["status"] == "blocked"
    assert route_decision["priority_score"] == 0
    assert blocker in _string_list(route_decision["blocking_fact_handles"])
    assert action_candidate["review_status"] == "human_review_required"
    assert action_candidate["direct_execution_allowed"] is False
    assert action_candidate["non_execution_semantics"] == "advisory_only_human_review_required"
    assert "filing_destination" not in action_candidate
    assert "debtor_contact_payload" not in action_candidate


def test_engine_rejects_goal4_stale_finance_model_version(tmp_path: Path) -> None:
    # Given: a request using a finance model resource with a stale model version.
    finance_path = tmp_path / "claim_finance_model_v1.json"
    finance_model = json.loads((REPO_ROOT / "resources/finance/claim_finance_model_v1.json").read_text(encoding="utf-8"))
    finance_model["model_version"] = "recova-claim-finance-model@stale"
    _ = finance_path.write_text(json.dumps(finance_model), encoding="utf-8")
    payload = _adapter_payload(
        ("bank_account_attachment",),
        ("enforceable_title", "financial_account_hint"),
    )

    # When / Then: the engine rejects stale finance independently from stale legal sources.
    with pytest.raises(DomainDecisionError) as error:
        _ = evaluate_claim_domain_decision(
            DomainDecisionRequest(
                payload,
                workflow_state="execution_route_selection",
                finance_path=finance_path,
            ),
        )

    assert error.value.reason_code == "stale_finance_model_version"
    assert error.value.location == "resources/finance/claim_finance_model_v1.json"


def _adapter_payload(route_ids: tuple[str, ...], fact_handles: tuple[str, ...]) -> JsonObject:
    legal_source_refs = (
        "kr-law-l009290-m268837-a223",
        "kr-law-l009290-m268837-a229",
        "kr-law-l009290-m268837-a246",
        "kr-law-l009930-m267359-a593",
        "kr-law-l010910-m268669-a12",
    )
    return {
        "schema_version": "trustgraph-claim-domain-adapter/v1",
        "domain_ontology_version": "recova-debt-collection-v1@1.0.0",
        "claim_root": {
            "claim_id": "claim:fixture",
            "claim_ref": "claim:fixture",
            "source_refs": ["fixture:source#claim"],
        },
        "fact_handles": [
            {
                "fact_id": f"fact:{fact_handle}",
                "claim_id": "claim:fixture",
                "fact_handle": fact_handle,
                "source_refs": [f"fixture:source#{fact_handle}"],
            }
            for fact_handle in fact_handles
        ],
        "route_candidates": [
            {
                "route_id": route_id,
                "domain_route_id": route_id,
                "claim_id": "claim:fixture",
                "domain_legal_source_refs": list(legal_source_refs),
                "direct_execution_allowed": False,
                "domain_review_status": "approved_static_v1",
            }
            for route_id in route_ids
        ],
        "source_refs": ["fixture:source#claim", "fixture:source#title"],
        "legal_source_refs": list(legal_source_refs),
        "non_execution_semantics": "adapter_projection_only_human_review_required",
        "pii_profile": {"raw_text_included": False, "source_text_included": False},
    }


def _object_list(value: JsonValue) -> list[JsonObject]:
    assert isinstance(value, list)
    objects: list[JsonObject] = []
    for item in value:
        assert isinstance(item, dict)
        objects.append(item)
    return objects


def _string_list(value: JsonValue) -> list[str]:
    assert isinstance(value, list)
    strings: list[str] = []
    for item in value:
        assert isinstance(item, str)
        strings.append(item)
    return strings


def _only_object(value: JsonValue) -> JsonObject:
    objects = _object_list(value)
    assert len(objects) == 1
    return objects[0]
