from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from trustgraph_legal.debtor_context_types import JsonObject
from trustgraph_legal.domain_graph_adapter_case_graph import case_graph
from trustgraph_legal.domain_graph_adapter_handles import (
    claim_roots,
    fact_handles,
    governance_handles,
    legal_source_ids,
    route_handles,
    snapshot_handle,
    source_refs_from_handles,
)
from trustgraph_legal.domain_graph_adapter_shared import (
    DomainGraphAdapterError,
    GraphInput,
    graph_json,
    json_object,
    pii_profile,
    required_text,
    text,
)

SCHEMA_VERSION: Final = "trustgraph-claim-domain-adapter/v1"
DOMAIN_ONTOLOGY_VERSION: Final = "recova-debt-collection-v1@1.0.0"
NON_EXECUTION_SEMANTICS: Final = "adapter_projection_only_human_review_required"
__all__ = [
    "ClaimDomainAdapterPayload",
    "DomainGraphAdapterError",
    "adapt_debtor_graph_to_claim_domain",
]


@dataclass(frozen=True, slots=True)
class ClaimDomainAdapterPayload:
    payload: JsonObject

    def to_json(self) -> JsonObject:
        return self.payload


def adapt_debtor_graph_to_claim_domain(
    graph: GraphInput,
    governance_records: Sequence[JsonObject] = (),
) -> ClaimDomainAdapterPayload:
    graph_payload = graph_json(graph)
    graph_snapshot = json_object(graph_payload.get("graph_snapshot"))
    debtor_graph_id = required_text(graph_payload, "debtor_graph_id", "graph")
    graph_snapshot_id = required_text(graph_snapshot, "graph_snapshot_id", "graph_snapshot")
    source_bundle_hash = required_text(graph_snapshot, "source_bundle_hash", "graph_snapshot")
    roots = claim_roots(graph_payload, debtor_graph_id, graph_snapshot_id, source_bundle_hash)
    primary_claim_id = text(roots[0].get("claim_id"))
    facts = fact_handles(graph_payload, primary_claim_id)
    routes = route_handles(graph_payload, primary_claim_id)
    governance = governance_handles(governance_records, primary_claim_id)
    payload: JsonObject = {
        "schema_version": SCHEMA_VERSION,
        "domain_ontology_version": DOMAIN_ONTOLOGY_VERSION,
        "debtor_graph_id": debtor_graph_id,
        "graph_snapshot_id": graph_snapshot_id,
        "source_bundle_hash": source_bundle_hash,
        "claim_root": roots[0],
        "claim_roots": list(roots),
        "graph_snapshot": snapshot_handle(graph_snapshot),
        "fact_handles": list(facts),
        "route_candidates": list(routes),
        "governance_records": list(governance),
        "case_graph": case_graph(
            debtor_graph_id,
            graph_snapshot_id,
            source_bundle_hash,
            roots,
            facts,
            routes,
            governance,
        ),
        "source_refs": list(source_refs_from_handles(facts, governance)),
        "legal_source_refs": list(legal_source_ids(routes)),
        "summary": {
            "claim_roots": len(roots),
            "fact_handles": len(facts),
            "route_candidates": len(routes),
            "governance_records": len(governance),
        },
        "non_execution_semantics": NON_EXECUTION_SEMANTICS,
        "pii_profile": pii_profile(),
    }
    return ClaimDomainAdapterPayload(payload)
