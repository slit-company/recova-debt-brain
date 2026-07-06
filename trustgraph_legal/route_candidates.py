from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Final

from pydantic import JsonValue as PydanticJsonValue, TypeAdapter

from trustgraph_legal.debtor_context_types import DebtorGraphPayload, FactAssertion, JsonObject, JsonValue, RouteCandidate
from trustgraph_legal.stop_gates import evaluate_case_graph

ROUTES_PATH: Final = Path(__file__).resolve().parents[1] / "resources" / "legal_routes" / "debt_collection_routes_v0.json"
LEGAL_SOURCES_PATH: Final = Path(__file__).resolve().parents[1] / "resources" / "legal_rules" / "debt_collection_route_sources_v0.json"
CLEAR_FACT_REVIEW_STATUSES: Final = frozenset({"approved", "assembled", "confirmed", "extracted", "verified"})
REVIEW_BLOCKER_MARKERS: Final = ("review", "uncertain", "unclear", "unknown", "missing")
LEGAL_REVIEW_MARKERS: Final = ("draft", "deprecated", "future", "review")
APPROVED_LEGAL_STATUSES: Final = frozenset({"approved", "approved-static-v0", "retrieved"})
EVALUATION_DATE: Final = date(2026, 7, 6)
GLOBAL_STOP_GATE_REASON_CODES: Final = frozenset({"invalid_fact_without_provenance", "rule_source_unapproved"})
REVIEW_REQUIRED_STATUS: Final = "review_required"
JSON_VALUE_ADAPTER: Final = TypeAdapter[PydanticJsonValue](PydanticJsonValue)


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
    review_status: str
    required_fact_handles: tuple[str, ...]
    blocking_fact_handles: tuple[str, ...]
    legal_source_refs: tuple[str, ...]
    no_direct_execution: bool
    direct_execution_allowed: bool


@dataclass(frozen=True, slots=True)
class FactHit:
    fact_ids: tuple[str, ...]
    confidence: float
    review_required: bool


@dataclass(frozen=True, slots=True)
class RouteEvaluationContext:
    facts: Mapping[str, FactHit]
    review_handles: frozenset[str]
    stop_gate_reason_codes: tuple[str, ...]
    legal_sources: Mapping[str, JsonObject]


def load_route_templates(routes_path: Path = ROUTES_PATH) -> tuple[RouteTemplate, ...]:
    raw = JSON_VALUE_ADAPTER.validate_json(routes_path.read_bytes())
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


def load_legal_source_catalog(sources_path: Path = LEGAL_SOURCES_PATH) -> Mapping[str, JsonObject]:
    raw = JSON_VALUE_ADAPTER.validate_json(sources_path.read_bytes())
    if not isinstance(raw, dict):
        raise RouteResourceError(str(sources_path), "legal source root must be an object")
    sources = raw.get("sources")
    if not isinstance(sources, list):
        raise RouteResourceError(str(sources_path), "sources must be a list")
    entries = tuple(_legal_source(source, index) for index, source in enumerate(sources))
    return {_text(source, "source_id", str(sources_path)): source for source in entries}


def evaluate_route_candidates(
    graph: DebtorGraphPayload, templates: Sequence[RouteTemplate] | None = None, *, legal_sources_path: Path = LEGAL_SOURCES_PATH
) -> tuple[RouteCandidate, ...]:
    active_templates = load_route_templates() if templates is None else tuple(templates)
    context = RouteEvaluationContext(
        facts=_fact_hits(graph.fact_assertions),
        review_handles=_review_handles(graph),
        stop_gate_reason_codes=_stop_gate_reason_codes(graph),
        legal_sources=load_legal_source_catalog(legal_sources_path),
    )
    return tuple(_candidate(template, context) for template in active_templates)


def _template(route: JsonObject, index: int) -> RouteTemplate:
    location = "routes[{}]".format(index)
    route_id = _text(route, "route_id", location)
    return RouteTemplate(
        route_id=route_id,
        route_label=_label(route_id),
        family=_text(route, "family", location),
        review_status=_text(route, "review_status", location),
        required_fact_handles=_strings(route, "required_fact_handles", location),
        blocking_fact_handles=_strings(route, "blocking_fact_handles", location),
        legal_source_refs=_strings(route, "legal_source_refs", location),
        no_direct_execution=_bool(route, "no_direct_execution", location),
        direct_execution_allowed=_bool(route, "direct_execution_allowed", location),
    )


def _candidate(template: RouteTemplate, context: RouteEvaluationContext) -> RouteCandidate:
    missing = tuple(handle for handle in template.required_fact_handles if handle not in context.facts)
    template_blockers = tuple(
        handle
        for handle in template.blocking_fact_handles
        if handle in context.facts or handle in context.review_handles
    )
    stop_gate_blockers = _affected_stop_gate_reasons(template, context.stop_gate_reason_codes, template_blockers)
    blockers = template_blockers + stop_gate_blockers
    required_hits = tuple(context.facts[handle] for handle in template.required_fact_handles if handle in context.facts)
    blocker_hits = tuple(context.facts[handle] for handle in template_blockers if handle in context.facts)
    hits = required_hits + blocker_hits
    status = "possible"
    if template_blockers:
        status = "blocked"
        if template.family == "stopgate" or any(_review_blocker(handle) for handle in template_blockers):
            status = REVIEW_REQUIRED_STATUS
        if any(hit.review_required for hit in hits):
            status = REVIEW_REQUIRED_STATUS
    elif stop_gate_blockers:
        status = REVIEW_REQUIRED_STATUS
    elif missing:
        status = "missing_facts"
    elif any(hit.review_required for hit in hits):
        status = REVIEW_REQUIRED_STATUS
    elif _legal_review_required(template.legal_source_refs, template.review_status, context.legal_sources):
        status = REVIEW_REQUIRED_STATUS

    return RouteCandidate(
        route_id=template.route_id,
        route_label=template.route_label,
        status=status,
        required_facts=template.required_fact_handles,
        missing_facts=missing,
        blocking_facts=blockers,
        legal_source_refs=_legal_source_refs(template.legal_source_refs, context.legal_sources),
        source_fact_ids=_source_fact_ids(template.required_fact_handles + template_blockers, context.facts),
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


def _stop_gate_reason_codes(graph: DebtorGraphPayload) -> tuple[str, ...]:
    reasons = set(_reason_codes(graph.stop_gates))
    if _has_case_graph_packets(graph.case_packets):
        payload = evaluate_case_graph(graph.to_json()).to_json()
        reasons.update(_reason_codes(_object_tuple(payload.get("stop_gates"))))
    return tuple(sorted(reasons))


def _has_case_graph_packets(case_packets: Iterable[JsonObject]) -> bool:
    return any(isinstance(packet.get("entities"), list) for packet in case_packets)


def _reason_codes(items: Iterable[JsonObject]) -> tuple[str, ...]:
    reasons: list[str] = []
    for item in items:
        reason = _optional_text(item.get("reason_code")) or _optional_text(item.get("review_reason"))
        if reason is not None:
            reasons.append(reason)
    return tuple(reasons)


def _legal_source(source: JsonValue, index: int) -> JsonObject:
    location = "sources[{}]".format(index)
    if not isinstance(source, dict):
        raise RouteResourceError(location, "legal source must be an object")
    return source


def _legal_source_refs(source_ids: tuple[str, ...], catalog: Mapping[str, JsonObject]) -> tuple[str, ...]:
    return tuple(_legal_source_ref(source_id, catalog.get(source_id)) for source_id in source_ids)


def _legal_source_ref(source_id: str, source: JsonObject | None) -> str:
    if source is None:
        return "{}|lawId=missing|MST=missing|article=missing|effective_date=missing|retrieval_status=missing|review_status=missing".format(source_id)
    return "{}|lawId={}|MST={}|article={}|effective_date={}|retrieval_status={}|review_status={}".format(
        source_id,
        _text(source, "law_id", source_id),
        _text(source, "mst", source_id),
        _text(source, "article", source_id),
        _text(source, "effective_date", source_id),
        _text(source, "retrieval_status", source_id),
        _text(source, "review_status", source_id),
    )


def _legal_review_required(source_ids: tuple[str, ...], route_review_status: str, catalog: Mapping[str, JsonObject]) -> bool:
    if _status_requires_review(route_review_status):
        return True
    return any(_source_requires_review(catalog.get(source_id), source_id) for source_id in source_ids)


def _source_requires_review(source: JsonObject | None, source_id: str) -> bool:
    if source is None:
        return True
    return (
        _status_requires_review(_text(source, "review_status", source_id))
        or _status_requires_review(_text(source, "retrieval_status", source_id))
        or _future_effective_date(_text(source, "effective_date", source_id))
    )


def _status_requires_review(status: str) -> bool:
    normalized = status.replace("_", "-").lower()
    return normalized not in APPROVED_LEGAL_STATUSES and any(marker in normalized for marker in LEGAL_REVIEW_MARKERS)


def _future_effective_date(value: str) -> bool:
    try:
        return date.fromisoformat(value) > EVALUATION_DATE
    except ValueError:
        return True


def _affected_stop_gate_reasons(template: RouteTemplate, reason_codes: tuple[str, ...], template_blockers: tuple[str, ...]) -> tuple[str, ...]:
    if template.family == "title":
        return tuple(reason for reason in reason_codes if reason in GLOBAL_STOP_GATE_REASON_CODES)
    return tuple(reason for reason in reason_codes if reason not in template_blockers)


def _confidence(required_hits: tuple[FactHit, ...], missing: tuple[str, ...], blocker_hits: tuple[FactHit, ...]) -> float:
    if blocker_hits:
        return round(max(hit.confidence for hit in blocker_hits), 2)
    if missing:
        total = len(required_hits) + len(missing)
        present_ratio = len(required_hits) / total if total else 0.0
        return round(0.35 + (0.45 * present_ratio), 2)
    return round(min((hit.confidence for hit in required_hits), default=0.75), 2)


def _source_fact_ids(handles: tuple[str, ...], facts: Mapping[str, FactHit]) -> tuple[str, ...]:
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


def _object_tuple(value: JsonValue) -> tuple[JsonObject, ...]:
    return tuple(item for item in value if isinstance(item, dict)) if isinstance(value, list) else ()


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
