from __future__ import annotations

import importlib
from collections.abc import Sequence
from pathlib import Path

from trustgraph_legal.debtor_context_builder import (
    DebtorContextInputError,
    build_debtor_context,
)
from trustgraph_legal.debtor_context_types import DebtorGraphPayload, JsonObject
from trustgraph_legal.document_assembly import (
    DocumentAssemblyPayload,
    build_document_assembly_payload,
)
from trustgraph_legal.document_assembly_pages import materialize_pages

__all__ = [
    "DebtorContextInputError",
    "build_debtor_context",
    "build_debtor_context_from_path",
    "main",
]


def build_debtor_context_from_path(
    pages_dir: Path,
    repo_root: Path | None = None,
) -> DebtorGraphPayload:
    root = repo_root if repo_root is not None else Path.cwd()
    payload: DocumentAssemblyPayload | JsonObject = build_document_assembly_payload(
        materialize_pages(pages_dir, root)
    )
    return build_debtor_context(payload, root)


def main(argv: Sequence[str] | None = None) -> int:
    cli = importlib.import_module("trustgraph_legal.debtor_context_cli")
    return cli.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
