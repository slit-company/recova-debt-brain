from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Final, List, Optional, Sequence, Tuple, Union

from trustgraph_legal import __version__
from trustgraph_legal.classifier import classify_text
from trustgraph_legal.fields import EXTRACTOR_VERSION as FIELD_EXTRACTOR_VERSION, DocumentInput, ExtractedField, extract_fields

JsonScalar = Optional[Union[str, int, float, bool]]
JsonValue = Union[JsonScalar, List["JsonValue"], Dict[str, "JsonValue"]]

SCHEMA_VERSION: Final = "trustgraph-legal-case-graph/v1"
EXTRACTOR_VERSION: Final = "trustgraph_legal.case_graph@{}".format(__version__)
ONTOLOGY_VERSION: Final = "recova-debt-collection@v0"
PROMPT_VERSION: Final = "legal-ontology-extraction@v0"
ROLE_FIELDS: Final[Dict[str, str]] = {"creditor_role": "creditor", "debtor_role": "debtor", "third_party_debtor_role": "third-party-debtor", "assignor_role": "assignor", "assignee_role": "assignee", "served_party_role": "debtor", "identity_subject_role": "debtor", "insolvency_subject_role": "debtor", "asset_subject_role": "debtor", "organization_role": "asset-holder"}
ORG_ROLES: Final = {"creditor", "third-party-debtor", "assignor", "assignee", "asset-holder"}
AMOUNT_FIELDS: Final = {"claim_amount", "principal_amount", "claimed_total"}


@dataclass(frozen=True)
class ManifestDocument:
    document_id: str; document_type: str; source_fixture_path: str; source_hash: str


@dataclass(frozen=True)
class SourceDocument:
    manifest: ManifestDocument; canonical_type: str; confidence: float; fields: Tuple[ExtractedField, ...]


@dataclass(frozen=True)
class CaseGraphPayload:
    graph: Dict[str, JsonValue]

    def to_json(self) -> Dict[str, JsonValue]: return self.graph


class CaseGraphInputError(Exception):
    def __init__(self, manifest_path: Path, detail: str) -> None:
        self.manifest_path = manifest_path; self.detail = detail; super().__init__()

    def __str__(self) -> str: return "{}: {}".format(self.manifest_path, self.detail)


def build_case_graph(manifest_path: Path, repo_root: Optional[Path] = None) -> CaseGraphPayload:
    root = repo_root if repo_root is not None else Path.cwd()
    documents = tuple(_load_source_document(item, root) for item in _manifest_documents(manifest_path))
    packet = _build_packet(documents)
    entities = packet["entities"]
    findings = packet["findings"]
    summary = {"case_packets": 1, "documents": len(documents), "entities": len(entities), "edges": len(packet["edges"]), "unresolved_identities": sum(1 for item in findings if item["reason"] == "identity_uncertain"), "review_items": len(findings)}
    payload = {"schema_version": SCHEMA_VERSION, "ontology_version": ONTOLOGY_VERSION, "prompt_version": PROMPT_VERSION, "extractor_version": EXTRACTOR_VERSION, "summary": summary, "pii_profile": {"raw_text_included": False, "source_text_included": False}, "case_packets": [packet]}
    return CaseGraphPayload(payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python3 -m trustgraph_legal.case_graph")
    parser.add_argument("--fixtures", required=True)
    parser.add_argument("--out", required=True)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    graph = build_case_graph(Path(args.fixtures), Path.cwd())
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(graph.to_json(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"case_packets": 1, "evidence": str(output_path)}, sort_keys=True))
    return 0


def _manifest_documents(manifest_path: Path) -> Tuple[ManifestDocument, ...]:
    raw: JsonValue = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise CaseGraphInputError(manifest_path, "manifest root must be an object")
    raw_documents = raw.get("documents")
    if not isinstance(raw_documents, list):
        raise CaseGraphInputError(manifest_path, "missing documents list")
    documents: List[ManifestDocument] = []
    for index, item in enumerate(raw_documents):
        if not isinstance(item, dict):
            raise CaseGraphInputError(manifest_path, "document {} must be an object".format(index))
        document_id = item.get("document_id")
        document_type = item.get("document_type")
        source_fixture_path = item.get("source_fixture_path")
        source_hash = item.get("source_hash")
        if not all(isinstance(value, str) for value in (document_id, document_type, source_fixture_path, source_hash)):
            raise CaseGraphInputError(manifest_path, "document {} has invalid metadata".format(index))
        documents.append(ManifestDocument(document_id, document_type, source_fixture_path, source_hash))
    return tuple(documents)


def _load_source_document(document: ManifestDocument, repo_root: Path) -> SourceDocument:
    path = repo_root / document.source_fixture_path
    text = path.read_text(encoding="utf-8")
    classified = classify_text(document.document_id, document.source_fixture_path, text)
    fields = extract_fields(
        DocumentInput(document.document_id, document.document_type, "fixture:{}".format(document.source_fixture_path), text)
    )
    return SourceDocument(document, fields.document_type, min(classified.confidence, fields.confidence or classified.confidence), fields.fields)


def _build_packet(documents: Tuple[SourceDocument, ...]) -> Dict[str, JsonValue]:
    all_fields = tuple(field for document in documents for field in document.fields)
    document_hashes = tuple(document.manifest.source_hash for document in documents)
    court_cases = _field_values(all_fields, {"court_case_number", "linked_title_case_number"})
    claim_material = _field_values(all_fields, {"assigned_claim_token", "linked_claim_token", "claim_amount", "principal_amount", "court_case_number"}) or document_hashes
    title_material = _field_values(all_fields, {"court_case_number", "linked_title_case_number", "execution_clause_status"}) or document_hashes
    claim_id, claim_key = _derived_key("claim_id", claim_material, "derived from claim/title fixture facts")
    title_id, title_key = _derived_key("enforcement_title_id", title_material, "derived from title case and service/finality facts")
    case_packet_id, packet_key = _derived_key("case_packet_id", court_cases + (claim_id, title_id) + document_hashes, "derived from court, claim, title, and document hashes")
    identity_keys = _field_values(all_fields, {"party_identity_key"})
    evidence_keys = [
        _key_json("case_packet_id", case_packet_id, 0.96, "case-packet-id", "deterministic packet resolver", [packet_key]),
        _key_json("court_case_number", list(court_cases), 0.94, "court-case-number", "field evidence", _field_refs(all_fields, {"court_case_number", "linked_title_case_number"})),
        _key_json("claim_id", claim_id, 0.88, "claim-id", "deterministic claim id derivation", [claim_key]),
        _key_json("enforcement_title_id", title_id, 0.89, "enforcement-title-id", "deterministic title id derivation", [title_key]),
        _key_json("party_identity_key", list(identity_keys), 0.91 if identity_keys else 0.2, "party-identity-key", "identity evidence field" if identity_keys else "missing identity evidence", _field_refs(all_fields, {"party_identity_key"})),
        _key_json("document_hash", list(document_hashes), 1.0, "source-hash", "manifest source_hash mapped to Todo 6 document_hash", []),
    ]
    entities: List[Dict[str, JsonValue]] = []
    edges: List[Dict[str, JsonValue]] = []
    findings: List[Dict[str, JsonValue]] = []
    _add_document_graph(case_packet_id, documents, entities, edges)
    _add_party_graph(case_packet_id, all_fields, identity_keys, entities, edges, findings)
    _add_claim_graph(case_packet_id, claim_id, title_id, all_fields, entities, edges)
    _add_asset_graph(case_packet_id, all_fields, entities, edges)
    _add_ledger_graph(case_packet_id, all_fields, entities, edges)
    _add_findings(case_packet_id, all_fields, entities, edges, findings)
    return {"id": case_packet_id, "entity_type": "CasePacket", "ontology_class": "case-packet", "case_packet_id": case_packet_id, "case_projection": {"entity_type": "Case", "derived": True, "ontology_class": None, "maps_to": "case-packet"}, "evidence_keys": evidence_keys, "entities": entities, "edges": edges, "findings": findings, "identity_resolution": {"merge_decisions": _identity_decisions(findings)}}


def _add_document_graph(case_packet_id: str, documents: Tuple[SourceDocument, ...], entities: List[Dict[str, JsonValue]], edges: List[Dict[str, JsonValue]]) -> None:
    for document in documents:
        doc_id = "document:{}".format(document.manifest.document_id)
        provenance = _document_provenance(document)
        entities.append(_entity(doc_id, "Document", "legal-document", document.canonical_type, provenance, {"document_hash": document.manifest.source_hash}))
        entities.append(_entity("provenance:{}".format(document.manifest.document_id), "DocumentProvenance", "document-provenance", EXTRACTOR_VERSION, provenance, {"derived": True}))
        edges.append(_edge(case_packet_id, "has-document", doc_id, provenance))
        edges.append(_edge(doc_id, "has-provenance", "provenance:{}".format(document.manifest.document_id), provenance, {"derived": True}))
        for field in document.fields:
            span_id = _field_id("span", field)
            entities.append(_entity(span_id, "SourceSpan", "source-span", field.name, _field_provenance(field), {"field_name": field.name}))
            edges.append(_edge(doc_id, "has-source-span", span_id, _field_provenance(field)))


def _add_party_graph(case_packet_id: str, fields: Tuple[ExtractedField, ...], identity_keys: Tuple[str, ...], entities: List[Dict[str, JsonValue]], edges: List[Dict[str, JsonValue]], findings: List[Dict[str, JsonValue]]) -> None:
    identity_by_value = _identity_by_value(fields, identity_keys)
    debtor_without_identity: List[Dict[str, JsonValue]] = []
    for field in fields:
        role = ROLE_FIELDS.get(field.name)
        if role is None:
            continue
        identity_key = identity_by_value.get(field.normalized_value)
        party_id = "party:{}".format(_hash(identity_key if identity_key is not None else "{}:{}:{}".format(role, field.normalized_value, field.document_id)))
        role_id = _field_id("role", field)
        if not any(entity["id"] == party_id for entity in entities):
            party_type = "Organization" if role in ORG_ROLES else "Person"
            party_class = "organization-party" if role in ORG_ROLES else "person-party"
            entities.append(_entity(party_id, party_type, party_class, field.normalized_value, _field_provenance(field), {"identity_key": identity_key}))
            edges.append(_edge(case_packet_id, "has-party", party_id, _field_provenance(field)))
        entities.append(_entity(role_id, "".join(part.capitalize() for part in role.split("-")), "party-role", field.normalized_value, _field_provenance(field), {"role": role, "party_id": party_id}))
        edges.append(_edge(party_id, "has-party-role", role_id, _field_provenance(field)))
        if identity_key is None and role == "debtor":
            debtor_without_identity.append({"role_id": role_id, "value": field.normalized_value, "provenance": _field_provenance(field)})
    _add_identity_edges(fields, identity_by_value, entities, edges)
    if len(debtor_without_identity) > 1:
        findings.append({"reason": "identity_uncertain", "severity": "review", "candidates": debtor_without_identity})
        findings.append({"reason": "name_only_without_identity_evidence", "severity": "review", "candidates": debtor_without_identity})


def _add_claim_graph(case_packet_id: str, claim_id: str, title_id: str, fields: Tuple[ExtractedField, ...], entities: List[Dict[str, JsonValue]], edges: List[Dict[str, JsonValue]]) -> None:
    claim_provenance = _first_provenance(fields, {"assigned_claim_token", "linked_claim_token", "claim_amount", "principal_amount"})
    entities.append(_entity(claim_id, "Claim", "claim", claim_id, claim_provenance, {"claim_id": claim_id}))
    edges.append(_edge(case_packet_id, "has-claim", claim_id, claim_provenance))
    title_provenance = _first_provenance(fields, {"court_case_number", "linked_title_case_number", "execution_clause_status"})
    entities.append(_entity(title_id, "EnforcementTitle", "enforcement-title", title_id, title_provenance, {"enforcement_title_id": title_id, "title_type": "payment-order"}))
    edges.append(_edge(case_packet_id, "has-enforcement-title", title_id, title_provenance))
    edges.append(_edge(title_id, "supports-title", claim_id, title_provenance))
    for field in fields:
        if field.name in AMOUNT_FIELDS:
            amount_id = _field_id("amount", field)
            entities.append(_entity(amount_id, "Amount", "amount", field.normalized_value, _field_provenance(field), {"amount_kind": field.name}))
            edges.append(_edge(claim_id, "has-amount", amount_id, _field_provenance(field)))
        if field.name in {"court_case_number", "linked_title_case_number", "service_result", "finality_result", "execution_clause_status"}:
            procedure_id = _field_id("procedure", field)
            entities.append(_entity(procedure_id, "CourtProcedure", "court-procedure", field.normalized_value, _field_provenance(field), {"field_name": field.name}))
            edges.append(_edge(case_packet_id, "has-court-procedure", procedure_id, _field_provenance(field)))


def _add_asset_graph(case_packet_id: str, fields: Tuple[ExtractedField, ...], entities: List[Dict[str, JsonValue]], edges: List[Dict[str, JsonValue]]) -> None:
    for field in fields:
        if field.name == "attachment_target":
            target_id = _field_id("target", field)
            entities.append(_entity(target_id, "AttachmentTarget", "attachment-target", field.normalized_value, _field_provenance(field), {"target_type": "monetary-claim"}))
            edges.append(_edge(case_packet_id, "has-attachment-target", target_id, _field_provenance(field)))
        if field.name == "asset_class":
            evidence_id = _field_id("asset-evidence", field)
            asset_id = _field_id("asset", field)
            entities.append(_entity(evidence_id, "AssetEvidence", "asset-evidence", field.normalized_value, _field_provenance(field), {}))
            entities.append(_entity(asset_id, "Asset", "asset", field.normalized_value, _field_provenance(field), {"asset_class": field.normalized_value}))
            edges.append(_edge(case_packet_id, "has-asset-evidence", evidence_id, _field_provenance(field)))
            edges.append(_edge(evidence_id, "describes-asset", asset_id, _field_provenance(field)))


def _add_ledger_graph(case_packet_id: str, fields: Tuple[ExtractedField, ...], entities: List[Dict[str, JsonValue]], edges: List[Dict[str, JsonValue]]) -> None:
    ledger_fields = tuple(field for field in fields if field.name in {"ledger_event", "recovery_amount", "cost_amount"})
    if not ledger_fields:
        return
    ledger_id = "ledger:{}".format(case_packet_id)
    entities.append(_entity(ledger_id, "OperationalLedger", "operational-ledger", case_packet_id, _field_provenance(ledger_fields[0]), {}))
    edges.append(_edge(case_packet_id, "has-ledger", ledger_id, _field_provenance(ledger_fields[0])))
    for field in ledger_fields:
        entry_id = _field_id("ledger-entry", field)
        entities.append(_entity(entry_id, "LedgerEvent", "ledger-entry", field.normalized_value, _field_provenance(field), {"ledger_entry_type": field.name}))
        edges.append(_edge(ledger_id, "has-ledger-entry", entry_id, _field_provenance(field)))
        if field.name == "recovery_amount":
            tx_id = _field_id("recovery", field)
            entities.append(_entity(tx_id, "RecoveryTransaction", "recovery-transaction", field.normalized_value, _field_provenance(field), {}))
            edges.append(_edge(entry_id, "records-recovery", tx_id, _field_provenance(field)))
        if field.name == "cost_amount":
            cost_id = _field_id("cost", field)
            entities.append(_entity(cost_id, "Cost", "cost-entry", field.normalized_value, _field_provenance(field), {}))
            edges.append(_edge(entry_id, "records-cost", cost_id, _field_provenance(field)))


def _add_findings(case_packet_id: str, fields: Tuple[ExtractedField, ...], entities: List[Dict[str, JsonValue]], edges: List[Dict[str, JsonValue]], findings: List[Dict[str, JsonValue]]) -> None:
    for field in fields:
        if field.name in {"exemption_review_status", "procedure_status"}:
            finding_id = _field_id("legal-check", field)
            entities.append(_entity(finding_id, "RuleFinding", "legal-check", field.normalized_value, _field_provenance(field), {"reason": field.name}))
            edges.append(_edge(case_packet_id, "has-legal-check", finding_id, _field_provenance(field)))
            findings.append({"reason": field.name, "severity": "review", "provenance": _field_provenance(field)})


def _add_identity_edges(fields: Tuple[ExtractedField, ...], identity_by_value: Dict[str, str], entities: List[Dict[str, JsonValue]], edges: List[Dict[str, JsonValue]]) -> None:
    for subject, identity_key in identity_by_value.items():
        source = next(field for field in fields if field.normalized_value == subject)
        identity_id = "identity:{}".format(_hash(identity_key))
        entities.append(_entity(identity_id, "IdentityEvidence", "identity-evidence", identity_key, _field_provenance(source), {"party_identity_key": identity_key}))
        for entity in entities:
            if entity.get("value") == subject and entity.get("ontology_class") in {"person-party", "organization-party"}:
                edges.append(_edge(entity["id"], "supported-by-identity", identity_id, _field_provenance(source)))


def _entity(entity_id: str, entity_type: str, ontology_class: str, value: JsonValue, provenance: Dict[str, JsonValue], extra: Dict[str, JsonValue]) -> Dict[str, JsonValue]:
    payload = {"id": entity_id, "entity_type": entity_type, "ontology_class": ontology_class, "value": value, "provenance": provenance}
    payload.update(extra)
    return payload


def _edge(source: str, predicate: str, target: str, provenance: Dict[str, JsonValue], extra: Optional[Dict[str, JsonValue]] = None) -> Dict[str, JsonValue]:
    payload = {"id": "edge:{}".format(_hash("{}:{}:{}".format(source, predicate, target))), "source": source, "predicate": predicate, "target": target, "provenance": provenance}
    if extra is not None:
        payload.update(extra)
    return payload


def _key_json(key: str, value: JsonValue, confidence: float, ontology_property: str, reason: str, sources: List[JsonValue]) -> Dict[str, JsonValue]:
    return {"key": key, "value": value, "confidence": confidence, "ontology_property": ontology_property, "merge_reason": reason, "derivation_reason": reason, "source_fact_refs": sources}


def _document_provenance(document: SourceDocument) -> Dict[str, JsonValue]:
    return {"document_id": document.manifest.document_id, "source_ref": "fixture:{}".format(document.manifest.source_fixture_path), "chunk_id": "manifest", "line_start": 0, "line_end": 0, "confidence": document.confidence, "extractor_version": EXTRACTOR_VERSION, "source_module": "trustgraph_legal.case_graph"}


def _field_provenance(field: ExtractedField) -> Dict[str, JsonValue]:
    return {"document_id": field.document_id, "source_ref": field.source_ref, "chunk_id": field.chunk_id, "line_start": field.line_start, "line_end": field.line_end, "confidence": field.confidence, "extractor_version": FIELD_EXTRACTOR_VERSION, "source_module": "trustgraph_legal.fields", "field_name": field.name}


def _field_id(prefix: str, field: ExtractedField) -> str:
    return "{}:{}".format(prefix, _hash("{}:{}:{}:{}".format(field.document_id, field.name, field.chunk_id, field.normalized_value)))


def _field_values(fields: Tuple[ExtractedField, ...], names: set[str]) -> Tuple[str, ...]:
    return tuple(sorted({field.normalized_value for field in fields if field.name in names}))


def _field_refs(fields: Tuple[ExtractedField, ...], names: set[str]) -> List[JsonValue]:
    return [_field_id("field", field) for field in fields if field.name in names]


def _derived_key(prefix: str, material: Tuple[str, ...], reason: str) -> Tuple[str, Dict[str, JsonValue]]:
    value = "{}-{}".format(prefix.replace("_", "-"), _hash("|".join(sorted(material)))[:20])
    return value, {"reason": reason, "inputs": list(material)}


def _identity_by_value(fields: Tuple[ExtractedField, ...], identity_keys: Tuple[str, ...]) -> Dict[str, str]:
    if not identity_keys:
        return {}
    subjects = _field_values(fields, {"identity_subject_role"})
    return {subject: identity_keys[0] for subject in subjects}


def _first_provenance(fields: Tuple[ExtractedField, ...], names: set[str]) -> Dict[str, JsonValue]:
    for field in fields:
        if field.name in names:
            return _field_provenance(field)
    return {"document_id": "missing", "source_ref": "missing", "chunk_id": "missing", "line_start": 0, "line_end": 0, "confidence": 0.0, "extractor_version": EXTRACTOR_VERSION, "source_module": "trustgraph_legal.case_graph"}


def _identity_decisions(findings: List[Dict[str, JsonValue]]) -> List[Dict[str, JsonValue]]:
    return [{"reason": finding["reason"], "severity": finding["severity"], "candidates": finding.get("candidates", [])} for finding in findings if finding["reason"] in {"identity_uncertain", "name_only_without_identity_evidence"}]


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
