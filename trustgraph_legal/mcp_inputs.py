from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, Final, List, Optional

from trustgraph_legal.governance_models import JsonValue

JsonObject = Dict[str, JsonValue]

DEFAULT_COLLECTION: Final = "recova-debt-collection"
DEFAULT_MANIFEST: Final = Path("tests/fixtures/legal-ocr/manifest.json")
DEFAULT_ONTOLOGY: Final = Path("resources/ontologies/recova-debt-collection.json")


def manifest_path(args: JsonObject, root: Path) -> Path:
    return path_arg(args, "manifest_path", root) or root / DEFAULT_MANIFEST


def ontology_path(args: JsonObject, root: Path) -> Path:
    return path_arg(args, "ontology_path", root) or root / DEFAULT_ONTOLOGY


def packet_entities(graph: JsonObject) -> List[JsonObject]:
    return [
        entity
        for packet in object_list(graph.get("case_packets"))
        for entity in object_list(packet.get("entities"))
    ]


def object_list(value: JsonValue) -> List[JsonObject]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def path_arg(args: JsonObject, key: str, root: Path) -> Optional[Path]:
    value = args.get(key)
    if not isinstance(value, str) or not value:
        return None
    path = Path(value)
    candidate = path if path.is_absolute() else root / path
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        raise PermissionError("path_outside_repo_root")
    return resolved


def repo_root(repo_root_value: Optional[Path]) -> Path:
    return (Path.cwd() if repo_root_value is None else repo_root_value).resolve()


def str_arg(args: JsonObject, key: str, default: str) -> str:
    value = args.get(key)
    return value if isinstance(value, str) else default


def int_arg(args: JsonObject, key: str) -> Optional[int]:
    value = args.get(key)
    return value if isinstance(value, int) else None


def document_id(args: JsonObject, text: str) -> str:
    fallback = "mcp-doc-{}".format(hash_text(text).removeprefix("sha256:")[:16])
    return str_arg(args, "document_id", fallback)


def hash_text(text: str) -> str:
    return "sha256:{}".format(hashlib.sha256(text.encode("utf-8")).hexdigest())
