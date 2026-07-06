from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Iterable, Sequence

from trustgraph_legal.debtor_context_types import DebtorGraphPayload, FactAssertion, JsonObject, JsonValue, RouteCandidate

ROUTES_PATH: Final = Path(__file__).resolve().parents[1] / "resources" / "legal_routes" / "debt_collection_routes_v0.json"
CLEAR_FACT_REVIEW_STATUSES: Final = frozenset({"approved", "assembled", "confirmed", "extracted", "verified"})
REVIEW_BLOCKER_MARKERS: Final = ("review", "uncertain", "unclear", "unknown", "missing")
POSSIBLE_STATUS: Final = "possible"
BLOCKED_STATUS: Final = "blocked"
MISSING_FACTS_STATUS: Final = "missing_facts"
REVIEW_REQUIRED_STATUS: Final = "review_required"


@dataclass(frozen=True, slots=True)
class RouteResourceError(Exception):
    location: str
    detail: str

    def __str__(self) -> str:
        return "{}: {}".format(self.location, self.detail)


@dataclass(frozen=True, slots=True)
class RouteTemplate:
    route_id: str
    route_label: str
    family: str
    resource_status: str
    review_status: str
    required_fact_handles: tuple[str, ...]
    missing_fact_handles: tuple[str, ...]
    blocking_fact_handles: tuple[str, ...]
    legal_source_refs: tuple[str, ...]
    no_direct_execution: bool
    direct_execution_allowed: bool
    execution_semantics: str


@dataclass(frozen=True, slots=True)
class FactHit:
    fact_ids: tuple[str, ...]
    confidence: float
    review_required: bool


def load_route_templates(routes_path: Path = ROUTES_PATH) -> tuple[RouteTemplate, ...]:
    raw = json.loads(routes_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise RouteResourceError(str(routes_path), "resource root must be an object")

    routes = raw.get("routes")
    if not isinstance(routes, list):
        raise RouteResourceError(str(routes_path), "routes must be a list")

    templates: list[RouteTemplate] = []
    for index, route in enumerate(routes):
        if not isinstance(route, dict):
            raise RouteResourceError("routes[{}]".format(index), "route must be an object")
        templates.append(_template(route, index))
    return tuple(templates)


def evaluate_route_candidates(
    graph: DebtorGraphPayload,
    templates: Sequence[RouteTemplate] | None = None,
) -> tuple[RouteCandidate, ...]:
    active_templates = load_route_templates() if templates is None else tuple(templates)
    facts = _fact_hits(graph.fact_assertions)
    review_handles = _review_handles(graph)
    return tuple(_candidate(template, facts, review_handles) for template in active_templates)


def _template(route: JsonObject, index: int) -> RouteTemplate:
    location = "routes[{}]".format(index)
    route_id = _text(route, "route_id", location)
    return RouteTemplate(
        route_id=route_id,
        route_label=_label(route_id),
        family=_text(route, "family", location),
        resource_status=_text(route, "status", location),
        review_status=_text(route, "review_status", location),
        required_fact_handles=_strings(route, "required_fact_handles", location),
        missing_fact_handles=_strings(route, "missing_fact_handles", location),
        blocking_fact_handles=_strings(route, "blocking_fact_handles", location),
        legal_source_refs=_strings(route, "legal_source_refs", location),
        no_direct_execution=_bool(route, "no_direct_execution", location),
        direct_execution_allowed=_bool(route, "direct_execution_allowed", location),
        execution_semantics=_text(route, "execution_semantics", location),
    )


def _candidate(
    template: RouteTemplate,
    facts: dict[str, FactHit],
    review_handles: frozenset[str],
) -> RouteCandidate:
    missing = tuple(handle for handle in template.required_fact_handles if handle not in facts)
    blockers = tuple(
        handle
        for handle in template.blocking_fact_handles
        if handle in facts or handle in review_handles
    )
    required_hits = tuple(facts[handle] for handle in template.required_fact_handles if handle in facts)
    blocker_hits = tuple(facts[handle] for handle in blockers if handle in facts)
    hits = required_hits + blocker_hits
    status = POSSIBLE_STATUS
    if blockers:
        status = BLOCKED_STATUS
        if template.family == "stopgate" or any(_review_blocker(handle) for handle in blockers):
            status = REVIEW_REQUIRED_STATUS
        if any(hit.review_required for hit in hits):
            status = REVIEW_REQUIRED_STATUS
    elif missing:
        status = MISSING_FACTS_STATUS
    elif any(hit.review_required for hit in hits):
        status = REVIEW_REQUIRED_STATUS

    return RouteCandidate(
        route_id=template.route_id,
        route_label=template.route_label,
        status=status,
        required_facts=template.required_fact_handles,
        missing_facts=missing,
        blocking_facts=blockers,
        legal_source_refs=template.legal_source_refs,
        source_fact_ids=_source_fact_ids(template.required_fact_handles + blockers, facts),
        confidence=_confidence(required_hits, missing, blocker_hits),
        review_status=REVIEW_REQUIRED_STATUS,
        no_direct_execution=True,
    )


def _fact_hits(fact_assertions: Iterable[FactAssertion]) -> dict[str, FactHit]:
    facts_by_handle: dict[str, list[FactAssertion]] = {}
    for fact in fact_assertions:
        facts_by_handle.setdefault(fact.predicate, []).append(fact)
    return {handle: _fact_hit(facts) for handle, facts in facts_by_handle.items()}


def _fact_hit(facts: Sequence[FactAssertion]) -> FactHit:
    return FactHit(
        fact_ids=tuple(sorted({fact.fact_id for fact in facts})),
        confidence=round(max((fact.confidence for fact in facts), default=0.0), 2),
        review_required=not any(fact.review_status in CLEAR_FACT_REVIEW_STATUSES for fact in facts),
    )


def _review_handles(graph: DebtorGraphPayload) -> frozenset[str]:
    handles = set(_reason_codes(graph.stop_gates))
    handles.update(_reason_codes(graph.review_items))
    return frozenset(handles)


def _reason_codes(items: Iterable[JsonObject]) -> tuple[str, ...]:
    reasons: list[str] = []
    for item in items:
        reason = _optional_text(item.get("reason_code")) or _optional_text(item.get("review_reason"))
        if reason is not None:
            reasons.append(reason)
    return tuple(reasons)


def _confidence(
    required_hits: tuple[FactHit, ...],
    missing: tuple[str, ...],
    blocker_hits: tuple[FactHit, ...],
) -> float:
    if blocker_hits:
        return round(max(hit.confidence for hit in blocker_hits), 2)
    if missing:
        total = len(required_hits) + len(missing)
        present_ratio = len(required_hits) / total if total else 0.0
        return round(0.35 + (0.45 * present_ratio), 2)
    return round(min((hit.confidence for hit in required_hits), default=0.75), 2)


def _source_fact_ids(handles: tuple[str, ...], facts: dict[str, FactHit]) -> tuple[str, ...]:
    ids = {fact_id for handle in handles if handle in facts for fact_id in facts[handle].fact_ids}
    return tuple(sorted(ids))


def _review_blocker(handle: str) -> bool:
    return any(marker in handle for marker in REVIEW_BLOCKER_MARKERS)


def _label(route_id: str) -> str:
    text = route_id.replace("_", " ")
    return text[:1].upper() + text[1:]


def _text(entry: JsonObject, field: str, location: str) -> str:
    value = entry.get(field)
    if isinstance(value, str) and value:
        return value
    raise RouteResourceError(location, "{} must be a non-empty string".format(field))


def _optional_text(value: JsonValue) -> str | None:
    return value if isinstance(value, str) and value else None


def _bool(entry: JsonObject, field: str, location: str) -> bool:
    value = entry.get(field)
    if isinstance(value, bool):
        return value
    raise RouteResourceError(location, "{} must be boolean".format(field))


def _strings(entry: JsonObject, field: str, location: str) -> tuple[str, ...]:
    value = entry.get(field)
    if not isinstance(value, list):
        raise RouteResourceError(location, "{} must be a list".format(field))
    strings = tuple(item for item in value if isinstance(item, str) and item)
    if len(strings) != len(value) or not strings:
        raise RouteResourceError(location, "{} must be a non-empty string list".format(field))
    return strings
