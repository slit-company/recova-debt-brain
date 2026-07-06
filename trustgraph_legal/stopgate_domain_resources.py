from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Final, Tuple

from trustgraph_legal.stop_gates import _object_list, _str_or
from trustgraph_legal.stopgate_rules import StopGateInputError, load_rule_source
from trustgraph_legal.stopgate_types import FactRef, JsonValue, RuleSourceSet

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
DOMAIN_STOPGATE_RULES_PATH: Final = (
    REPO_ROOT / "resources" / "legal_rules" / "debt_collection_stopgate_domain_v1.json"
)
DOMAIN_SOURCES_PATH: Final = REPO_ROOT / "resources" / "legal_rules" / "debt_collection_domain_sources_v1.json"
DOMAIN_ROUTES_PATH: Final = REPO_ROOT / "resources" / "legal_routes" / "debt_collection_routes_v1.json"
APPROVED_STATUS: Final = "approved_static_v1"
ROUTE_CANDIDATE_CLASS: Final = "route-candidate"
LEGAL_SOURCE_CLASS: Final = "legal-source"


@dataclass(frozen=True)
class LegalSourceStatusFact:
    source_id: str
    review_status: str
    ref: FactRef


@dataclass(frozen=True)
class RouteCandidateFact:
    route_id: str
    review_status: str
    legal_source_refs: Tuple[str, ...]
    direct_execution_allowed: bool
    ref: FactRef


@dataclass(frozen=True)
class RouteCatalogEntry:
    route_id: str
    review_status: str
    legal_source_refs: Tuple[str, ...]
    direct_execution_allowed: bool


@dataclass(frozen=True)
class DomainContext:
    source_status_by_id: Dict[str, str]
    route_by_id: Dict[str, RouteCatalogEntry]


def load_domain_v1_rule_source(rules_path: Path = DOMAIN_STOPGATE_RULES_PATH) -> RuleSourceSet:
    return load_rule_source(rules_path)


def load_domain_context(
    sources_path: Path = DOMAIN_SOURCES_PATH,
    routes_path: Path = DOMAIN_ROUTES_PATH,
) -> DomainContext:
    return DomainContext(load_domain_source_statuses(sources_path), load_route_catalog(routes_path))


def load_domain_source_statuses(sources_path: Path = DOMAIN_SOURCES_PATH) -> Dict[str, str]:
    raw = json.loads(sources_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise StopGateInputError(sources_path, "domain source root must be an object")
    statuses: Dict[str, str] = {}
    for item in _object_list(raw.get("sources")):
        source_id = _str_or(item.get("source_id"), "")
        review_status = _str_or(item.get("review_status"), "")
        if source_id:
            statuses[source_id] = review_status
    return statuses


def load_route_catalog(routes_path: Path = DOMAIN_ROUTES_PATH) -> Dict[str, RouteCatalogEntry]:
    raw = json.loads(routes_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise StopGateInputError(routes_path, "route catalog root must be an object")
    routes: Dict[str, RouteCatalogEntry] = {}
    for item in _object_list(raw.get("routes")):
        route_id = _str_or(item.get("route_id"), "")
        if route_id:
            routes[route_id] = RouteCatalogEntry(
                route_id,
                _str_or(item.get("review_status"), ""),
                string_tuple(item.get("legal_source_refs")),
                item.get("direct_execution_allowed") is True,
            )
    return routes


def string_tuple(value: JsonValue) -> Tuple[str, ...]:
    return tuple(item for item in value if isinstance(item, str)) if isinstance(value, list) else ()


def text_value(value: JsonValue, default: str) -> str:
    return value if isinstance(value, str) else default
