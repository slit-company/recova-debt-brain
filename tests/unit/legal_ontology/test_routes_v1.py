from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import TypeAlias


REPO_ROOT = Path(__file__).resolve().parents[3]
ROUTES_PATH = REPO_ROOT / "resources" / "legal_routes" / "debt_collection_routes_v1.json"
SOURCES_PATH = REPO_ROOT / "resources" / "legal_rules" / "debt_collection_domain_sources_v1.json"
VALIDATOR_PATH = REPO_ROOT / "scripts" / "legal_ontology" / "validate_routes.py"
JsonScalar: TypeAlias = None | bool | int | float | str
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]

REQUIRED_ROUTE_FAMILIES = {
    "voluntary_repayment",
    "notarial_deed",
    "title_acquisition",
    "provisional_remedy",
    "financial_asset_execution",
    "income_execution",
    "housing_lease_execution",
    "business_receivable_execution",
    "real_estate_execution",
    "movable_business_asset_execution",
    "insurance_refund_deposit_execution",
    "tax_refund_distribution_compensation",
    "inheritance_family_property",
    "fraudulent_transfer_hidden_asset",
    "special_property_right",
    "welfare_public_benefit_exclusion",
    "asset_disclosure_inquiry_registry",
    "insolvency_recovery_review",
    "monitoring_retry",
}


def load_json_object(path: Path) -> JsonObject:
    raw: JsonValue = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    return raw


def route_entries(routes: JsonObject) -> list[JsonObject]:
    entries = routes["routes"]
    assert isinstance(entries, list)
    typed_entries: list[JsonObject] = []
    for entry in entries:
        assert isinstance(entry, dict)
        typed_entries.append(entry)
    return typed_entries


def run_validator(routes_path: Path = ROUTES_PATH) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), str(routes_path), str(SOURCES_PATH)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_validator_accepts_expanded_routes_v1_catalog() -> None:
    # Given: the expanded v1 route catalog and curated v1 domain legal sources.
    routes = load_json_object(ROUTES_PATH)
    routes_list = route_entries(routes)

    # When: the CLI validator checks the catalog.
    result = run_validator()

    # Then: it accepts an expanded, advisory-only catalog with all required route families.
    assert result.returncode == 0
    assert "PASS routes" in result.stdout
    assert "routes=32" in result.stdout
    assert len(routes_list) == 32
    assert len(routes_list) > 18
    assert {str(route["family"]) for route in routes_list} >= REQUIRED_ROUTE_FAMILIES
    assert all(route["direct_execution_allowed"] is False for route in routes_list)


def test_validator_rejects_unknown_legal_source_ref(tmp_path: Path) -> None:
    # Given: a generated route copy whose first route points to an unknown domain source id.
    routes = load_json_object(ROUTES_PATH)
    routes_list = route_entries(routes)
    routes_list[0]["legal_source_refs"] = ["missing-domain-source"]
    invalid_routes_path = tmp_path / "invalid-source-routes.json"
    _ = invalid_routes_path.write_text(json.dumps(routes, ensure_ascii=False), encoding="utf-8")

    # When: the CLI validator checks the generated route resource.
    result = run_validator(invalid_routes_path)

    # Then: it fails with the missing source id named in diagnostics.
    assert result.returncode != 0
    assert "missing-domain-source" in result.stderr
    assert "unknown legal source" in result.stderr.lower()


def test_validator_rejects_invalid_fact_handle(tmp_path: Path) -> None:
    # Given: a generated route copy whose first route uses a handle outside the catalog.
    routes = load_json_object(ROUTES_PATH)
    routes_list = route_entries(routes)
    routes_list[0]["required_fact_handles"] = ["unknown_fact_handle"]
    invalid_routes_path = tmp_path / "invalid-handle-routes.json"
    _ = invalid_routes_path.write_text(json.dumps(routes, ensure_ascii=False), encoding="utf-8")

    # When: the CLI validator checks the generated route resource.
    result = run_validator(invalid_routes_path)

    # Then: it fails before downstream decision logic can consume the bad handle.
    assert result.returncode != 0
    assert "unknown fact handle unknown_fact_handle" in result.stderr


def test_validator_rejects_direct_execution_enabled(tmp_path: Path) -> None:
    # Given: a generated route copy that tries to authorize direct execution.
    routes = load_json_object(ROUTES_PATH)
    routes_list = route_entries(routes)
    routes_list[0]["direct_execution_allowed"] = True
    invalid_routes_path = tmp_path / "direct-execution-routes.json"
    _ = invalid_routes_path.write_text(json.dumps(routes, ensure_ascii=False), encoding="utf-8")

    # When: the CLI validator checks the generated route resource.
    result = run_validator(invalid_routes_path)

    # Then: it rejects the execution boundary violation.
    assert result.returncode != 0
    assert "direct_execution_allowed must be false" in result.stderr


def test_validator_rejects_duplicate_route_id(tmp_path: Path) -> None:
    # Given: a generated route copy whose first two entries share an id.
    routes = load_json_object(ROUTES_PATH)
    routes_list = route_entries(routes)
    routes_list[1]["route_id"] = routes_list[0]["route_id"]
    invalid_routes_path = tmp_path / "duplicate-route-routes.json"
    _ = invalid_routes_path.write_text(json.dumps(routes, ensure_ascii=False), encoding="utf-8")

    # When: the CLI validator checks the generated route resource.
    result = run_validator(invalid_routes_path)

    # Then: it fails with a duplicate-id diagnostic.
    assert result.returncode != 0
    assert "duplicate id" in result.stderr
