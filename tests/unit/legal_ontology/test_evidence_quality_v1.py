from __future__ import annotations

import json

from trustgraph_legal.evidence_quality import evaluate_evidence_quality

JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject = dict[str, JsonValue]


def test_source_backed_direct_proof_passes_without_review_items() -> None:
    # Given: a claim-domain payload with one direct source-backed fact handle.
    payload = _payload(
        _fact(
            "fact:title",
            "enforceable_title",
            True,
            source_refs=("fixture:judgment#L10",),
            confidence=0.94,
        ),
    )

    # When: evidence quality is checked for workflow inputs.
    checkpoint = evaluate_evidence_quality(payload).to_json()

    # Then: the checkpoint clears without raw text or review noise.
    assert checkpoint["schema_version"] == "trustgraph-evidence-quality-check/v1"
    assert checkpoint["decision"] == "pass"
    assert checkpoint["review_items"] == []
    assert checkpoint["hold_items"] == []
    assert checkpoint["summary"] == {
        "facts_checked": 1,
        "review_items": 0,
        "hold_items": 0,
        "lowest_confidence": 0.94,
    }
    encoded = json.dumps(checkpoint, ensure_ascii=False)
    assert "RAW OCR" not in encoded
    assert "object_value" not in encoded
    assert '"source_text":' not in encoded


def test_placeholder_source_ref_creates_review_item() -> None:
    # Given: a fact handle whose source ref is still a placeholder.
    payload = _payload(
        _fact(
            "fact:placeholder",
            "financial_account_hint",
            True,
            source_refs=("todo:bank-source",),
            confidence=0.88,
        ),
    )

    # When: evidence quality is checked.
    checkpoint = evaluate_evidence_quality(payload).to_json()

    # Then: workflow consumers get a review-required signal, not an exception.
    assert checkpoint["decision"] == "review_required"
    assert {str(item["code"]) for item in _object_list(checkpoint["review_items"])} == {
        "placeholder_source_ref",
    }
    review_item = _only_object(checkpoint["review_items"])
    assert review_item["category"] == "evidence"
    assert review_item["fact_ids"] == ["fact:placeholder"]
    assert review_item["fact_handles"] == ["financial_account_hint"]


def test_stale_low_confidence_and_derived_facts_create_review_items() -> None:
    # Given: stale, low-confidence, and derived facts that should not be route-clearing proof.
    payload = _payload(
        _fact(
            "fact:stale",
            "current_balance",
            100000,
            confidence=0.91,
            freshness_status="stale",
        ),
        _fact("fact:low", "payment_default", True, confidence=0.58),
        _fact("fact:derived", "enforceable_title", True, confidence=0.86, derived=True),
    )

    # When: evidence quality is checked.
    checkpoint = evaluate_evidence_quality(payload).to_json()

    # Then: all workflow-risky evidence states are explicit review items.
    assert checkpoint["decision"] == "review_required"
    codes = {str(item["code"]) for item in _object_list(checkpoint["review_items"])}
    assert codes >= {"stale_fact", "low_confidence_fact", "derived_fact_review"}
    assert checkpoint["summary"] == {
        "facts_checked": 3,
        "review_items": 3,
        "hold_items": 0,
        "lowest_confidence": 0.58,
    }


def test_conflicting_payment_or_title_fact_values_create_hold() -> None:
    # Given: two source-backed facts assert different values for the same workflow-critical handle.
    payload = _payload(
        _fact("fact:title-yes", "enforceable_title", True, source_refs=("fixture:title-a#L1",)),
        _fact("fact:title-no", "enforceable_title", False, source_refs=("fixture:title-b#L4",)),
    )

    # When: evidence quality is checked.
    checkpoint = evaluate_evidence_quality(payload).to_json()

    # Then: the contradiction becomes a hold signal without echoing raw values.
    assert checkpoint["decision"] == "hold"
    hold_item = _only_object(checkpoint["hold_items"])
    assert hold_item["code"] == "conflicting_fact_values"
    assert hold_item["category"] == "evidence_conflict"
    assert hold_item["fact_ids"] == ["fact:title-yes", "fact:title-no"]
    assert hold_item["fact_handles"] == ["enforceable_title"]
    assert hold_item["review_status"] == "human_review_required"
    assert hold_item["source_refs"] == ["fixture:title-a#L1", "fixture:title-b#L4"]
    assert "value_fingerprints" in hold_item
    assert "object_value" not in json.dumps(hold_item, ensure_ascii=False)


def _payload(*facts: JsonObject) -> JsonObject:
    return {
        "schema_version": "trustgraph-claim-domain-adapter/v1",
        "claim_root": {"claim_ref": "claim:evidence-quality"},
        "fact_handles": list(facts),
        "pii_profile": {"raw_text_included": False, "source_text_included": False},
    }


def _fact(
    fact_id: str,
    fact_handle: str,
    object_value: JsonValue,
    *,
    source_refs: tuple[str, ...] = ("fixture:source#L1",),
    confidence: float = 0.91,
    freshness_status: str = "current",
    derived: bool = False,
) -> JsonObject:
    return {
        "fact_id": fact_id,
        "claim_id": "claim:evidence-quality",
        "fact_handle": fact_handle,
        "object_value": object_value,
        "source_refs": list(source_refs),
        "source_document_id": "document:evidence-quality",
        "source_hash": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "chunk_id": "chunk:evidence-quality:1",
        "line_start": 1,
        "line_end": 2,
        "confidence": confidence,
        "review_status": "source_backed",
        "freshness_status": freshness_status,
        "derived": derived,
    }


def _object_list(value: JsonValue) -> list[JsonObject]:
    assert isinstance(value, list)
    objects: list[JsonObject] = []
    for item in value:
        assert isinstance(item, dict)
        objects.append(item)
    return objects


def _only_object(value: JsonValue) -> JsonObject:
    objects = _object_list(value)
    assert len(objects) == 1
    return objects[0]
