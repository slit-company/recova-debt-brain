from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Final, TypeAlias

from pydantic import JsonValue as PydanticJsonValue
from pydantic import TypeAdapter

from trustgraph_legal.debtor_context import build_debtor_context
from trustgraph_legal.debtor_governance import build_debtor_governance_payload
from trustgraph_legal.document_assembly import build_document_assembly
from trustgraph_legal.domain_graph_adapter import adapt_debtor_graph_to_claim_domain
from trustgraph_legal.finance_claims import (
    ClaimFinanceFixture,
    FinanceRelationship,
    MoneyComponent,
    Payment,
    PaymentAllocationRule,
    RatePeriod,
    calculate_claim_finance_fixture,
)
from trustgraph_legal.route_candidates import evaluate_route_candidates

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
FIXTURE_ROOT: Final = REPO_ROOT / "tests" / "fixtures" / "claim-domain-v1"
SCENARIO_BUNDLE: Final = FIXTURE_ROOT / "synthetic_claim_states.json"
MANUAL_FIXTURE: Final = FIXTURE_ROOT / "minimized_manual_v2_scenarios.md"
PAGES_FIXTURE: Final = REPO_ROOT / "tests" / "fixtures" / "legal-ocr-pages"
DOMAIN_SOURCES_PATH: Final = REPO_ROOT / "resources" / "legal_rules" / "debt_collection_domain_sources_v1.json"
ROUTES_PATH: Final = REPO_ROOT / "resources" / "legal_routes" / "debt_collection_routes_v1.json"
WORKFLOW_PATH: Final = REPO_ROOT / "resources" / "workflows" / "debt_collection_workflow_v1.json"
DECISIONS_PATH: Final = REPO_ROOT / "resources" / "decision_tables" / "debt_collection_route_decisions_v1.json"
ACTION_PACKETS_PATH: Final = REPO_ROOT / "resources" / "action_packets" / "debt_collection_action_packets_v1.json"
FINANCE_PATH: Final = REPO_ROOT / "resources" / "finance" / "claim_finance_model_v1.json"
ONTOLOGY_PATH: Final = REPO_ROOT / "resources" / "ontologies" / "recova-debt-collection-v1.json"
V0_ROUTES_PATH: Final = REPO_ROOT / "resources" / "legal_routes" / "debt_collection_routes_v0.json"
V0_STOPGATE_PATH: Final = REPO_ROOT / "resources" / "legal_rules" / "debt_collection_stopgate_v0.json"
FORBIDDEN_KEYS: Final = frozenset({"raw_text", "source_text", "body", "excerpt", "source_path"})
FORBIDDEN_TEXT: Final = (
    "/" + "Users" + "/",
    "010-",
    "900101-",
    '"' + "debtor_contact_payload" + '":',
    '"' + "filing_destination" + '":',
)
JsonValue: TypeAlias = PydanticJsonValue
JsonObject: TypeAlias = dict[str, JsonValue]
JSON_OBJECT_ADAPTER: Final = TypeAdapter[JsonObject](JsonObject)


@dataclass(frozen=True, slots=True)
class Scenario:
    scenario_id: str
    route_id: str
    workflow_state: str
    fact_handles: tuple[str, ...]
    finance_review_codes: tuple[str, ...]
    legal_source_refs: tuple[str, ...]
    expected_status: str
    expected_packet_type: str
    expected_review_codes: tuple[str, ...]


def load_bundle() -> JsonObject:
    assert SCENARIO_BUNDLE.is_file(), "synthetic claim-domain scenario fixture is missing"
    return load_json_object(SCENARIO_BUNDLE)


def scenario_list(bundle: JsonObject) -> tuple[Scenario, ...]:
    return tuple(_scenario(entry) for entry in object_list(bundle["scenarios"]))


def run_manual_inventory(tmp_path: Path) -> JsonObject:
    output_path = tmp_path / "manual-inventory.json"
    result = _run(
        (
            str(REPO_ROOT / "scripts" / "legal_ontology" / "domain_manual_inventory.py"),
            "--manual",
            str(MANUAL_FIXTURE),
            "--out",
            str(output_path),
        ),
    )
    assert result.returncode == 0, result.stderr
    return load_json_object(output_path)


def run_resource_validators() -> tuple[str, ...]:
    commands = (
        (str(_validator("validate_domain_ontology_v1.py")), str(ONTOLOGY_PATH)),
        (str(_validator("validate_domain_sources_v1.py")), str(DOMAIN_SOURCES_PATH), str(V0_ROUTES_PATH), str(V0_STOPGATE_PATH)),
        (str(_validator("validate_finance_claim_model_v1.py")), str(FINANCE_PATH)),
        (str(_validator("validate_workflow_v1.py")), str(WORKFLOW_PATH), str(DOMAIN_SOURCES_PATH)),
        (str(_validator("validate_routes.py")), str(ROUTES_PATH), str(DOMAIN_SOURCES_PATH)),
        (str(_validator("validate_route_decisions_v1.py")), str(DECISIONS_PATH), str(ROUTES_PATH), str(DOMAIN_SOURCES_PATH), str(WORKFLOW_PATH), str(FINANCE_PATH)),
        (str(_validator("validate_action_packets_v1.py")), str(ACTION_PACKETS_PATH), str(DECISIONS_PATH), str(ROUTES_PATH), str(DOMAIN_SOURCES_PATH), str(WORKFLOW_PATH), str(FINANCE_PATH)),
    )
    outputs: list[str] = []
    for command in commands:
        result = _run(command)
        assert result.returncode == 0, result.stderr
        outputs.append(result.stdout.strip())
    return tuple(outputs)


def adapt_synthetic_debtor_graph() -> JsonObject:
    assembly = build_document_assembly(PAGES_FIXTURE, REPO_ROOT)
    base_graph = build_debtor_context(assembly, repo_root=REPO_ROOT)
    routes = evaluate_route_candidates(base_graph)
    graph = replace(
        base_graph,
        graph_snapshot=replace(base_graph.graph_snapshot, route_candidate_ids=tuple(route.route_id for route in routes)),
        route_candidates=routes,
    )
    governance = build_debtor_governance_payload(graph)
    return adapt_debtor_graph_to_claim_domain(graph, governance_records=governance.records).to_json()


def finance_review_codes() -> tuple[str, ...]:
    fixture = ClaimFinanceFixture(
        claim_id="claim:integration-finance",
        evaluation_date=date(2026, 7, 7),
        principal=MoneyComponent("principal", "principal", 1_000_000, ("fixture:finance#principal",)),
        interest=RatePeriod("interest", 1200, date(2026, 1, 1), date(2026, 1, 31), "explicit_contract_rate", ("fixture:finance#interest",)),
        late_damages=RatePeriod("late_damages", 300, date(2026, 1, 1), date(2026, 1, 31), "explicit_contract_rate", ("fixture:finance#late",)),
        enforcement_costs=(MoneyComponent("cost", "enforcement_costs", 10_000, ("fixture:finance#cost",)),),
        payments=(Payment("payment:001", 50_000, date(2026, 2, 1), ("fixture:finance#payment",)),),
        allocation_rule=PaymentAllocationRule(
            "allocation:fixture",
            ("enforcement_costs", "interest", "late_damages", "principal"),
            "explicit_fixture_rule",
            ("fixture:finance#allocation",),
        ),
        assignment_succession=FinanceRelationship("assignment_succession", "successor_claimant_reviewed", ("fixture:finance#assignment",)),
        guarantee_surety=FinanceRelationship("guarantee_surety", "surety_claim_preserved", ("fixture:finance#surety",)),
        reimbursement_subrogation_candidate=FinanceRelationship("reimbursement_subrogation_candidate", "candidate_preserved_for_review", ("fixture:finance#subrogation",)),
    )
    calculation = calculate_claim_finance_fixture(fixture.with_review_risks()).to_json()
    return tuple(str(item["code"]) for item in object_list(calculation["review_items"]))


def adapter_payload(scenario: Scenario) -> JsonObject:
    claim_ref = f"claim:{scenario.scenario_id}"
    return {
        "schema_version": "trustgraph-claim-domain-adapter/v1",
        "domain_ontology_version": "recova-debt-collection-v1@1.0.0",
        "claim_root": {"claim_id": claim_ref, "claim_ref": claim_ref, "source_refs": [f"fixture:{scenario.scenario_id}#claim"]},
        "fact_handles": [_fact_handle(scenario, fact, claim_ref) for fact in scenario.fact_handles],
        "route_candidates": [_route_candidate(scenario, claim_ref)],
        "source_refs": [f"fixture:{scenario.scenario_id}#claim", f"fixture:{scenario.scenario_id}#summary"],
        "legal_source_refs": list(scenario.legal_source_refs),
        "non_execution_semantics": "adapter_projection_only_human_review_required",
        "pii_profile": {"raw_text_included": False, "source_text_included": False},
    }


def assert_fixture_safe(bundle: JsonObject, source_ids: frozenset[str]) -> None:
    forbidden_key = _forbidden_key(bundle)
    assert forbidden_key is None, "forbidden fixture key {}".format(forbidden_key)
    encoded = json.dumps(bundle, ensure_ascii=False)
    for token in FORBIDDEN_TEXT:
        assert token not in encoded
    for scenario in scenario_list(bundle):
        unknown_sources = [source_ref for source_ref in scenario.legal_source_refs if source_ref not in source_ids]
        assert not unknown_sources, "unknown legal source {}".format(unknown_sources[0])


def domain_source_ids() -> frozenset[str]:
    root = load_json_object(DOMAIN_SOURCES_PATH)
    return frozenset(str(source["source_id"]) for source in object_list(root["sources"]))


def load_json_object(path: Path) -> JsonObject:
    return JSON_OBJECT_ADAPTER.validate_json(path.read_bytes())


def mcp_result(envelope: JsonObject) -> JsonObject:
    assert envelope["schema_version"] == "trustgraph-legal-mcp-tool-response/v1"
    assert envelope["group"] == "claim_domain"
    result = json_object(envelope["result"])
    assert_no_leakage(envelope)
    return result


def assert_no_leakage(payload: JsonObject) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    forbidden_key = _forbidden_key(payload)
    assert forbidden_key is None, "forbidden payload key {}".format(forbidden_key)
    for token in FORBIDDEN_TEXT:
        assert token not in encoded


def object_list(value: JsonValue) -> list[JsonObject]:
    assert isinstance(value, list)
    return [json_object(item) for item in value]


def json_object(value: JsonValue) -> JsonObject:
    assert isinstance(value, dict)
    return value


def int_value(value: JsonValue) -> int:
    assert isinstance(value, int)
    assert not isinstance(value, bool)
    return value


def only(values: list[JsonObject]) -> JsonObject:
    assert len(values) == 1
    return values[0]


def _scenario(entry: JsonObject) -> Scenario:
    return Scenario(
        scenario_id=_text(entry["scenario_id"]),
        route_id=_text(entry["route_id"]),
        workflow_state=_text(entry["workflow_state"]),
        fact_handles=_strings(entry["fact_handles"]),
        finance_review_codes=_strings(entry["finance_review_codes"]),
        legal_source_refs=_strings(entry["legal_source_refs"]),
        expected_status=_text(entry["expected_status"]),
        expected_packet_type=_text(entry["expected_packet_type"]),
        expected_review_codes=_strings(entry["expected_review_codes"]),
    )


def _fact_handle(scenario: Scenario, fact: str, claim_ref: str) -> JsonObject:
    return {
        "fact_id": f"fact:{scenario.scenario_id}:{fact}",
        "claim_id": claim_ref,
        "fact_handle": fact,
        "source_refs": [f"fixture:{scenario.scenario_id}#{fact}"],
    }


def _route_candidate(scenario: Scenario, claim_ref: str) -> JsonObject:
    return {
        "route_id": scenario.route_id,
        "domain_route_id": scenario.route_id,
        "claim_id": claim_ref,
        "domain_legal_source_refs": list(scenario.legal_source_refs),
        "direct_execution_allowed": False,
        "domain_review_status": "approved_static_v1",
    }


def _validator(filename: str) -> Path:
    return REPO_ROOT / "scripts" / "legal_ontology" / filename


def _run(args: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], cwd=REPO_ROOT, check=False, capture_output=True, text=True)


def _forbidden_key(value: JsonValue) -> str | None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in FORBIDDEN_KEYS:
                return key
            nested = _forbidden_key(item)
            if nested is not None:
                return nested
        return None
    if isinstance(value, list):
        for item in value:
            nested = _forbidden_key(item)
            if nested is not None:
                return nested
    return None


def _strings(value: JsonValue) -> tuple[str, ...]:
    assert isinstance(value, list)
    return tuple(item for item in value if isinstance(item, str))


def _text(value: JsonValue) -> str:
    assert isinstance(value, str)
    return value
