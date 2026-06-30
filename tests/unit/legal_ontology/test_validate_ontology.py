from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
ONTOLOGY_PATH = REPO_ROOT / "resources" / "ontologies" / "recova-debt-collection.json"
VALIDATOR_PATH = REPO_ROOT / "scripts" / "legal_ontology" / "validate_ontology.py"


def test_validator_accepts_recova_debt_collection_ontology() -> None:
    # Given: the v0 ontology resource committed in TrustGraph config shape.
    command = [sys.executable, str(VALIDATOR_PATH), str(ONTOLOGY_PATH)]

    # When: the CLI validator checks the ontology.
    result = subprocess.run(command, cwd=REPO_ROOT, check=False, capture_output=True, text=True)

    # Then: it reports success with structural counts.
    assert result.returncode == 0
    assert "PASS ontology" in result.stdout
    assert "classes=" in result.stdout
    assert "objectProperties=" in result.stdout
    assert "datatypeProperties=" in result.stdout


def test_validator_rejects_unknown_object_property_range(tmp_path: Path) -> None:
    # Given: a generated copy whose object property points at a missing class.
    raw = json.loads(ONTOLOGY_PATH.read_text(encoding="utf-8"))
    ontology = raw["recova-debt-collection"]
    first_property = next(iter(ontology["objectProperties"].values()))
    first_property["rdfs:range"] = "missing-class"
    invalid_path = tmp_path / "invalid-ontology.json"
    invalid_path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")

    # When: the CLI validator checks the invalid copy.
    result = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), str(invalid_path)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    # Then: it fails with the missing range named in diagnostics.
    assert result.returncode != 0
    assert "missing-class" in result.stderr
    assert "unknown range" in result.stderr.lower()
