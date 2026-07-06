from __future__ import annotations

import json
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Sequence, TypeAlias


JsonScalar: TypeAlias = None | bool | int | float | str
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]

ONTOLOGY_KEY: Final = "recova-debt-collection-v1"
REQUIRED_SECTIONS: Final = ("metadata", "classes", "objectProperties", "datatypeProperties")
REQUIRED_METADATA: Final = ("name", "version", "namespace", "root", "evaluation_date", "non_execution_semantics")
REQUIRED_ROOT_LABEL: Final = "Claim/Receivable"
XSD_RANGE_PREFIX: Final = "xsd:"
KEBAB_CASE: Final = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
DATE_ONLY: Final = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


@dataclass(frozen=True)
class OntologyIssue:
    location: str
    message: str

    def format(self) -> str:
        return f"{self.location}: {self.message}"


RequiredEdge: TypeAlias = tuple[str, str]
OntologySummary: TypeAlias = tuple[int, int, int, int]
ROOT_CLASSES: Final[dict[str, str]] = {"claim": "Claim", "receivable": "Receivable"}
REQUIRED_CLASSES: Final = (
    "claim", "receivable", "debtor-identity", "creditor-party", "assignee-party", "guarantee-surety",
    "case-packet", "document-assembly", "enforcement-title", "service-proof", "finality-proof",
    "execution-clause", "limitation-review", "ledger-fact", "asset-hint", "route-candidate",
    "workflow-state", "stopgate", "action-packet", "governance-record", "debtor-context-graph-handle",
    "fact-handle",
)
REQUIRED_EDGES: Final[dict[str, RequiredEdge]] = {
    "claim-has-debtor-identity": ("claim", "debtor-identity"),
    "claim-has-creditor": ("claim", "creditor-party"),
    "claim-has-assignee": ("claim", "assignee-party"),
    "claim-has-guarantee-surety": ("claim", "guarantee-surety"),
    "claim-has-case-packet": ("claim", "case-packet"),
    "claim-has-document-assembly": ("claim", "document-assembly"),
    "claim-has-enforcement-title": ("claim", "enforcement-title"),
    "claim-has-service-proof": ("claim", "service-proof"),
    "claim-has-finality-proof": ("claim", "finality-proof"),
    "claim-has-execution-clause": ("claim", "execution-clause"),
    "claim-has-limitation-review": ("claim", "limitation-review"),
    "claim-has-ledger-fact": ("claim", "ledger-fact"),
    "claim-has-asset-hint": ("claim", "asset-hint"),
    "claim-has-route-candidate": ("claim", "route-candidate"),
    "claim-has-workflow-state": ("claim", "workflow-state"),
    "claim-has-stopgate": ("claim", "stopgate"),
    "claim-has-action-packet": ("claim", "action-packet"),
    "claim-has-governance-record": ("claim", "governance-record"),
    "claim-maps-from-debtor-context-graph": ("claim", "debtor-context-graph-handle"),
    "debtor-graph-has-fact-handle": ("debtor-context-graph-handle", "fact-handle"),
}
REQUIRED_DATATYPE_PROPERTIES: Final = (
    "claim-domain-id", "receivable-id", "evaluation-date", "graph-snapshot-id", "source-ref",
    "review-status", "non-execution-status", "workflow-state-id", "route-status", "stopgate-decision",
    "balance-review-status",
)


def load_json(path: Path) -> JsonObject:
    with path.open(encoding="utf-8") as handle:
        raw = json.load(handle)

    if not isinstance(raw, dict):
        raise TypeError("ontology root must be a JSON object")
    return raw


def text_value(entry: JsonObject, field: str) -> str:
    value = entry.get(field)
    if isinstance(value, str):
        return value
    return ""


def object_value(entry: JsonObject, field: str) -> JsonObject | None:
    value = entry.get(field)
    if isinstance(value, dict):
        return value
    return None


def label_values(entry: JsonObject) -> set[str]:
    raw_labels = entry.get("rdfs:label")
    if not isinstance(raw_labels, list):
        return set()
    return {value for raw_label in raw_labels if isinstance(raw_label, dict) for value in [raw_label.get("value")] if isinstance(value, str)}


def validate_identifier(identifier: str, location: str) -> list[OntologyIssue]:
    if KEBAB_CASE.fullmatch(identifier):
        return []
    return [OntologyIssue(location=location, message=f"{identifier} must be kebab-case")]


def validate_object_section(parent: JsonObject, section: str, location: str) -> tuple[JsonObject, list[OntologyIssue]]:
    value = object_value(parent, section)
    if value is None:
        return {}, [OntologyIssue(location=location, message=f"{section} must be an object")]
    return value, []


def validate_metadata(ontology: JsonObject) -> list[OntologyIssue]:
    metadata, issues = validate_object_section(ontology, "metadata", f"{ONTOLOGY_KEY}.metadata")
    for field in REQUIRED_METADATA:
        if not text_value(metadata, field):
            issues.append(OntologyIssue(location=f"{ONTOLOGY_KEY}.metadata", message=f"missing {field}"))
    if text_value(metadata, "root") != REQUIRED_ROOT_LABEL:
        issues.append(OntologyIssue(location=f"{ONTOLOGY_KEY}.metadata.root", message="root must be Claim/Receivable"))
    evaluation_date = text_value(metadata, "evaluation_date")
    if evaluation_date and DATE_ONLY.fullmatch(evaluation_date) is None:
        issues.append(OntologyIssue(location=f"{ONTOLOGY_KEY}.metadata.evaluation_date", message="evaluation_date must use YYYY-MM-DD"))
    if text_value(metadata, "non_execution_semantics") != "descriptive_only":
        issues.append(OntologyIssue(location=f"{ONTOLOGY_KEY}.metadata.non_execution_semantics", message="non_execution_semantics must be descriptive_only"))
    return issues


def validate_required_classes(classes: JsonObject) -> list[OntologyIssue]:
    issues: list[OntologyIssue] = []
    for class_id in REQUIRED_CLASSES:
        if class_id not in classes:
            issues.append(OntologyIssue(location=f"{ONTOLOGY_KEY}.classes", message=f"missing required class {class_id}"))
    for class_id, label in ROOT_CLASSES.items():
        raw_class = classes.get(class_id)
        if not isinstance(raw_class, dict):
            issues.append(OntologyIssue(location=f"{ONTOLOGY_KEY}.classes.{class_id}", message=f"missing required root class {class_id} ({label})"))
            continue
        if label not in label_values(raw_class):
            issues.append(OntologyIssue(location=f"{ONTOLOGY_KEY}.classes.{class_id}", message=f"required root class {class_id} must label {label}"))
    return issues


def validate_ids(identifiers: Iterable[str], section: str) -> list[OntologyIssue]:
    issues: list[OntologyIssue] = []
    for identifier in identifiers:
        issues.extend(validate_identifier(identifier, f"{ONTOLOGY_KEY}.{section}.{identifier}"))
    return issues


def validate_object_properties(classes: JsonObject, properties: JsonObject) -> list[OntologyIssue]:
    issues: list[OntologyIssue] = []
    for property_id, raw_property in properties.items():
        location = f"{ONTOLOGY_KEY}.objectProperties.{property_id}"
        if not isinstance(raw_property, dict):
            issues.append(OntologyIssue(location=location, message="property must be an object"))
            continue
        domain = text_value(raw_property, "rdfs:domain")
        range_id = text_value(raw_property, "rdfs:range")
        if not domain:
            issues.append(OntologyIssue(location=location, message="missing domain"))
        elif domain not in classes:
            issues.append(OntologyIssue(location=location, message=f"unknown domain {domain}"))
        if not range_id:
            issues.append(OntologyIssue(location=location, message="missing range"))
        elif range_id not in classes:
            issues.append(OntologyIssue(location=location, message=f"unknown range {range_id}"))
    for edge_id, requirement in REQUIRED_EDGES.items():
        raw_property = properties.get(edge_id)
        location = f"{ONTOLOGY_KEY}.objectProperties.{edge_id}"
        if not isinstance(raw_property, dict):
            issues.append(OntologyIssue(location=location, message=f"missing required edge {edge_id}"))
            continue
        domain, range_id = requirement
        if text_value(raw_property, "rdfs:domain") != domain:
            issues.append(OntologyIssue(location=location, message=f"required edge domain must be {domain}"))
        if text_value(raw_property, "rdfs:range") != range_id:
            issues.append(OntologyIssue(location=location, message=f"required edge range must be {range_id}"))
    return issues


def validate_datatype_properties(classes: JsonObject, properties: JsonObject) -> list[OntologyIssue]:
    issues: list[OntologyIssue] = []
    for property_id, raw_property in properties.items():
        location = f"{ONTOLOGY_KEY}.datatypeProperties.{property_id}"
        if not isinstance(raw_property, dict):
            issues.append(OntologyIssue(location=location, message="property must be an object"))
            continue
        domain = text_value(raw_property, "rdfs:domain")
        range_id = text_value(raw_property, "rdfs:range")
        if not domain:
            issues.append(OntologyIssue(location=location, message="missing domain"))
        elif domain not in classes:
            issues.append(OntologyIssue(location=location, message=f"unknown domain {domain}"))
        if not range_id:
            issues.append(OntologyIssue(location=location, message="missing range"))
        elif not range_id.startswith(XSD_RANGE_PREFIX):
            issues.append(OntologyIssue(location=location, message=f"datatype range must use {XSD_RANGE_PREFIX}"))
    for property_id in REQUIRED_DATATYPE_PROPERTIES:
        if property_id not in properties:
            issues.append(OntologyIssue(location=f"{ONTOLOGY_KEY}.datatypeProperties.{property_id}", message=f"missing required datatype property {property_id}"))
    return issues


def validate_ontology(root: JsonObject) -> tuple[OntologySummary | None, list[OntologyIssue]]:
    raw_ontology = root.get(ONTOLOGY_KEY)
    if not isinstance(raw_ontology, dict):
        return None, [OntologyIssue(location="ontology", message=f"missing {ONTOLOGY_KEY}")]
    issues: list[OntologyIssue] = []
    for section in REQUIRED_SECTIONS:
        if section not in raw_ontology:
            issues.append(OntologyIssue(location=ONTOLOGY_KEY, message=f"missing {section}"))
    issues.extend(validate_metadata(raw_ontology))
    classes, class_section_issues = validate_object_section(raw_ontology, "classes", f"{ONTOLOGY_KEY}.classes")
    object_properties, object_section_issues = validate_object_section(raw_ontology, "objectProperties", f"{ONTOLOGY_KEY}.objectProperties")
    datatype_properties, datatype_section_issues = validate_object_section(raw_ontology, "datatypeProperties", f"{ONTOLOGY_KEY}.datatypeProperties")
    issues.extend(class_section_issues)
    issues.extend(object_section_issues)
    issues.extend(datatype_section_issues)
    issues.extend(validate_ids(classes, "classes"))
    issues.extend(validate_required_classes(classes))
    issues.extend(validate_ids(object_properties, "objectProperties"))
    issues.extend(validate_ids(datatype_properties, "datatypeProperties"))
    issues.extend(validate_object_properties(classes, object_properties))
    issues.extend(validate_datatype_properties(classes, datatype_properties))
    return (len(classes), len(object_properties), len(datatype_properties), len(REQUIRED_EDGES)), issues


def main(argv: Sequence[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_domain_ontology_v1.py <ontology.json>", file=sys.stderr)
        return 2
    ontology_path = Path(argv[1])
    try:
        summary, issues = validate_ontology(load_json(ontology_path))
    except json.JSONDecodeError as error:
        print(f"ERROR {ontology_path}: invalid JSON: {error}", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"ERROR {ontology_path}: {error}", file=sys.stderr)
        return 1
    except TypeError as error:
        print(f"ERROR {ontology_path}: {error}", file=sys.stderr)
        return 1
    if issues:
        for issue in issues:
            print(f"ERROR {issue.format()}", file=sys.stderr)
        return 1
    if summary is None:
        print(f"ERROR ontology: missing {ONTOLOGY_KEY}", file=sys.stderr)
        return 1
    class_count, object_property_count, datatype_property_count, required_edge_count = summary
    print(f"PASS ontology {ONTOLOGY_KEY} root=Claim/Receivable classes={class_count} objectProperties={object_property_count} datatypeProperties={datatype_property_count} requiredEdges={required_edge_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
