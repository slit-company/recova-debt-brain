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
SOURCE_VERSION = "recova-debt-collection-domain-sources@v1.0.0"
JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject = dict[str, JsonValue]


def test_engine_returns_advisory_payload_for_possible_missing_and_blocked_routes() -> None:
    # Given: three PII-safe claim-domain adapter outputs with possible, missing, and blocked facts.
    possible_payload = _adapter_payload(
        ("bank_account_attachment",),
        ("enforceable_title", "financial_account_hint"),
    )
    missing_payload = _adapter_payload(
        ("bank_account_attachment",),
        ("enforceable_title",),
    )
    blocked_payload = _adapter_payload(
        ("bank_account_attachment",),
        ("enforceable_title", "financial_account_hint", "insolvency_stay"),
    )

    # When: the deterministic domain decision engine evaluates each payload.
    possible = evaluate_claim_domain_decision(
        DomainDecisionRequest(possible_payload, workflow_state="execution_route_selection"),
    )
    missing = evaluate_claim_domain_decision(
        DomainDecisionRequest(missing_payload, workflow_state="execution_route_selection"),
    )
    blocked = evaluate_claim_domain_decision(
        DomainDecisionRequest(blocked_payload, workflow_state="execution_route_selection"),
    )

    # Then: every response has the stable advisory schema required by Todo 11.
    for payload in (possible, missing, blocked):
        assert set(payload) >= {
            "schema_version",
            "claim_ref",
            "workflow_state",
            "route_decisions",
            "review_items",
            "action_packet_candidates",
            "source_refs",
            "pii_profile",
            "non_execution_semantics",
        }
        assert payload["schema_version"] == "trustgraph-claim-domain-decision/v1"
        assert payload["claim_ref"] == "claim:fixture"
        assert payload["workflow_state"] == "execution_route_selection"
        assert payload["non_execution_semantics"] == "advisory_only_human_review_required"
        assert payload["pii_profile"] == {
            "raw_text_included": False,
            "source_text_included": False,
            "debtor_contact_payload_included": False,
            "filing_destination_included": False,
        }
        assert "fixture:source#title" in _string_list(payload["source_refs"])
        encoded = json.dumps(payload, ensure_ascii=False)
        assert '"raw_text":' not in encoded
        assert "debtor_phone" not in encoded
        assert "/" + "Users" + "/" not in encoded

    # Then: possible routes remain advisory and prepare only human-review packet candidates.
    possible_decision = _only_object(possible["route_decisions"])
    possible_packet = _only_object(possible["action_packet_candidates"])
    assert possible_decision["route_id"] == "bank_account_attachment"
    assert possible_decision["status"] == "possible"
    assert possible_packet["packet_type"] == "legal_action_review"
    assert possible_packet["review_status"] == "human_review_required"
    assert possible_packet["direct_execution_allowed"] is False
    assert possible_packet["non_execution_semantics"] == "advisory_only_human_review_required"
    assert "filing_destination" not in possible_packet
    assert "debtor_contact_payload" not in possible_packet

    # Then: missing and blocked cases expose review items without mutating route semantics.
    missing_decision = _only_object(missing["route_decisions"])
    blocked_decision = _only_object(blocked["route_decisions"])
    assert missing_decision["status"] == "missing_facts"
    assert missing_decision["missing_fact_handles"] == ["financial_account_hint"]
    assert {str(item["code"]) for item in _object_list(missing["review_items"])} >= {
        "missing_route_fact",
    }
    assert blocked_decision["status"] == "blocked"
    assert "insolvency_stay" in _string_list(blocked_decision["blocking_fact_handles"])
    assert {str(item["code"]) for item in _object_list(blocked["review_items"])} >= {
        "route_blocked",
    }


def test_engine_keeps_finance_review_codes_as_review_required_items() -> None:
    # Given: a route-ready payload with a finance review trigger from the finance model boundary.
    payload = _adapter_payload(
        ("bank_account_attachment",),
        ("enforceable_title", "financial_account_hint"),
    )

    # When: the engine evaluates with a finance review code.
    decision = evaluate_claim_domain_decision(
        DomainDecisionRequest(
            payload,
            workflow_state="execution_route_selection",
            finance_review_codes=("payment_allocation_conflict",),
        ),
    )

    # Then: route evaluation becomes review-required and the review item is source-traceable.
    route_decision = _only_object(decision["route_decisions"])
    assert route_decision["status"] == "review_required"
    finance_items = [
        item
        for item in _object_list(decision["review_items"])
        if item["code"] == "payment_allocation_conflict"
    ]
    assert finance_items
    assert finance_items[0]["category"] == "finance"
    assert finance_items[0]["source_refs"]
    action_packet = _only_object(decision["action_packet_candidates"])
    assert action_packet["direct_execution_allowed"] is False
    assert action_packet["non_execution_semantics"] == "advisory_only_human_review_required"
    assert "filing_destination" not in action_packet
    assert "debtor_contact_payload" not in action_packet


def test_engine_rejects_unknown_route_id() -> None:
    # Given: an otherwise valid adapter payload that asks for an unknown route id.
    payload = _adapter_payload(("unknown_route",), ("enforceable_title",))

    # When / Then: the engine rejects it with a typed failure instead of fabricating a route result.
    with pytest.raises(DomainDecisionError) as error:
        _ = evaluate_claim_domain_decision(
            DomainDecisionRequest(payload, workflow_state="execution_route_selection"),
        )

    assert error.value.reason_code == "unknown_route_id"
    assert error.value.location == "route_ids[0]"


def test_engine_rejects_stale_legal_source_version() -> None:
    # Given: a request pinned to a stale legal-source resource version.
    payload = _adapter_payload(
        ("bank_account_attachment",),
        ("enforceable_title", "financial_account_hint"),
    )

    # When / Then: the engine fails fast before evaluating advisory decisions.
    with pytest.raises(DomainDecisionError) as error:
        _ = evaluate_claim_domain_decision(
            DomainDecisionRequest(
                payload,
                workflow_state="execution_route_selection",
                expected_domain_source_version="stale-domain-sources@v0",
            ),
        )

    assert error.value.reason_code == "stale_legal_source_version"
    assert error.value.location == "resources/legal_rules/debt_collection_domain_sources_v1.json"


def test_engine_rejects_stale_finance_model_version(tmp_path: Path) -> None:
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
