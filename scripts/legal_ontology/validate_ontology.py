#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Sequence, TypeAlias


JsonScalar: TypeAlias = None | bool | int | float | str
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]

ONTOLOGY_KEY: Final = "recova-debt-collection"
REQUIRED_SECTIONS: Final = ("metadata", "classes", "objectProperties", "datatypeProperties")
REQUIRED_METADATA: Final = ("name", "version", "namespace")
KEBAB_CASE: Final = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
XSD_RANGE_PREFIX: Final = "xsd:"


@dataclass(frozen=True)
class OntologyIssue:
    location: str
    message: str

    def format(self) -> str:
        return f"{self.location}: {self.message}"


@dataclass(frozen=True)
class OntologySummary:
    ontology_id: str
    class_count: int
    object_property_count: int
    datatype_property_count: int


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
    return issues


def validate_class_ids(classes: JsonObject) -> list[OntologyIssue]:
    issues: list[OntologyIssue] = []
    for class_id in classes:
        issues.extend(validate_identifier(class_id, f"{ONTOLOGY_KEY}.classes.{class_id}"))
    return issues


def validate_property_ids(properties: JsonObject, section: str) -> list[OntologyIssue]:
    issues: list[OntologyIssue] = []
    for property_id in properties:
        issues.extend(validate_identifier(property_id, f"{ONTOLOGY_KEY}.{section}.{property_id}"))
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
    object_properties, object_section_issues = validate_object_section(
        raw_ontology,
        "objectProperties",
        f"{ONTOLOGY_KEY}.objectProperties",
    )
    datatype_properties, datatype_section_issues = validate_object_section(
        raw_ontology,
        "datatypeProperties",
        f"{ONTOLOGY_KEY}.datatypeProperties",
    )
    issues.extend(class_section_issues)
    issues.extend(object_section_issues)
    issues.extend(datatype_section_issues)
    issues.extend(validate_class_ids(classes))
    issues.extend(validate_property_ids(object_properties, "objectProperties"))
    issues.extend(validate_property_ids(datatype_properties, "datatypeProperties"))
    issues.extend(validate_object_properties(classes, object_properties))
    issues.extend(validate_datatype_properties(classes, datatype_properties))

    summary = OntologySummary(
        ontology_id=ONTOLOGY_KEY,
        class_count=len(classes),
        object_property_count=len(object_properties),
        datatype_property_count=len(datatype_properties),
    )
    return summary, issues


def main(argv: Sequence[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_ontology.py <ontology.json>", file=sys.stderr)
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

    print(
        "PASS ontology "
        f"{summary.ontology_id} "
        f"classes={summary.class_count} "
        f"objectProperties={summary.object_property_count} "
        f"datatypeProperties={summary.datatype_property_count}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
