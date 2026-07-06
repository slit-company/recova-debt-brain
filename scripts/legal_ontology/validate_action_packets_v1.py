#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "scripts.legal_ontology"

from .action_packet_validation_v1 import DependencyRoots, validate_action_packets
from .domain_sources_v1_common import load_json


def main(argv: Sequence[str]) -> int:
    if len(argv) != 7:
        usage = (
            "usage: validate_action_packets_v1.py <action-packets.json> <decisions.json> <routes.json> "
            + "<sources.json> <workflow.json> <finance.json>"
        )
        print(
            usage,
            file=sys.stderr,
        )
        return 2
    try:
        summary, issues = validate_action_packets(
            load_json(Path(argv[1])),
            DependencyRoots(
                decisions_root=load_json(Path(argv[2])),
                routes_root=load_json(Path(argv[3])),
                sources_root=load_json(Path(argv[4])),
                workflow_root=load_json(Path(argv[5])),
                finance_root=load_json(Path(argv[6])),
            ),
        )
    except json.JSONDecodeError as error:
        print(f"ERROR invalid JSON: {error}", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 1
    except TypeError as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 1
    if issues:
        for validation_issue in issues:
            print(f"ERROR {validation_issue.format()}", file=sys.stderr)
        return 1
    message = " ".join(
        [
            f"PASS action_packets {summary.action_packet_version}",
            f"packet_types={summary.packet_type_count}",
            f"required_inputs={summary.required_input_count}",
            f"source_refs={summary.source_ref_count}",
        ]
    )
    print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
