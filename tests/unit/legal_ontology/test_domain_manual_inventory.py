from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Final, TypeAlias

from pydantic import JsonValue as PydanticJsonValue
from pydantic import TypeAdapter

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "scripts" / "legal_ontology" / "domain_manual_inventory.py"
FORBIDDEN_KEYS: Final = {"body", "body_text", "raw_text", "source_text", "excerpt", "source_path"}
JsonValue: TypeAlias = PydanticJsonValue
JsonObject: TypeAlias = dict[str, JsonValue]
JSON_OBJECT_ADAPTER: Final = TypeAdapter[JsonObject](JsonObject)


def test_inventory_writes_summary_candidates_without_manual_text_or_paths(tmp_path: Path) -> None:
    # Given: a minimized manual with route headings, legal refs, finance terms, and PII-like prose.
    manual_path = tmp_path / "manual.md"
    output_path = tmp_path / "inventory.json"
    phone_token = "010-" + "1234-" + "5678"
    resident_token = "900101-" + "1234567"
    account_token = "123456" + "789012"
    _ = manual_path.write_text(
        "\n".join(
            [
                "# 장기채권 추심 실무 루트 총정리 v2",
                "## 2. 사건을 처음 받았을 때의 실무 체크리스트",
                "### 2.1 사건 기본정보",
                f"{phone_token} {resident_token} 계좌 {account_token}는 절대 출력되면 안 된다.",
                "## 3. 장기채권에서 시효를 보는 방법",
                "### 3.2 시효위험 플래그",
                "## 5. 임의회수·채무승인·공정증서 루트",
                "### 5.2 일부변제",
                "민법 제168조와 원금, 이자, 비용, 변제충당을 검토한다.",
                "## 8. 은행·금융자산 집행 루트",
                "### 8.1 예금채권 압류",
                "민사집행법 제246조 및 압류금지채권을 확인한다.",
                "## 21. 회생·파산·면책 필터",
                "### 21.1 면책 확인",
                "## 23. Recova 제품화 관점: 자동 추천 엔진",
                "### 23.3 우선순위 스코어링",
            ],
        ),
        encoding="utf-8",
    )

    # When: the CLI inventory extractor is driven against the manual.
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--manual",
            str(manual_path),
            "--out",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    # Then: the output is a candidate inventory with no prose, PII, or local path leakage.
    assert result.returncode == 0
    payload = load_json_object(output_path)
    payload_dump = json.dumps(payload, ensure_ascii=False)
    counts = object_field(payload, "counts")
    pii_profile = object_field(payload, "pii_profile")

    assert str_field(payload, "schema_version") == "domain-manual-inventory/v2"
    assert str_field(payload, "summary_kind") == "manual_candidate_inventory"
    assert bool_field(pii_profile, "raw_text_included") is False
    assert bool_field(pii_profile, "source_paths_included") is False
    assert int_field(counts, "route_candidates") >= 2
    assert int_field(counts, "workflow_candidates") >= 2
    assert int_field(counts, "legal_source_candidates") >= 2
    assert int_field(counts, "finance_candidates") >= 4
    assert int_field(counts, "action_packet_candidates") >= 2
    assert str(manual_path) not in payload_dump
    assert phone_token not in payload_dump
    assert resident_token not in payload_dump
    assert account_token not in payload_dump
    assert "절대 출력되면 안 된다" not in payload_dump
    assert _contains_forbidden_key(payload) is False


def test_inventory_rejects_missing_manual_without_partial_output(tmp_path: Path) -> None:
    # Given: a missing manual path and an output destination.
    output_path = tmp_path / "missing-inventory.json"

    # When: the CLI inventory extractor is pointed at the missing manual.
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--manual",
            str(tmp_path / "missing-manual.md"),
            "--out",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    # Then: it reports a controlled error and writes no partial JSON.
    assert result.returncode == 1
    assert "manual path does not exist" in result.stderr
    assert not output_path.exists()


def load_json_object(path: Path) -> JsonObject:
    return JSON_OBJECT_ADAPTER.validate_json(path.read_bytes())


def object_field(value: JsonObject, key: str) -> JsonObject:
    field = value[key]
    assert isinstance(field, dict)
    return field


def str_field(value: JsonObject, key: str) -> str:
    field = value[key]
    assert isinstance(field, str)
    return field


def int_field(value: JsonObject, key: str) -> int:
    field = value[key]
    assert isinstance(field, int)
    assert not isinstance(field, bool)
    return field


def bool_field(value: JsonObject, key: str) -> bool:
    field = value[key]
    assert isinstance(field, bool)
    return field


def _contains_forbidden_key(value: JsonValue) -> bool:
    if isinstance(value, dict):
        return any(key in FORBIDDEN_KEYS or _contains_forbidden_key(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_key(item) for item in value)
    return False
