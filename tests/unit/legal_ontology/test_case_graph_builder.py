from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Final, List, Union

from trustgraph_legal.case_graph import build_case_graph


REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = REPO_ROOT / "tests" / "fixtures" / "legal-ocr" / "manifest.json"
ONTOLOGY_PATH = REPO_ROOT / "resources" / "ontologies" / "recova-debt-collection.json"
JsonScalar = Union[str, int, float, bool, type(None)]
JsonValue = Union[JsonScalar, List["JsonValue"], Dict[str, "JsonValue"]]
REQUIRED_KEYS: Final = {
    "case_packet_id",
    "court_case_number",
    "claim_id",
    "enforcement_title_id",
    "party_identity_key",
    "document_hash",
}


def test_fixture_manifest_builds_case_packet_graph_with_required_keys() -> None:
    # Given: the synthetic Todo 5 legal OCR manifest.
    graph = build_case_graph(MANIFEST_PATH, REPO_ROOT).to_json()

    # When: graph facts are resolved into the v0 ontology shape.
    packet = graph["case_packets"][0]
    key_names = {key["key"] for key in packet["evidence_keys"]}
    ontology_classes = {
        entity["ontology_class"]
        for entity in packet["entities"]
        if entity.get("ontology_class") is not None
    }
    edge_predicates = {edge["predicate"] for edge in packet["edges"]}
    entity_by_id = {entity["id"]: entity for entity in packet["entities"]}
    party_target_classes = {
        entity_by_id[edge["target"]]["ontology_class"]
        for edge in packet["edges"]
        if edge["predicate"] == "has-party"
    }

    # Then: CasePacket is the primary anchor and explicit Todo 6 evidence keys exist.
    assert graph["schema_version"] == "trustgraph-legal-case-graph/v1"
    assert packet["entity_type"] == "CasePacket"
    assert packet["ontology_class"] == "case-packet"
    assert packet["case_projection"]["derived"] is True
    assert packet["case_projection"]["ontology_class"] is None
    assert "case" not in ontology_classes
    assert REQUIRED_KEYS <= key_names
    assert _evidence_key(packet, "claim_id")["confidence"] >= 0.85
    assert "derivation_reason" in _evidence_key(packet, "claim_id")
    assert _evidence_key(packet, "enforcement_title_id")["confidence"] >= 0.85
    assert "derivation_reason" in _evidence_key(packet, "enforcement_title_id")

    # Then: representative legal graph entities and ontology edges are present.
    assert ontology_classes >= {
        "legal-document",
        "source-span",
        "document-provenance",
        "organization-party",
        "person-party",
        "party-role",
        "claim",
        "amount",
        "enforcement-title",
        "court-procedure",
        "attachment-target",
        "asset",
        "operational-ledger",
        "ledger-entry",
        "recovery-transaction",
        "cost-entry",
        "legal-check",
    }
    assert edge_predicates >= {
        "has-document",
        "has-party",
        "has-claim",
        "has-enforcement-title",
        "has-court-procedure",
        "has-attachment-target",
        "has-asset-evidence",
        "has-ledger",
        "has-legal-check",
    }
    assert party_target_classes <= {"person-party", "organization-party"}
    assert {"person-party", "organization-party", "party-role"} <= ontology_classes
    assert _non_derived_facts_have_provenance(packet["entities"])
    assert _non_derived_facts_have_provenance(packet["edges"])


def test_emitted_ontology_ids_are_configured_v0_classes_and_properties() -> None:
    # Given: the configured v0 ontology and the resolved fixture graph.
    ontology = json.loads(ONTOLOGY_PATH.read_text(encoding="utf-8"))[
        "recova-debt-collection"
    ]
    configured_classes = set(ontology["classes"])
    configured_properties = set(ontology["objectProperties"])
    graph = build_case_graph(MANIFEST_PATH, REPO_ROOT).to_json()

    # When: emitted class and predicate IDs are collected recursively.
    packet = graph["case_packets"][0]
    emitted_classes = {
        item["ontology_class"]
        for item in [packet] + packet["entities"]
        if item.get("ontology_class") is not None
    }
    emitted_predicates = {edge["predicate"] for edge in packet["edges"]}

    # Then: no unconfigured ontology IDs such as Case, Creditor, or LedgerEvent leak out.
    assert emitted_classes <= configured_classes
    assert emitted_predicates <= configured_properties
    assert {"Case", "Creditor", "Debtor", "ThirdPartyDebtor", "LedgerEvent"}.isdisjoint(
        emitted_classes
    )


def test_module_entrypoint_writes_case_graph_json(tmp_path: Path) -> None:
    # Given: the public Todo 6 module invocation contract.
    output_path = tmp_path / "task-6-case-graph.json"

    # When: python runs the case graph module entrypoint.
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "trustgraph_legal.case_graph",
            "--fixtures",
            str(MANIFEST_PATH),
            "--out",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    # Then: the CLI writes JSON with the expected CasePacket graph summary.
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert result.returncode == 0
    assert str(output_path) in result.stdout
    assert payload["summary"]["case_packets"] == 1
    assert payload["case_packets"][0]["ontology_class"] == "case-packet"


def test_similar_debtors_without_identity_evidence_remain_unresolved(tmp_path: Path) -> None:
    # Given: two payment-order documents with similar debtor placeholders and no identity key.
    first = _write_fixture(
        tmp_path,
        "payment_a.md",
        "Respondent: [DEBTOR_PERSON]\nCase number: 2026차전0001",
    )
    second = _write_fixture(
        tmp_path,
        "payment_b.md",
        "Respondent: [DEBTOR_PERSON_VARIANT]\nCase number: 2026차전0002",
    )
    manifest_path = _write_manifest(tmp_path, [first, second])

    # When: the graph resolver considers name-like role evidence without identity evidence.
    packet = build_case_graph(manifest_path, tmp_path).to_json()["case_packets"][0]
    debtor_roles = [
        entity
        for entity in packet["entities"]
        if entity.get("role") == "debtor"
    ]

    # Then: debtors remain separate and the rejection is explicit.
    assert len(debtor_roles) == 2
    assert {role["value"] for role in debtor_roles} == {
        "[DEBTOR_PERSON]",
        "[DEBTOR_PERSON_VARIANT]",
    }
    assert {
        decision["reason"]
        for decision in packet["identity_resolution"]["merge_decisions"]
    } >= {"identity_uncertain", "name_only_without_identity_evidence"}
    assert any(
        finding["reason"] == "identity_uncertain"
        for finding in packet["findings"]
    )


def _evidence_key(packet: Dict[str, JsonValue], key_name: str) -> Dict[str, JsonValue]:
    for key in packet["evidence_keys"]:
        if key["key"] == key_name:
            return key
    raise AssertionError("missing evidence key: {}".format(key_name))


def _non_derived_facts_have_provenance(facts: List[Dict[str, JsonValue]]) -> bool:
    return all(
        bool(fact.get("provenance"))
        for fact in facts
        if fact.get("derived") is not True
    )


def _write_fixture(tmp_path: Path, name: str, variable_lines: str) -> Dict[str, str]:
    text = "\n".join(
        [
            "# Synthetic Fixture: Payment Order Variant",
            "Document marker: 지급명령 / 판결 정본",
            "Court: [COURT_REDACTED]",
            variable_lines,
            "Claimant: [CREDITOR_ORG]",
            "Principal: KRW 1,000",
            "Delayed damages: 12 percent per year from [DATE_REDACTED]",
        ]
    )
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {
        "document_id": "test-{}".format(name[:-3]),
        "document_type": "judgment_payment_order",
        "source_fixture_path": name,
        "source_hash": "sha256:{}".format(digest),
    }


def _write_manifest(tmp_path: Path, documents: List[Dict[str, str]]) -> Path:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "legal-ocr-fixture-manifest/v1",
                "ontology_version": "recova-debt-collection@v0",
                "prompt_version": "legal-ontology-extraction@v0",
                "documents": documents,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return manifest_path
