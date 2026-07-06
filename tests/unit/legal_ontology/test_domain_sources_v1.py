from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import TypeAlias


REPO_ROOT = Path(__file__).resolve().parents[3]
DOMAIN_SOURCES_PATH = REPO_ROOT / "resources" / "legal_rules" / "debt_collection_domain_sources_v1.json"
ROUTES_PATH = REPO_ROOT / "resources" / "legal_routes" / "debt_collection_routes_v0.json"
STOPGATES_PATH = REPO_ROOT / "resources" / "legal_rules" / "debt_collection_stopgate_v0.json"
VALIDATOR_PATH = REPO_ROOT / "scripts" / "legal_ontology" / "validate_domain_sources_v1.py"
JsonScalar: TypeAlias = None | bool | int | float | str
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]


def load_json_object(path: Path) -> JsonObject:
    raw: JsonValue = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    return raw


def run_validator(
    sources_path: Path = DOMAIN_SOURCES_PATH,
    routes_path: Path = ROUTES_PATH,
    stopgates_path: Path = STOPGATES_PATH,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), str(sources_path), str(routes_path), str(stopgates_path)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_validator_accepts_domain_source_resource() -> None:
    # Given: the curated v1 domain sources and v0 route/StopGate resources.
    # When: the CLI validator checks all source references.
    result = run_validator()

    # Then: it reports the expected domain source, route, StopGate, and workflow counts.
    assert result.returncode == 0
    assert "PASS domain_sources" in result.stdout
    assert "legal_sources=21" in result.stdout
    assert "routes=18" in result.stdout
    assert "stopgates=12" in result.stdout
    assert "workflow_refs=12" in result.stdout
    assert "workflow_source_refs=29" in result.stdout


def test_validator_rejects_unknown_route_source_ref(tmp_path: Path) -> None:
    # Given: a generated route copy whose first route points to an unknown source id.
    routes = load_json_object(ROUTES_PATH)
    route_entries = routes["routes"]
    assert isinstance(route_entries, list)
    first_route = route_entries[0]
    assert isinstance(first_route, dict)
    first_route["legal_source_refs"] = ["missing-domain-source"]
    invalid_routes_path = tmp_path / "invalid-routes.json"
    _ = invalid_routes_path.write_text(json.dumps(routes, ensure_ascii=False), encoding="utf-8")

    # When: the CLI validator checks the generated route resource.
    result = run_validator(routes_path=invalid_routes_path)

    # Then: it fails with the missing source id named in diagnostics.
    assert result.returncode != 0
    assert "missing-domain-source" in result.stderr
    assert "unknown source_id" in result.stderr


def test_validator_rejects_missing_source_metadata(tmp_path: Path) -> None:
    # Given: a generated source copy missing required temporal metadata.
    sources = load_json_object(DOMAIN_SOURCES_PATH)
    source_entries = sources["sources"]
    assert isinstance(source_entries, list)
    first_source = source_entries[0]
    assert isinstance(first_source, dict)
    del first_source["evaluation_date"]
    invalid_sources_path = tmp_path / "invalid-domain-sources.json"
    _ = invalid_sources_path.write_text(json.dumps(sources, ensure_ascii=False), encoding="utf-8")

    # When: the CLI validator checks the generated source resource.
    result = run_validator(sources_path=invalid_sources_path)

    # Then: it fails before the source can be treated as curated.
    assert result.returncode != 0
    assert "missing evaluation_date" in result.stderr
