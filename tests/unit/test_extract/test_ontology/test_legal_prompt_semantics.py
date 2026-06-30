import json
from pathlib import Path

import ibis

from trustgraph.extract.kg.ontology.ontology_loader import OntologyLoader
from trustgraph.extract.kg.ontology.ontology_selector import OntologySubset
from trustgraph.extract.kg.ontology.simplified_parser import parse_extraction_response
from trustgraph.extract.kg.ontology.triple_converter import TripleConverter
from trustgraph.schema.core.primitives import IRI


REPO_ROOT = Path(__file__).resolve().parents[4]
PROMPT_PATH = REPO_ROOT / "ontology-prompt.md"
ONTOLOGY_PATH = REPO_ROOT / "resources/ontologies/recova-debt-collection.json"
LEGAL_IRI_BASE = "https://recova.ai/ontologies/debt-collection#"


def _recova_subset() -> OntologySubset:
    config = json.loads(ONTOLOGY_PATH.read_text())
    ontology_config = config["recova-debt-collection"]
    loader = OntologyLoader()
    loader.update_ontologies({"recova-debt-collection": ontology_config})
    ontology = loader.get_ontology("recova-debt-collection")
    assert ontology is not None

    class_ids = ["case-packet", "legal-document", "source-span", "claim"]
    object_property_ids = ["has-document", "has-source-span", "has-claim"]
    datatype_property_ids = [
        "case-packet-id",
        "document-id",
        "source-ref",
        "claim-id",
        "prompt-version",
    ]

    return OntologySubset(
        ontology_id="recova-debt-collection",
        classes={class_id: ontology.classes[class_id].__dict__ for class_id in class_ids},
        object_properties={
            prop_id: ontology.object_properties[prop_id].__dict__
            for prop_id in object_property_ids
        },
        datatype_properties={
            prop_id: ontology.datatype_properties[prop_id].__dict__
            for prop_id in datatype_property_ids
        },
        metadata=ontology.metadata,
    )


def _render_ontology_prompt(subset: OntologySubset) -> str:
    template = ibis.Template(PROMPT_PATH.read_text())
    return template.render(
        {
            "text": "A redacted payment order mentions a claim and its source chunk.",
            "classes": subset.classes,
            "object_properties": subset.object_properties,
            "datatype_properties": subset.datatype_properties,
        }
    )


def _legal_objects():
    source_fields = {
        "document_id": "DOC-EXAMPLE-001",
        "chunk_id": "chunk-7",
        "source_refs": ["DOC-EXAMPLE-001#chunk-7"],
    }
    return [
        {
            "type": "entity",
            "entity": "case-packet example 001",
            "entity_type": "case-packet",
            **source_fields,
        },
        {
            "type": "entity",
            "entity": "payment order document 001",
            "entity_type": "legal-document",
            **source_fields,
        },
        {
            "type": "entity",
            "entity": "payment order span chunk 7",
            "entity_type": "source-span",
            **source_fields,
        },
        {
            "type": "relationship",
            "subject": "case-packet example 001",
            "subject_type": "case-packet",
            "relation": "has-document",
            "object": "payment order document 001",
            "object_type": "legal-document",
            **source_fields,
        },
        {
            "type": "relationship",
            "subject": "payment order document 001",
            "subject_type": "legal-document",
            "relation": "has-source-span",
            "object": "payment order span chunk 7",
            "object_type": "source-span",
            **source_fields,
        },
        {
            "type": "attribute",
            "entity": "payment order span chunk 7",
            "entity_type": "source-span",
            "attribute": "source-ref",
            "value": "DOC-EXAMPLE-001#chunk-7",
            **source_fields,
        },
    ]


class TestLegalPromptSemantics:
    def test_rendered_prompt_uses_simplified_legal_ids_and_source_evidence(self):
        subset = _recova_subset()

        rendered = _render_ontology_prompt(subset)

        for configured_id in [
            "case-packet",
            "legal-document",
            "source-span",
            "has-document",
            "has-source-span",
            "source-ref",
        ]:
            assert configured_id in rendered
        for source_field in ["document_id", "chunk_id", "source_refs"]:
            assert source_field in rendered
        for runtime_field in ["entity_type", "relation", "attribute"]:
            assert runtime_field in rendered
        assert "labels for explanation only" in rendered
        assert "Do not output labels as identifiers" in rendered
        assert "Recipe" not in rendered
        assert "Ingredient" not in rendered
        assert "has_ingredient" not in rendered
        assert '"predicate"' not in rendered

    def test_simplified_parser_and_converter_emit_recova_uri_triples(self):
        subset = _recova_subset()
        converter = TripleConverter(subset, "recova-debt-collection")

        parsed = parse_extraction_response(_legal_objects())
        assert parsed is not None
        triples = converter.convert_all(parsed)

        predicate_iris = {triple.p.iri for triple in triples if triple.p.type == IRI}
        object_iris = {triple.o.iri for triple in triples if triple.o.type == IRI}
        assert f"{LEGAL_IRI_BASE}has-document" in predicate_iris
        assert f"{LEGAL_IRI_BASE}has-source-span" in predicate_iris
        assert f"{LEGAL_IRI_BASE}source-ref" in predicate_iris
        assert f"{LEGAL_IRI_BASE}case-packet" in object_iris
        assert f"{LEGAL_IRI_BASE}legal-document" in object_iris
        assert f"{LEGAL_IRI_BASE}source-span" in object_iris

    def test_converter_rejects_unconfigured_legal_values(self):
        subset = _recova_subset()
        converter = TripleConverter(subset, "recova-debt-collection")

        valid = parse_extraction_response(_legal_objects())
        invalid = parse_extraction_response(
            [
                {"type": "entity", "entity": "label-shaped type", "entity_type": "Case packet"},
                {
                    "type": "relationship",
                    "subject": "case packet",
                    "subject_type": "case-packet",
                    "relation": "has_ingredient",
                    "object": "legal document",
                    "object_type": "legal-document",
                },
                {
                    "type": "relationship",
                    "subject": "claim",
                    "subject_type": "claim",
                    "relation": "has-document",
                    "object": "legal document",
                    "object_type": "legal-document",
                },
                {
                    "type": "attribute",
                    "entity": "source span",
                    "entity_type": "source-span",
                    "attribute": "sourceReference",
                    "value": "DOC-001",
                },
            ]
        )
        assert valid is not None
        assert invalid is not None

        valid_triples = converter.convert_all(valid)
        invalid_triples = converter.convert_all(invalid)

        assert valid_triples
        assert invalid_triples == []
