from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
ROUTES_PATH = REPO_ROOT / "resources" / "legal_routes" / "debt_collection_routes_v0.json"
SOURCES_PATH = REPO_ROOT / "resources" / "legal_rules" / "debt_collection_route_sources_v0.json"
VALIDATOR_PATH = REPO_ROOT / "scripts" / "legal_ontology" / "validate_routes.py"


def test_validator_accepts_debt_collection_route_resources() -> None:
    # Given: the curated v0 route and legal source resources.
    command = [sys.executable, str(VALIDATOR_PATH), str(ROUTES_PATH), str(SOURCES_PATH)]

    # When: the CLI validator checks cross-resource source references.
    result = subprocess.run(command, cwd=REPO_ROOT, check=False, capture_output=True, text=True)

    # Then: it reports the route and legal source counts.
    assert result.returncode == 0
    assert "PASS routes" in result.stdout
    assert "routes=18" in result.stdout
    assert "legal_sources=18" in result.stdout


def test_validator_rejects_unknown_legal_source_ref(tmp_path: Path) -> None:
    # Given: a generated copy whose first route references a nonexistent legal source.
    routes = json.loads(ROUTES_PATH.read_text(encoding="utf-8"))
    routes["routes"][0]["legal_source_refs"] = ["missing-source-id"]
    invalid_routes_path = tmp_path / "invalid-routes.json"
    invalid_routes_path.write_text(json.dumps(routes, ensure_ascii=False), encoding="utf-8")

    # When: the CLI validator checks the invalid route resource.
    result = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), str(invalid_routes_path), str(SOURCES_PATH)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    # Then: it fails with the missing source id named in diagnostics.
    assert result.returncode != 0
    assert "missing-source-id" in result.stderr
    assert "unknown legal source" in result.stderr.lower()


def test_validator_rejects_missing_legal_source_refs(tmp_path: Path) -> None:
    # Given: a generated copy whose first route has no legal source refs field.
    routes = json.loads(ROUTES_PATH.read_text(encoding="utf-8"))
    del routes["routes"][0]["legal_source_refs"]
    invalid_routes_path = tmp_path / "missing-refs-routes.json"
    invalid_routes_path.write_text(json.dumps(routes, ensure_ascii=False), encoding="utf-8")

    # When: the CLI validator checks the invalid route resource.
    result = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), str(invalid_routes_path), str(SOURCES_PATH)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    # Then: it fails because every route must carry at least one legal source ref.
    assert result.returncode != 0
    assert "legal_source_refs" in result.stderr
    assert "non-empty string list" in result.stderr
