from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional, Sequence

from trustgraph_legal.stop_gates import check_case_graph


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python3 -m trustgraph_legal.check")
    parser.add_argument("--case", required=True)
    parser.add_argument("--out")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    payload = check_case_graph(Path(args.case)).to_json()
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.out is not None:
        output_path = Path(args.out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
