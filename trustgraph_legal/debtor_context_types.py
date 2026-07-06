from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Final, List, Optional, Tuple, Union

from trustgraph_legal import __version__

JsonScalar = Optional[Union[str, int, float, bool]]
JsonValue = Union[JsonScalar, List["JsonValue"], Dict[str, "JsonValue"]]
JsonObject = Dict[str, JsonValue]

SCHEMA_VERSION: Final = "recova-debtor-context-graph/v1"
EXTRACTOR_VERSION: Final = "trustgraph_legal.debtor_context_types@{}".format(__version__)
DOCUMENT_ASSEMBLY_VERSION: Final = "recova-document-assembly@v0"
ONTOLOGY_VERSION: Final = "recova-debt-collection@v0"
ROUTE_VERSION: Final = "recova-debt-routes@v0"
LEGAL_RULE_SOURCE_VERSION: Final = "recova-legal-rule-sources@v0"
PLACEHOLDER_SOURCE_REFS: Final = frozenset(
    {
        "",
        "-",
        "missing",
        "n/a",
        "none",
        "null",
        "placeholder",
        "source_ref",
        "source-ref",
        "todo",
        "unknown",
    }
)


@dataclass(frozen=True, slots=True)
class DocumentPage:
    page_id: str
    source_ref: str
    source_hash: str
    relative_path: str
    page_order: int
    classifier_document_type: str
    review_status: str
    line_count: int
    char_count: int

    def to_json(self) -> JsonObject:
        return {
            "page_id": self.page_id,
            "source_ref": self.source_ref,
            "source_hash": self.source_hash,
            "relative_path": self.relative_path,
            "page_order": self.page_order,
            "classifier_document_type": self.classifier_document_type,
            "review_status": self.review_status,
            "line_count": self.line_count,
            "char_count": self.char_count,
        }


@dataclass(frozen=True, slots=True)
class DocumentAssembly:
    assembly_id: str
    document_id: str
    canonical_document_type: str
    page_ids: Tuple[str, ...]
    source_refs: Tuple[str, ...]
    source_hashes: Tuple[str, ...]
    confidence: float
    review_status: str
    assembly_method: str = DOCUMENT_ASSEMBLY_VERSION
    procedure_episode_id: Optional[str] = None

    def to_json(self) -> JsonObject:
        return {
            "assembly_id": self.assembly_id,
            "document_id": self.document_id,
            "canonical_document_type": self.canonical_document_type,
            "page_ids": list(self.page_ids),
            "source_refs": list(self.source_refs),
            "source_hashes": list(self.source_hashes),
            "confidence": self.confidence,
            "review_status": self.review_status,
            "assembly_method": self.assembly_method,
            "procedure_episode_id": self.procedure_episode_id,
        }


@dataclass(frozen=True, slots=True)
class ProcedureEpisode:
    episode_id: str
    episode_type: str
    document_ids: Tuple[str, ...]
    source_refs: Tuple[str, ...]
    sequence_order: int
    review_status: str

    def to_json(self) -> JsonObject:
        return {
            "episode_id": self.episode_id,
            "episode_type": self.episode_type,
            "document_ids": list(self.document_ids),
            "source_refs": list(self.source_refs),
            "sequence_order": self.sequence_order,
            "review_status": self.review_status,
        }


@dataclass(frozen=True)
class FactAssertionSourceRefError(Exception):
    fact_id: str
    source_ref: Optional[str] = None

    def __str__(self) -> str:
        if self.source_ref is None:
            return "fact {} has no source_refs".format(self.fact_id)
        return "fact {} has placeholder source_ref {}".format(self.fact_id, self.source_ref)


@dataclass(frozen=True, slots=True)
class FactAssertion:
    fact_id: str
    subject_id: str
    predicate: str
    object_value: JsonValue
    confidence: float
    source_refs: Tuple[str, ...]
    source_document_id: str
    source_hash: str
    chunk_id: str
    line_start: int
    line_end: int
    review_status: str
    extractor_version: str = EXTRACTOR_VERSION
    ontology_version: str = ONTOLOGY_VERSION
    valid_time: Optional[str] = None
    observed_time: Optional[str] = None
    derived: bool = False

    def __post_init__(self) -> None:
        if not self.source_refs:
            raise FactAssertionSourceRefError(self.fact_id)
        for source_ref in self.source_refs:
            if _is_placeholder_source_ref(source_ref):
                raise FactAssertionSourceRefError(self.fact_id, source_ref)

    def to_json(self) -> JsonObject:
        return {
            "fact_id": self.fact_id,
            "subject_id": self.subject_id,
            "predicate": self.predicate,
            "object_value": self.object_value,
            "confidence": self.confidence,
            "source_ref": self.source_refs[0],
            "source_refs": list(self.source_refs),
            "source_document_id": self.source_document_id,
            "source_hash": self.source_hash,
            "chunk_id": self.chunk_id,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "extractor_version": self.extractor_version,
            "ontology_version": self.ontology_version,
            "valid_time": self.valid_time,
            "observed_time": self.observed_time,
            "review_status": self.review_status,
            "derived": self.derived,
        }


@dataclass(frozen=True, slots=True)
class RouteCandidate:
    route_id: str
    route_label: str
    status: str
    required_facts: Tuple[str, ...]
    missing_facts: Tuple[str, ...]
    blocking_facts: Tuple[str, ...]
    legal_source_refs: Tuple[str, ...]
    source_fact_ids: Tuple[str, ...]
    confidence: float
    review_status: str
    no_direct_execution: bool = True

    def to_json(self) -> JsonObject:
        return {
            "route_id": self.route_id,
            "route_label": self.route_label,
            "status": self.status,
            "required_facts": list(self.required_facts),
            "missing_facts": list(self.missing_facts),
            "blocking_facts": list(self.blocking_facts),
            "legal_source_refs": list(self.legal_source_refs),
            "source_fact_ids": list(self.source_fact_ids),
            "confidence": self.confidence,
            "review_status": self.review_status,
            "no_direct_execution": self.no_direct_execution,
        }


@dataclass(frozen=True, slots=True)
class GraphSnapshot:
    graph_snapshot_id: str
    source_bundle_hash: str
    generated_at: str
    fact_assertion_ids: Tuple[str, ...]
    route_candidate_ids: Tuple[str, ...]
    extractor_versions: Tuple[str, ...] = (EXTRACTOR_VERSION,)
    ontology_version: str = ONTOLOGY_VERSION
    route_version: str = ROUTE_VERSION
    legal_rule_source_version: str = LEGAL_RULE_SOURCE_VERSION

    def to_json(self) -> JsonObject:
        return {
            "graph_snapshot_id": self.graph_snapshot_id,
            "source_bundle_hash": self.source_bundle_hash,
            "extractor_versions": list(self.extractor_versions),
            "ontology_version": self.ontology_version,
            "route_version": self.route_version,
            "legal_rule_source_version": self.legal_rule_source_version,
            "generated_at": self.generated_at,
            "fact_assertion_ids": list(self.fact_assertion_ids),
            "route_candidate_ids": list(self.route_candidate_ids),
        }


@dataclass(frozen=True, slots=True)
class DebtorGraphPayload:
    debtor_graph_id: str
    graph_snapshot: GraphSnapshot
    identity_resolution: JsonObject
    case_packets: Tuple[JsonObject, ...]
    document_pages: Tuple[DocumentPage, ...]
    document_assemblies: Tuple[DocumentAssembly, ...]
    fact_assertions: Tuple[FactAssertion, ...]
    claims: Tuple[JsonObject, ...]
    enforcement_titles: Tuple[JsonObject, ...]
    procedure_episodes: Tuple[ProcedureEpisode, ...]
    asset_hints: Tuple[JsonObject, ...]
    stop_gates: Tuple[JsonObject, ...]
    route_candidates: Tuple[RouteCandidate, ...]
    review_items: Tuple[JsonObject, ...]

    def to_json(self) -> JsonObject:
        return {
            "schema_version": SCHEMA_VERSION,
            "debtor_graph_id": self.debtor_graph_id,
            "graph_snapshot_id": self.graph_snapshot.graph_snapshot_id,
            "graph_snapshot": self.graph_snapshot.to_json(),
            "identity_resolution": self.identity_resolution,
            "case_packets": list(self.case_packets),
            "document_pages": [page.to_json() for page in self.document_pages],
            "document_assemblies": [assembly.to_json() for assembly in self.document_assemblies],
            "fact_assertions": [fact.to_json() for fact in self.fact_assertions],
            "claims": list(self.claims),
            "enforcement_titles": list(self.enforcement_titles),
            "procedure_episodes": [episode.to_json() for episode in self.procedure_episodes],
            "asset_hints": list(self.asset_hints),
            "stop_gates": list(self.stop_gates),
            "route_candidates": [candidate.to_json() for candidate in self.route_candidates],
            "review_items": list(self.review_items),
            "summary": {
                "case_packets": len(self.case_packets),
                "document_pages": len(self.document_pages),
                "document_assemblies": len(self.document_assemblies),
                "fact_assertions": len(self.fact_assertions),
                "route_candidates": len(self.route_candidates),
                "review_items": len(self.review_items),
            },
            "pii_profile": {"raw_text_included": False, "source_text_included": False},
        }


def _is_placeholder_source_ref(source_ref: str) -> bool:
    normalized = source_ref.strip().lower()
    return (
        normalized in PLACEHOLDER_SOURCE_REFS
        or normalized.startswith("placeholder:")
        or normalized.startswith("todo:")
        or normalized.startswith("[")
    )
