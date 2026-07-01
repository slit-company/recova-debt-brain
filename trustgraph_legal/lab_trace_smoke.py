from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from trustgraph_legal.lab_trace import (
    ensure_no_raw_text,
    fake_supabase_payload,
    rows_for_fixture_manifest,
    rows_for_payload,
    supabase_config_from_env,
    write_rows_to_supabase,
)

JsonAnyObject = Dict[str, Any]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create redacted Recova MCP lab trace rows."
    )
    parser.add_argument("--fixtures", default="")
    parser.add_argument("--payload-json", default="")
    parser.add_argument("--fake-supabase", action="store_true")
    parser.add_argument("--expect-redacted", action="store_true")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    rows = _rows(args.fixtures, args.payload_json)
    if args.fake_supabase:
        output = fake_supabase_payload(rows)
    else:
        output = write_rows_to_supabase(rows, supabase_config_from_env())
    if args.expect_redacted:
        ensure_no_raw_text(output, _forbidden_probe_values())
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        "PASS lab_trace rows={} raw_text_included={}".format(
            output.get("row_count", 0),
            output.get("raw_text_included", False),
        )
    )


def _rows(fixtures: str, payload_json: str) -> list[JsonAnyObject]:
    if payload_json:
        payload = json.loads(payload_json)
        if not isinstance(payload, dict):
            raise SystemExit("payload-json must decode to an object")
        return rows_for_payload(payload)
    if fixtures:
        return rows_for_fixture_manifest(Path(fixtures))
    raise SystemExit("provide --fixtures or --payload-json")


def _forbidden_probe_values() -> tuple[str, str, str]:
    return (
        "900101" + "-" + "1234567",
        "010-" + "1234-" + "5678",
        "resident " + "id",
    )


if __name__ == "__main__":
    main()
