from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import TypeAlias

from scripts.legal_ontology.domain_sources_v1_common import load_json


REPO_ROOT = Path(__file__).resolve().parents[3]
PACKETS_PATH = REPO_ROOT / "resources" / "action_packets" / "debt_collection_action_packets_v1.json"
DECISIONS_PATH = REPO_ROOT / "resources" / "decision_tables" / "debt_collection_route_decisions_v1.json"
ROUTES_PATH = REPO_ROOT / "resources" / "legal_routes" / "debt_collection_routes_v1.json"
SOURCES_PATH = REPO_ROOT / "resources" / "legal_rules" / "debt_collection_domain_sources_v1.json"
WORKFLOW_PATH = REPO_ROOT / "resources" / "workflows" / "debt_collection_workflow_v1.json"
FINANCE_PATH = REPO_ROOT / "resources" / "finance" / "claim_finance_model_v1.json"
VALIDATOR_PATH = REPO_ROOT / "scripts" / "legal_ontology" / "validate_action_packets_v1.py"
REQUIRED_PACKET_TYPES = {
    "evidence_request",
    "legal_action_review",
    "finance_review",
    "contact_review",
    "monitoring_retry",
    "insolvency_recovery_review",
}
FORBIDDEN_FIELDS = {
    "filing_destination",
    "filing_destination_court",
    "debtor_contact_payload",
    "debtor_contact_channel",
    "executable_instruction",
}
JsonScalar: TypeAlias = None | bool | int | float | str
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]


def load_json_object(path: Path) -> JsonObject:
    return load_json(path)


def object_list(entry: JsonObject, field: str) -> list[JsonObject]:
    value = entry[field]
    assert isinstance(value, list)
    objects: list[JsonObject] = []
    for item in value:
        assert isinstance(item, dict)
        objects.append(item)
    return objects


def string_list_field(entry: JsonObject, field: str) -> list[str]:
    value = entry[field]
    assert isinstance(value, list)
    strings: list[str] = []
    for item in value:
        assert isinstance(item, str)
        strings.append(item)
    return strings


def run_validator(packets_path: Path = PACKETS_PATH) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(VALIDATOR_PATH),
            str(packets_path),
            str(DECISIONS_PATH),
            str(ROUTES_PATH),
            str(SOURCES_PATH),
            str(WORKFLOW_PATH),
            str(FINANCE_PATH),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_validator_accepts_action_packet_schemas_v1() -> None:
    # Given: the Todo 8 action packet schema resource and v1 dependency catalogs.
    result = run_validator()

    # When: the validator checks non-execution and cross-resource references.
    assert result.returncode == 0

    # Then: every advisory packet family is registered and source-traceable.
    assert "PASS action_packets recova-debt-collection-action-packets@v1.0.0" in result.stdout
    assert "packet_types=6" in result.stdout
    assert "required_inputs=" in result.stdout
    assert "source_refs=" in result.stdout


def test_packet_resource_stays_advisory_and_covers_route_decisions() -> None:
    # Given: the committed action-packet resource and route decision table.
    packets = load_json_object(PACKETS_PATH)
    decisions = load_json_object(DECISIONS_PATH)

    # When: packet types and route-decision next steps are compared.
    schemas = object_list(packets, "packet_schemas")
    packet_types = {str(schema["packet_type"]) for schema in schemas}
    decision_packet_types = {
        str(entry["next_step_action_packet_type"])
        for entry in object_list(decisions, "route_decisions")
    }

    # Then: the resource is complete, advisory-only, and forbids execution-bearing fields.
    assert packet_types == REQUIRED_PACKET_TYPES
    assert decision_packet_types <= packet_types
    assert packets["no_direct_execution"] is True
    assert packets["direct_execution_allowed"] is False
    assert packets["execution_semantics"] == "schema_only_advisory_packet_preparation"
    for schema in schemas:
        assert schema["non_execution_semantics"] == "advisory_only_human_review_required"
        assert schema["review_status"] == "human_review_required"
        assert "pii_profile" in schema
        assert set(string_list_field(schema, "forbidden_fields")) >= FORBIDDEN_FIELDS
        assert string_list_field(schema, "required_inputs")
        assert string_list_field(schema, "source_refs")


def test_validator_rejects_direct_execution_semantics(tmp_path: Path) -> None:
    # Given: a generated packet copy that allows direct execution.
    packets = load_json_object(PACKETS_PATH)
    packets["direct_execution_allowed"] = True
    schemas = object_list(packets, "packet_schemas")
    schemas[0]["non_execution_semantics"] = "direct_execution_allowed"
    invalid_path = tmp_path / "direct-execution-action-packets.json"
    _ = invalid_path.write_text(json.dumps(packets, ensure_ascii=False), encoding="utf-8")

    # When: the validator checks the generated copy.
    result = run_validator(invalid_path)

    # Then: it rejects executable action packet semantics.
    assert result.returncode != 0
    assert "direct_execution_allowed must be false" in result.stderr
    assert "non_execution_semantics must be advisory_only_human_review_required" in result.stderr


def test_validator_rejects_debtor_contact_payload_and_filing_destination(tmp_path: Path) -> None:
    # Given: a generated packet copy with execution-bearing forbidden fields.
    packets = load_json_object(PACKETS_PATH)
    schemas = object_list(packets, "packet_schemas")
    schemas[0]["allowed_output_fields"] = ["packet_id", "filing_destination", "debtor_contact_payload"]
    invalid_path = tmp_path / "execution-fields-action-packets.json"
    _ = invalid_path.write_text(json.dumps(packets, ensure_ascii=False), encoding="utf-8")

    # When: the validator checks the generated copy.
    result = run_validator(invalid_path)

    # Then: it rejects actual filing destinations and debtor-contact payload fields.
    assert result.returncode != 0
    assert "forbidden output field filing_destination" in result.stderr
    assert "forbidden output field debtor_contact_payload" in result.stderr
