from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_TEXT = (
    "recova-mcp-lab.slit.company",
    "mini",
    "Cloudflare Tunnel",
    "Supabase",
    "MCP_LAB_BEARER_TOKEN",
    "rollback",
    "task-11-mcp-smoke.json",
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Check Recova MCP lab runbook.")
    parser.add_argument("--runbook", required=True)
    parser.add_argument("--evidence-root", required=True)
    parser.add_argument("--require", action="append", default=[])
    parser.add_argument("--simulate-missing", default="")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    runbook = Path(args.runbook)
    evidence_root = Path(args.evidence_root)
    missing: list[str] = []

    if not runbook.is_file():
        missing.append(str(runbook))
        text = ""
    else:
        text = runbook.read_text(encoding="utf-8")

    missing.extend(_missing_runbook_text(text))
    missing.extend(_missing_evidence(evidence_root, args.require, args.simulate_missing))

    result: dict[str, Any] = {
        "status": "failed" if missing else "passed",
        "runbook": str(runbook),
        "evidence_root": str(evidence_root),
        "missing": missing,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    if missing:
        print("FAIL runbook_check missing={}".format(",".join(missing)))
        raise SystemExit(1)
    print("PASS runbook_check")


def _missing_runbook_text(text: str) -> list[str]:
    return ["runbook:{}".format(value) for value in REQUIRED_TEXT if value not in text]


def _missing_evidence(
    evidence_root: Path,
    required: list[str],
    simulate_missing: str,
) -> list[str]:
    missing = []
    for name in required:
        if name == simulate_missing or not (evidence_root / name).is_file():
            missing.append(name)
    return missing


if __name__ == "__main__":
    main()
