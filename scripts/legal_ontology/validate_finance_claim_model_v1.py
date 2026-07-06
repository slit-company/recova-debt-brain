#!/usr/bin/env python3
from __future__ import annotations

import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Final

from pydantic import BaseModel, ConfigDict, ValidationError

SCHEMA_VERSION: Final = "trustgraph-claim-finance-model/v1"
REQUIRED_COMPONENTS: Final = (
    "principal",
    "interest",
    "late_damages",
    "enforcement_costs",
    "payments",
    "payment_allocation",
    "remaining_balance",
    "assignment_succession",
    "guarantee_surety",
    "reimbursement_subrogation_candidate",
    "disputed_amount",
)
REQUIRED_REVIEW_TRIGGERS: Final = (
    "missing_source_ref",
    "incomplete_rate_period",
    "statutory_or_complex_interest",
    "payment_allocation_conflict",
    "disputed_amount",
    "authoritative_balance_forbidden",
)


class FinanceComponentSpec(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="allow")

    component_id: str


class FinanceAllocationRuleSpec(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="allow")

    rule_id: str
    component_order: tuple[str, ...]
    deterministic_only: bool


class FinanceReviewTriggerSpec(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="allow")

    code: str


class FinanceModelResource(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="allow")

    schema_version: str
    model_version: str
    evaluation_date: str
    non_execution_semantics: str
    authoritative_balance: bool
    component_types: tuple[FinanceComponentSpec, ...]
    allocation_rules: tuple[FinanceAllocationRuleSpec, ...]
    review_triggers: tuple[FinanceReviewTriggerSpec, ...]


@dataclass(frozen=True, slots=True)
class FinanceModelIssue:
    location: str
    message: str

    def format(self) -> str:
        return f"{self.location}: {self.message}"


@dataclass(frozen=True, slots=True)
class FinanceModelSummary:
    component_count: int
    allocation_rule_count: int
    review_trigger_count: int


def load_finance_model(path: Path) -> FinanceModelResource:
    return FinanceModelResource.model_validate_json(path.read_text(encoding="utf-8"))


def validate_finance_model(root: FinanceModelResource) -> tuple[FinanceModelSummary, list[FinanceModelIssue]]:
    issues: list[FinanceModelIssue] = []
    if root.schema_version != SCHEMA_VERSION:
        issues.append(FinanceModelIssue(location="finance_model.schema_version", message=f"must be {SCHEMA_VERSION}"))
    if root.non_execution_semantics != "deterministic_fixture_only_not_authoritative_ledger":
        issues.append(FinanceModelIssue(location="finance_model.non_execution_semantics", message="unexpected finance boundary"))
    if root.authoritative_balance is not False:
        issues.append(FinanceModelIssue(location="finance_model.authoritative_balance", message="authoritative_balance must be false"))

    component_ids = {component.component_id for component in root.component_types}
    for component_id in REQUIRED_COMPONENTS:
        if component_id not in component_ids:
            issues.append(FinanceModelIssue(location="finance_model.component_types", message=f"missing component {component_id}"))
    issues.extend(_validate_allocation_rules(root.allocation_rules, component_ids))

    trigger_codes = {trigger.code for trigger in root.review_triggers}
    for trigger_code in REQUIRED_REVIEW_TRIGGERS:
        if trigger_code not in trigger_codes:
            issues.append(FinanceModelIssue(location="finance_model.review_triggers", message=f"missing review trigger {trigger_code}"))
    return FinanceModelSummary(len(root.component_types), len(root.allocation_rules), len(root.review_triggers)), issues


def _validate_allocation_rules(allocation_rules: Sequence[FinanceAllocationRuleSpec], component_ids: set[str]) -> list[FinanceModelIssue]:
    issues: list[FinanceModelIssue] = []
    if not allocation_rules:
        issues.append(FinanceModelIssue(location="finance_model.allocation_rules", message="at least one allocation rule is required"))
    for index, rule in enumerate(allocation_rules):
        location = f"finance_model.allocation_rules[{index}]"
        if not rule.rule_id:
            issues.append(FinanceModelIssue(location=location, message="missing rule_id"))
        if rule.deterministic_only is not True:
            issues.append(FinanceModelIssue(location=location, message="deterministic_only must be true"))
        if not rule.component_order:
            issues.append(FinanceModelIssue(location=location, message="component_order must not be empty"))
        for component_id in rule.component_order:
            if component_id not in component_ids:
                issues.append(FinanceModelIssue(location=location, message=f"unknown component {component_id}"))
    return issues


def main(argv: Sequence[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_finance_claim_model_v1.py <finance-model.json>", file=sys.stderr)
        return 2
    try:
        summary, issues = validate_finance_model(load_finance_model(Path(argv[1])))
    except OSError as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 1
    except ValidationError as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 1
    if issues:
        for issue in issues:
            print(f"ERROR {issue.format()}", file=sys.stderr)
        return 1
    message = (
        f"PASS finance_claim_model components={summary.component_count} "
        f"allocation_rules={summary.allocation_rule_count} "
        f"review_triggers={summary.review_trigger_count}"
    )
    print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
