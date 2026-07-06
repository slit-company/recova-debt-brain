from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
ONTOLOGY_PATH = REPO_ROOT / "resources" / "ontologies" / "recova-debt-collection-v1.json"
VALIDATOR_PATH = REPO_ROOT / "scripts" / "legal_ontology" / "validate_domain_ontology_v1.py"


def test_validator_accepts_claim_centered_domain_ontology_v1() -> None:
    # Given: the v1 claim-centered debt collection ontology resource.
    command = [sys.executable, str(VALIDATOR_PATH), str(ONTOLOGY_PATH)]

    # When: the CLI validator checks the ontology.
    result = subprocess.run(command, cwd=REPO_ROOT, check=False, capture_output=True, text=True)

    # Then: it reports the root boundary, required edges, and structural counts.
    assert result.returncode == 0
    assert "PASS ontology recova-debt-collection-v1" in result.stdout
    assert "root=Claim/Receivable" in result.stdout
    assert "requiredEdges=" in result.stdout
    assert "classes=" in result.stdout
    assert "objectProperties=" in result.stdout
    assert "datatypeProperties=" in result.stdout


def test_validator_rejects_missing_claim_root(tmp_path: Path) -> None:
    # Given: a generated copy with the required Claim root removed.
    raw = json.loads(ONTOLOGY_PATH.read_text(encoding="utf-8"))
    ontology = raw["recova-debt-collection-v1"]
    ontology["classes"].pop("claim")
    invalid_path = tmp_path / "missing-claim-root.json"
    invalid_path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")

    # When: the CLI validator checks the invalid copy.
    result = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), str(invalid_path)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    # Then: it fails with the missing Claim root named in diagnostics.
    assert result.returncode != 0
    assert "Claim" in result.stderr
    assert "required root" in result.stderr


def test_validator_rejects_missing_required_claim_edge(tmp_path: Path) -> None:
    # Given: a generated copy with a required Claim edge removed.
    raw = json.loads(ONTOLOGY_PATH.read_text(encoding="utf-8"))
    ontology = raw["recova-debt-collection-v1"]
    ontology["objectProperties"].pop("claim-has-workflow-state")
    invalid_path = tmp_path / "missing-required-edge.json"
    invalid_path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")

    # When: the CLI validator checks the invalid copy.
    result = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), str(invalid_path)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    # Then: it fails with the required edge named in diagnostics.
    assert result.returncode != 0
    assert "claim-has-workflow-state" in result.stderr
    assert "required edge" in result.stderr
