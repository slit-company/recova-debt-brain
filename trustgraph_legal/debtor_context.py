from __future__ import annotations

from pathlib import Path

from trustgraph_legal.debtor_context_builder import (
    DebtorContextInputError,
    build_debtor_context,
)
from trustgraph_legal.debtor_context_types import DebtorGraphPayload, JsonObject
from trustgraph_legal.document_assembly import DocumentAssemblyPayload, build_document_assembly

__all__ = [
    "DebtorContextInputError",
    "build_debtor_context",
    "build_debtor_context_from_path",
]


def build_debtor_context_from_path(
    pages_dir: Path,
    repo_root: Path | None = None,
) -> DebtorGraphPayload:
    root = repo_root if repo_root is not None else Path.cwd()
    payload: DocumentAssemblyPayload | JsonObject = build_document_assembly(pages_dir, root)
    return build_debtor_context(payload, root)
