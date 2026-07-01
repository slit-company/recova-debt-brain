from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_compose_does_not_expose_origin_or_runtime_dns_token() -> None:
    compose = (REPO_ROOT / "deploy/recova-mcp-lab/docker-compose.yml").read_text(
        encoding="utf-8"
    )

    assert "CLOUDFLARE_API_TOKEN" not in compose
    assert '"8000:8000"' not in compose
    assert "127.0.0.1:8000:8000" in compose


def test_runtime_env_contract_excludes_operator_only_cloudflare_token() -> None:
    env_example = (REPO_ROOT / "deploy/recova-mcp-lab/.env.example").read_text(
        encoding="utf-8"
    )
    env_check = (REPO_ROOT / "scripts/recova_mcp/check_lab_env.sh").read_text(
        encoding="utf-8"
    )

    assert "CLOUDFLARE_API_TOKEN" not in env_example
    assert "CLOUDFLARE_API_TOKEN" not in env_check
