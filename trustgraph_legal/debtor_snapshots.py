from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Dict, Final, List, Optional, Tuple, Union

from trustgraph_legal.debtor_context_types import (
    DebtorGraphPayload,
    JsonObject,
    JsonValue,
    PLACEHOLDER_SOURCE_REFS,
)

GraphInput = Union[DebtorGraphPayload, JsonObject]
FingerprintMap = Dict[str, str]
RAW_TEXT_KEYS: Final = frozenset({"excerpt", "ocr_text", "raw_text", "source_text", "text"})
FACT_FIELDS: Final = ("fact_id", "subject_id", "predicate", "object_value", "confidence", "source_ref", "source_refs", "source_document_id", "source_hash", "chunk_id", "line_start", "line_end", "extractor_version", "ontology_version", "valid_time", "observed_time", "review_status", "derived")
ROUTE_FIELDS: Final = ("route_id", "route_label", "status", "required_facts", "missing_facts", "blocking_facts", "legal_source_refs", "source_fact_ids", "confidence", "review_status", "no_direct_execution")
VERSION_FIELDS: Final = ("extractor_versions", "ontology_version", "route_version", "legal_rule_source_version")
SHA256_RE: Final = re.compile(r"^sha256:[0-9a-f]{64}$")


@dataclass(frozen=True)
class SnapshotReplay:
    replay_snapshot_id: str
    graph_snapshot_id: str
    source_bundle_hash: str
    semantic_hash: str
    fact_assertion_ids: Tuple[str, ...]
    route_candidate_ids: Tuple[str, ...]
    versions: JsonObject

    def to_json(self) -> JsonObject:
        return {"replay_snapshot_id": self.replay_snapshot_id, "graph_snapshot_id": self.graph_snapshot_id, "source_bundle_hash": self.source_bundle_hash, "semantic_hash": self.semantic_hash, "fact_assertion_ids": list(self.fact_assertion_ids), "route_candidate_ids": list(self.route_candidate_ids), "versions": self.versions}


@dataclass(frozen=True)
class SnapshotVersionChange:
    field_name: str
    previous_value: JsonValue
    current_value: JsonValue

    def to_json(self) -> JsonObject:
        return {"field_name": self.field_name, "previous_value": self.previous_value, "current_value": self.current_value}


@dataclass(frozen=True)
class SnapshotDiff:
    previous_replay_snapshot_id: str
    current_replay_snapshot_id: str
    source_bundle_changed: bool
    previous_source_bundle_hash: str
    current_source_bundle_hash: str
    added_fact_ids: Tuple[str, ...]
    removed_fact_ids: Tuple[str, ...]
    changed_fact_ids: Tuple[str, ...]
    added_route_candidate_ids: Tuple[str, ...]
    removed_route_candidate_ids: Tuple[str, ...]
    changed_route_candidate_ids: Tuple[str, ...]
    version_changes: Tuple[SnapshotVersionChange, ...]
    legacy_graph_snapshot_id_collision: bool

    def to_json(self) -> JsonObject:
        return {"previous_replay_snapshot_id": self.previous_replay_snapshot_id, "current_replay_snapshot_id": self.current_replay_snapshot_id, "source_bundle_changed": self.source_bundle_changed, "previous_source_bundle_hash": self.previous_source_bundle_hash, "current_source_bundle_hash": self.current_source_bundle_hash, "added_fact_ids": list(self.added_fact_ids), "removed_fact_ids": list(self.removed_fact_ids), "changed_fact_ids": list(self.changed_fact_ids), "added_route_candidate_ids": list(self.added_route_candidate_ids), "removed_route_candidate_ids": list(self.removed_route_candidate_ids), "changed_route_candidate_ids": list(self.changed_route_candidate_ids), "version_changes": [change.to_json() for change in self.version_changes], "legacy_graph_snapshot_id_collision": self.legacy_graph_snapshot_id_collision}


@dataclass(frozen=True)
class ProvenanceIssue:
    fact_id: str
    reason_code: str
    field_name: str
    source_ref: Optional[str] = None

    def to_json(self) -> JsonObject:
        return {"fact_id": self.fact_id, "reason_code": self.reason_code, "field_name": self.field_name, "source_ref": self.source_ref}


@dataclass(frozen=True)
class ProvenanceValidationReport:
    valid: bool
    issues: Tuple[ProvenanceIssue, ...]

    def to_json(self) -> JsonObject:
        return {"valid": self.valid, "issues": [issue.to_json() for issue in self.issues], "summary": {"issues": len(self.issues)}}


def replay_snapshot(graph: GraphInput) -> SnapshotReplay:
    graph_json = _graph_json(graph)
    graph_snapshot = _json_object(graph_json.get("graph_snapshot"))
    fact_fingerprints = _fingerprints(graph_json.get("fact_assertions"), "fact_id", FACT_FIELDS)
    route_fingerprints = _fingerprints(graph_json.get("route_candidates"), "route_id", ROUTE_FIELDS)
    versions = _versions(graph_snapshot)
    source_bundle_hash = _text_or(graph_snapshot.get("source_bundle_hash"), "")
    semantic_payload: JsonObject = {"source_bundle_hash": source_bundle_hash, "fact_fingerprints": _fingerprint_json(fact_fingerprints), "route_fingerprints": _fingerprint_json(route_fingerprints), "versions": versions}
    semantic_hash = _hash_json(semantic_payload)
    return SnapshotReplay(replay_snapshot_id="snapshot-replay:{}".format(semantic_hash[:16]), graph_snapshot_id=_text_or(graph_snapshot.get("graph_snapshot_id"), ""), source_bundle_hash=source_bundle_hash, semantic_hash="sha256:{}".format(semantic_hash), fact_assertion_ids=tuple(sorted(fact_fingerprints)), route_candidate_ids=tuple(sorted(route_fingerprints)), versions=versions)


def diff_snapshots(previous: GraphInput, current: GraphInput) -> SnapshotDiff:
    previous_json = _graph_json(previous)
    current_json = _graph_json(current)
    previous_replay = replay_snapshot(previous_json)
    current_replay = replay_snapshot(current_json)
    previous_facts = _fingerprints(previous_json.get("fact_assertions"), "fact_id", FACT_FIELDS)
    current_facts = _fingerprints(current_json.get("fact_assertions"), "fact_id", FACT_FIELDS)
    previous_routes = _fingerprints(previous_json.get("route_candidates"), "route_id", ROUTE_FIELDS)
    current_routes = _fingerprints(current_json.get("route_candidates"), "route_id", ROUTE_FIELDS)
    version_changes = _version_changes(previous_replay.versions, current_replay.versions)
    collision = previous_replay.graph_snapshot_id == current_replay.graph_snapshot_id and previous_replay.replay_snapshot_id != current_replay.replay_snapshot_id
    return SnapshotDiff(previous_replay.replay_snapshot_id, current_replay.replay_snapshot_id, previous_replay.source_bundle_hash != current_replay.source_bundle_hash, previous_replay.source_bundle_hash, current_replay.source_bundle_hash, _added(previous_facts, current_facts), _removed(previous_facts, current_facts), _changed(previous_facts, current_facts), _added(previous_routes, current_routes), _removed(previous_routes, current_routes), _changed(previous_routes, current_routes), version_changes, collision)


def validate_snapshot_provenance(graph: GraphInput) -> ProvenanceValidationReport:
    graph_json = _graph_json(graph)
    issues: List[ProvenanceIssue] = []
    for fact in _json_objects(graph_json.get("fact_assertions")):
        issues.extend(_provenance_issues(fact))
    return ProvenanceValidationReport(valid=not issues, issues=tuple(issues))


def _provenance_issues(fact: JsonObject) -> Tuple[ProvenanceIssue, ...]:
    fact_id = _text_or(fact.get("fact_id"), "fact:<unknown>")
    source_refs = _source_refs(fact)
    issues: List[ProvenanceIssue] = []
    if fact.get("derived") is True and not source_refs:
        return _derived_issues(fact_id, fact)
    if not source_refs:
        issues.append(ProvenanceIssue(fact_id, "missing_source_ref", "source_ref"))
    for source_ref in source_refs:
        if _placeholder_text(source_ref):
            issues.append(ProvenanceIssue(fact_id, "placeholder_source_ref", "source_ref", source_ref))
    issues.extend(_source_metadata_issues(fact_id, fact))
    issues.extend(_span_issues(fact_id, fact))
    issues.extend(_fact_quality_issues(fact_id, fact))
    return tuple(issues)


def _derived_issues(fact_id: str, fact: JsonObject) -> Tuple[ProvenanceIssue, ...]:
    evidence = _json_object(fact.get("derivation_evidence"))
    source_fact_ids = evidence.get("source_fact_ids")
    method = _text_or(evidence.get("derivation_method"), "")
    if isinstance(source_fact_ids, list) and source_fact_ids and not _placeholder_text(method):
        return ()
    return (ProvenanceIssue(fact_id, "missing_derivation_evidence", "derivation_evidence"),)


def _source_metadata_issues(fact_id: str, fact: JsonObject) -> Tuple[ProvenanceIssue, ...]:
    issues: List[ProvenanceIssue] = []
    for field_name in ("source_document_id", "chunk_id"):
        value = _text_or(fact.get(field_name), "")
        if not value:
            issues.append(ProvenanceIssue(fact_id, "missing_{}".format(field_name), field_name))
        elif _placeholder_text(value):
            issues.append(ProvenanceIssue(fact_id, "placeholder_{}".format(field_name), field_name, value))
    source_hash = _text_or(fact.get("source_hash"), "")
    if not source_hash:
        issues.append(ProvenanceIssue(fact_id, "missing_source_hash", "source_hash"))
    elif _placeholder_text(source_hash):
        issues.append(ProvenanceIssue(fact_id, "placeholder_source_hash", "source_hash", source_hash))
    elif SHA256_RE.fullmatch(source_hash) is None:
        issues.append(ProvenanceIssue(fact_id, "invalid_source_hash", "source_hash", source_hash))
    return tuple(issues)


def _span_issues(fact_id: str, fact: JsonObject) -> Tuple[ProvenanceIssue, ...]:
    line_start = fact.get("line_start")
    line_end = fact.get("line_end")
    if not isinstance(line_start, int) or not isinstance(line_end, int) or isinstance(line_start, bool) or isinstance(line_end, bool):
        return (ProvenanceIssue(fact_id, "missing_line_span", "line_start"),)
    if line_start < 1 or line_end < line_start:
        return (ProvenanceIssue(fact_id, "invalid_line_span", "line_start"),)
    return ()


def _fact_quality_issues(fact_id: str, fact: JsonObject) -> Tuple[ProvenanceIssue, ...]:
    issues: List[ProvenanceIssue] = []
    for field_name in ("extractor_version", "ontology_version", "review_status"):
        value = _text_or(fact.get(field_name), "")
        if not value:
            issues.append(ProvenanceIssue(fact_id, "missing_{}".format(field_name), field_name))
        elif _placeholder_text(value):
            issues.append(ProvenanceIssue(fact_id, "placeholder_{}".format(field_name), field_name, value))
    confidence = fact.get("confidence")
    if not isinstance(confidence, (float, int)) or isinstance(confidence, bool) or not 0.0 <= confidence <= 1.0:
        issues.append(ProvenanceIssue(fact_id, "invalid_confidence", "confidence"))
    return tuple(issues)


def _version_changes(previous: JsonObject, current: JsonObject) -> Tuple[SnapshotVersionChange, ...]:
    changes: List[SnapshotVersionChange] = []
    for field_name in VERSION_FIELDS:
        previous_value = previous.get(field_name)
        current_value = current.get(field_name)
        if previous_value != current_value:
            changes.append(SnapshotVersionChange(field_name, previous_value, current_value))
    return tuple(changes)


def _versions(graph_snapshot: JsonObject) -> JsonObject:
    return {field_name: _canonical_value(graph_snapshot.get(field_name)) for field_name in VERSION_FIELDS}


def _fingerprints(value: JsonValue, id_field: str, fields: Tuple[str, ...]) -> FingerprintMap:
    fingerprints: FingerprintMap = {}
    for item in _json_objects(value):
        identifier = _text_or(item.get(id_field), "")
        if identifier:
            fingerprints[identifier] = _hash_json(_select_fields(item, fields))
    return fingerprints


def _fingerprint_json(fingerprints: FingerprintMap) -> JsonObject:
    return {key: value for key, value in fingerprints.items()}


def _select_fields(item: JsonObject, fields: Tuple[str, ...]) -> JsonObject:
    return {
        field: _canonical_value(item.get(field))
        for field in fields
        if field in item and field not in RAW_TEXT_KEYS
    }


def _canonical_value(value: JsonValue) -> JsonValue:
    if isinstance(value, dict):
        return {key: _canonical_value(value[key]) for key in sorted(value) if key not in RAW_TEXT_KEYS}
    if isinstance(value, list):
        return [_canonical_value(item) for item in value]
    return value


def _source_refs(fact: JsonObject) -> Tuple[str, ...]:
    raw_refs = fact.get("source_refs")
    if isinstance(raw_refs, list):
        refs = tuple(item for item in raw_refs if isinstance(item, str) and item)
        if refs:
            return refs
    source_ref = fact.get("source_ref")
    if isinstance(source_ref, str) and source_ref:
        return (source_ref,)
    return ()


def _json_objects(value: JsonValue) -> Tuple[JsonObject, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, dict))


def _json_object(value: JsonValue) -> JsonObject:
    return value if isinstance(value, dict) else {}


def _graph_json(graph: GraphInput) -> JsonObject:
    if isinstance(graph, DebtorGraphPayload):
        return graph.to_json()
    return graph


def _added(previous: FingerprintMap, current: FingerprintMap) -> Tuple[str, ...]:
    return tuple(sorted(set(current) - set(previous)))


def _removed(previous: FingerprintMap, current: FingerprintMap) -> Tuple[str, ...]:
    return tuple(sorted(set(previous) - set(current)))


def _changed(previous: FingerprintMap, current: FingerprintMap) -> Tuple[str, ...]:
    return tuple(sorted(key for key in set(previous) & set(current) if previous[key] != current[key]))


def _placeholder_text(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in PLACEHOLDER_SOURCE_REFS or normalized.startswith("placeholder:") or normalized.startswith("todo:") or normalized.startswith("[")


def _text_or(value: JsonValue, default: str) -> str:
    return value if isinstance(value, str) else default


def _hash_json(value: JsonValue) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
