from __future__ import annotations

from typing import Final


ACTION_PACKET_SCHEMA_VERSION: Final = "trustgraph-action-packets/v1"
ACTION_PACKET_VERSION: Final = "recova-debt-collection-action-packets@v1.0.0"
DECISION_TABLE_VERSION: Final = "recova-debt-collection-route-decisions@v1.0.0"
NON_EXECUTION_SEMANTICS: Final = "advisory_only_human_review_required"
EXECUTION_SEMANTICS: Final = "schema_only_advisory_packet_preparation"
REVIEW_STATUS: Final = "human_review_required"
REQUIRED_PACKET_TYPES: Final = frozenset(
    {
        "evidence_request",
        "legal_action_review",
        "finance_review",
        "contact_review",
        "monitoring_retry",
        "insolvency_recovery_review",
    }
)
FORBIDDEN_FIELDS: Final = frozenset(
    {
        "filing_destination",
        "filing_destination_court",
        "court_filing_endpoint",
        "submission_endpoint",
        "debtor_contact_payload",
        "debtor_contact_channel",
        "debtor_phone",
        "debtor_email",
        "payment_request_payload",
        "executable_instruction",
        "collection_execution_command",
    }
)
GENERIC_INPUTS: Final = frozenset(
    {
        "case_packet_ref",
        "claim_ref",
        "route_id",
        "reviewer_role",
        "request_reason_code",
        "source_refs",
        "missing_fact_handles",
        "legal_source_review_status",
    }
)
REQUIRED_ROOT_TEXT_FIELDS: Final = (
    "schema_version",
    "action_packet_version",
    "decision_table_version",
    "route_source_version",
    "domain_source_version",
    "workflow_version",
    "finance_model_version",
    "evaluation_date",
    "review_status",
    "execution_semantics",
    "non_execution_semantics",
)
REQUIRED_PACKET_TEXT_FIELDS: Final = (
    "packet_type",
    "label",
    "purpose",
    "packet_lifecycle",
    "review_status",
    "non_execution_semantics",
)
REQUIRED_PACKET_LIST_FIELDS: Final = (
    "required_inputs",
    "source_refs",
    "review_requirements",
    "allowed_output_fields",
    "forbidden_fields",
    "permitted_next_states",
)
PII_FALSE_FIELDS: Final = (
    "raw_text_included",
    "source_text_included",
    "debtor_contact_payload_included",
    "filing_destination_included",
)
