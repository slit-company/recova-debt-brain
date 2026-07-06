from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from trustgraph_legal.debtor_context_types import (
    DebtorGraphPayload,
    DocumentAssembly,
    DocumentPage,
    FactAssertion,
    GraphSnapshot,
    JsonObject,
    JsonValue,
)
from trustgraph_legal.document_assembly import DocumentAssemblyPayload
from trustgraph_legal.fields import DocumentInput, ExtractedField, extract_fields, normalize_document_type

GENERATED_AT: Final = "2026-07-06T00:00:00Z"
CASE_TOKEN_RE: Final = re.compile(r"\[CASE_PACKET_TOKEN_[A-Z0-9_]+\]")
FIELD_PREDICATES: Final = {
    "principal_amount": "claim_balance",
    "claim_amount": "claim_balance",
    "claimed_total": "claim_balance",
    "interest_rate": "claim_basis",
    "court_case_number": "enforceable_title",
    "linked_title_case_number": "enforceable_title",
    "service_result": "service_path",
    "finality_result": "final_title_or_written_title",
    "execution_clause_status": "executable_copy",
    "third_party_debtor_role": "third_party_debtor_hint",
    "attachment_target": "third_party_debtor_bank_hint",
    "party_identity_key": "debtor_identity",
    "procedure_status": "insolvency_signal",
    "asset_class": "asset_value_low_or_priority_unclear",
    "exemption_review_status": "protection_or_exemption_review",
}
DOCUMENT_TYPE_PREDICATES: Final = {
    "payment-order": ("enforceable_title", "money_payment_enforcement_title"),
    "attachment-collection-order": ("third_party_debtor_hint", "third_party_debtor_bank_hint"),
    "service-finality-proof": ("service_path", "final_title_or_written_title", "executable_copy"),
    "identity-evidence": ("identity_uncertain",),
    "insolvency-credit-recovery": ("insolvency_signal",),
    "asset-evidence": ("asset_value_low_or_priority_unclear",),
}


@dataclass(frozen=True, slots=True)
class DebtorContextInputError(Exception):
    location: str
    detail: str

    def __str__(self) -> str:
        return "{}: {}".format(self.location, self.detail)


@dataclass(frozen=True, slots=True)
class _PageContext:
    page: DocumentPage
    assembly: DocumentAssembly
    text: str | None


@dataclass(frozen=True, slots=True)
class _FactDraft:
    context: _PageContext
    predicate: str
    value: JsonValue
    confidence: float
    line_start: int
    line_end: int
    derived: bool


def build_debtor_context(
    assembly_payload: DocumentAssemblyPayload | JsonObject,
    repo_root: Path | None = None,
) -> DebtorGraphPayload:
    payload = _typed_payload(assembly_payload)
    _require_full_payload(payload)
    contexts = _page_contexts(payload, repo_root)
    bundle_hash = _source_bundle_hash(payload.document_pages)
    graph_id = "debtor-graph:{}".format(_digest_part(bundle_hash))
    facts = _facts(contexts)
    identity, reviews = _identity_resolution(graph_id, bundle_hash, facts)
    return DebtorGraphPayload(
        debtor_graph_id=graph_id,
        graph_snapshot=GraphSnapshot(
            graph_snapshot_id="snapshot:{}".format(_digest_part(bundle_hash)),
            source_bundle_hash=bundle_hash,
            generated_at=GENERATED_AT,
            fact_assertion_ids=tuple(fact.fact_id for fact in facts),
            route_candidate_ids=(),
        ),
        identity_resolution=identity,
        case_packets=_case_packets(graph_id, contexts, facts),
        document_pages=payload.document_pages,
        document_assemblies=payload.document_assemblies,
        fact_assertions=facts,
        claims=(),
        enforcement_titles=(),
        procedure_episodes=(),
        asset_hints=(),
        stop_gates=(),
        route_candidates=(),
        review_items=reviews,
    )


def _typed_payload(assembly_payload: DocumentAssemblyPayload | JsonObject) -> DocumentAssemblyPayload:
    if isinstance(assembly_payload, DocumentAssemblyPayload):
        return assembly_payload
    if isinstance(assembly_payload, dict):
        raise DebtorContextInputError("document_assembly", "summary-only JSON is not accepted")
    raise DebtorContextInputError("document_assembly", "unsupported assembly payload")


def _require_full_payload(payload: DocumentAssemblyPayload) -> None:
    if not payload.document_pages or not payload.document_assemblies:
        raise DebtorContextInputError("document_assembly", "document_pages and document_assemblies are required")


def _page_contexts(payload: DocumentAssemblyPayload, repo_root: Path | None) -> tuple[_PageContext, ...]:
    assemblies = {page_id: assembly for assembly in payload.document_assemblies for page_id in assembly.page_ids}
    return tuple(
        _PageContext(page=page, assembly=assemblies[page.page_id], text=_page_text(page, repo_root))
        for page in payload.document_pages
        if page.page_id in assemblies
    )


def _page_text(page: DocumentPage, repo_root: Path | None) -> str | None:
    if repo_root is None:
        return None
    path = repo_root / page.relative_path
    return path.read_text(encoding="utf-8") if path.is_file() else None


def _facts(contexts: tuple[_PageContext, ...]) -> tuple[FactAssertion, ...]:
    facts: list[FactAssertion] = []
    for context in contexts:
        facts.extend(_document_type_facts(context))
        facts.extend(_field_facts(context))
    return tuple(sorted(facts, key=lambda fact: fact.fact_id))


def _document_type_facts(context: _PageContext) -> tuple[FactAssertion, ...]:
    document_type = normalize_document_type(context.assembly.canonical_document_type)
    return tuple(
        _fact(_FactDraft(context, predicate, {"document_type": document_type}, context.assembly.confidence, 1, max(context.page.line_count, 1), True))
        for predicate in DOCUMENT_TYPE_PREDICATES.get(document_type, ())
    )


def _field_facts(context: _PageContext) -> tuple[FactAssertion, ...]:
    if context.text is None:
        return ()
    fields = extract_fields(
        DocumentInput(context.assembly.document_id, context.assembly.canonical_document_type, context.page.source_ref, context.text)
    ).fields
    return tuple(_field_fact(context, field) for field in fields if field.name in FIELD_PREDICATES)


def _field_fact(context: _PageContext, field: ExtractedField) -> FactAssertion:
    return _fact(
        _FactDraft(
            context,
            FIELD_PREDICATES[field.name],
            field.normalized_value,
            field.confidence,
            field.line_start,
            field.line_end,
            False,
        )
    )


def _fact(draft: _FactDraft) -> FactAssertion:
    return FactAssertion(
        fact_id="fact:{}:{}".format(draft.predicate, _hash_text(_fact_key(draft))[:16]),
        subject_id=draft.context.assembly.document_id,
        predicate=draft.predicate,
        object_value=draft.value,
        confidence=round(draft.confidence, 2),
        source_refs=(draft.context.page.source_ref,),
        source_document_id=draft.context.assembly.document_id,
        source_hash=draft.context.page.source_hash,
        chunk_id="{}#L{}-{}".format(draft.context.page.page_id, draft.line_start, draft.line_end),
        line_start=draft.line_start,
        line_end=draft.line_end,
        review_status="accepted" if draft.confidence >= 0.75 else "needs_review",
        derived=draft.derived,
    )


def _fact_key(draft: _FactDraft) -> str:
    return json.dumps(
        {
            "document": draft.context.assembly.document_id,
            "object": draft.value,
            "predicate": draft.predicate,
            "source": draft.context.page.source_ref,
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def _identity_resolution(
    graph_id: str,
    bundle_hash: str,
    facts: tuple[FactAssertion, ...],
) -> tuple[JsonObject, tuple[JsonObject, ...]]:
    identity_facts = tuple(fact for fact in facts if fact.predicate == "debtor_identity")
    if identity_facts:
        return {
            "status": "identity_evidence_available",
            "method": "identity_evidence_fact_hash",
            "identity_evidence_hash": "sha256:{}".format(_hash_text("|".join(fact.fact_id for fact in identity_facts))),
            "source_fact_ids": _json_values(fact.fact_id for fact in identity_facts),
        }, ()
    return {
        "status": "identity_unresolved",
        "method": "source_bundle_hash_fallback",
        "debtor_subject_id": graph_id,
        "source_bundle_hash": bundle_hash,
    }, (
        {
            "review_item_id": "review:identity-unresolved:{}".format(_digest_part(bundle_hash)),
            "reason_code": "identity_unresolved",
            "review_reason": "identity_unresolved",
            "source_bundle_hash": bundle_hash,
        },
    )


def _case_packets(graph_id: str, contexts: tuple[_PageContext, ...], facts: tuple[FactAssertion, ...]) -> tuple[JsonObject, ...]:
    refs_by_packet: dict[str, set[str]] = {}
    docs_by_packet: dict[str, set[str]] = {}
    for context in contexts:
        packet_id = _case_packet_id(graph_id, context)
        refs_by_packet.setdefault(packet_id, set()).add(context.page.source_ref)
        docs_by_packet.setdefault(packet_id, set()).add(context.assembly.document_id)
    packets: list[JsonObject] = []
    for packet_id in sorted(refs_by_packet):
        refs = refs_by_packet[packet_id]
        packets.append({
            "case_packet_id": packet_id,
            "document_ids": _json_values(sorted(docs_by_packet[packet_id])),
            "source_refs": _json_values(sorted(refs)),
            "fact_ids": _json_values(fact.fact_id for fact in facts if fact.source_refs[0] in refs),
            "identity_status": "identity_unresolved",
        })
    return tuple(packets)


def _case_packet_id(graph_id: str, context: _PageContext) -> str:
    if context.text is not None:
        match = CASE_TOKEN_RE.search(context.text)
        if match is not None:
            return "case-packet:{}".format(_hash_text(match.group(0))[:16])
    return "case-packet:{}".format(_hash_text("{}:{}".format(graph_id, context.assembly.document_id))[:16])


def _json_values(values: Iterable[str]) -> list[JsonValue]:
    return [value for value in values]


def _source_bundle_hash(pages: tuple[DocumentPage, ...]) -> str:
    return "sha256:{}".format(_hash_text("\n".join(sorted(page.source_hash for page in pages))))


def _digest_part(source_bundle_hash: str) -> str:
    return source_bundle_hash.removeprefix("sha256:")[:16]


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
