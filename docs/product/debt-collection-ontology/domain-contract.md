# Debt Collection Ontology Domain Contract

Status: v0 domain-brain contract
Ontology key: `recova-debt-collection`
Korean label: `채권추심 사건 온톨로지`

## Purpose

This contract defines the v0 legal-domain boundary for a Korean debt-collection
ontology running on TrustGraph. It is the contract for a domain brain server:
ontology, case graph, evidence, deterministic StopGates, governance queues, and
MCP-facing machine contracts.

It is intentionally:

- agent-agnostic: any MCP-capable client may use it.
- Hermes-agnostic: no Hermes-specific prompts, memory layout, or runtime behavior
  are part of this contract.
- user-UX-agnostic: review and governance states are service contracts, not a
  person-facing application design.
- non-executing: the server returns domain decisions and preconditions; it does
  not file, submit, contact, collect, pay, transfer, or otherwise perform
  business or legal execution.

## Source-Grounded Rationale

TrustGraph already provides the right substrate for this domain: workspaces,
collections, and flows isolate knowledge; ontology configuration can define
classes and object/datatype properties; extraction flows can preserve document
and chunk provenance; and the existing MCP surface already exposes document,
processing, graph, config, and query operations. The debt-collection layer should
therefore be a domain package and MCP wrapper over these primitives, not a
separate agent memory or UI workflow.

The OCR corpus evidence for planning shows recurring Korean legal packet themes:
attachment and collection orders, payment orders and judgments, service/finality
proof, execution clauses, assignment/succession, identity evidence, insolvency or
credit-recovery status, attachment targets, priority, asset evidence, ledgers,
and amount/interest calculations. v0 models these packet types and facts while
keeping source documents, extraction provenance, review state, and legal rule
versions explicit.

## Domain Scope

### In Scope

- Post-legal-action receivables and enforcement packets.
- OCR markdown or text extracted from legal packet documents.
- Document classification and case-level graph resolution.
- Party, claim, enforcement, asset, ledger, provenance, and legal-check facts.
- Deterministic StopGate evaluation using curated, versioned rule sources.
- MCP tool contracts for read, ingest, graph, StopGate, governance, and admin
  capabilities.
- Review queues for unknown, low-confidence, conflicting, or legally risky
  states.

### Out of Scope

- General legal research across all Korean law.
- Person-facing SaaS UX, workflow screens, or practitioner interface design.
- Client-agent planning, prompts, memory, or orchestration.
- Live law crawling or automatic production rule updates.
- Legal representation, legal advice finality, filing automation, debtor
  contact, payment collection, or irreversible execution.
- Storage or display of raw OCR sensitive identifiers in committed fixtures,
  logs, examples, reports, or contract docs.

## Canonical Identifiers

### `case_packet_id`

`case_packet_id` is the canonical internal case packet identifier. It is minted
by the domain brain when a document or packet cannot be safely attached to an
existing packet with enough evidence. It is not derived from a single party name,
court number, or document filename.

Required behavior:

- Every extracted case-level fact must link to one `case_packet_id`.
- Merge candidates must preserve all supporting evidence keys and confidence.
- Rejecting a merge must preserve the reason and competing evidence.
- A client may provide hints, but the server owns final packet resolution state.

### Hybrid Evidence Keys

The domain brain stores evidence keys as typed, redacted, provenance-linked
attributes:

| Key | Purpose | Merge Rule |
| --- | --- | --- |
| `court_case_number` | Court proceeding reference | Strong evidence only when court, proceeding type, and source document align. |
| `claim_id` | Internal or external claim reference | Strong evidence within the same creditor/source system; weak across systems. |
| `enforcement_title_id` | Judgment, payment order, settlement, or other title reference | Strong evidence when title type, date, court, and parties align. |
| `party_identity_key` | Redacted or hashed identity evidence for a party | Required for high-confidence party merge; name alone is insufficient. |
| `document_hash` | Content hash for source or redacted fixture document | Duplicate and lineage evidence; not enough by itself to merge cases. |

No merge may be based on a person's or organization's display name alone.

## Document Type Contract

Each source document receives one primary `document_type`, optional secondary
tags, confidence, evidence spans, and review state.

| Type ID | Description | Typical Facts |
| --- | --- | --- |
| `attachment-collection-application` | Application for attachment and collection order. | creditor, debtor, third-party debtor, claim, attachment target, requested amount |
| `attachment-collection-order` | Court order granting, denying, or modifying attachment/collection. | order status, target, served parties, amount, court, legal effect date |
| `payment-order` | Payment order or demand-like title document. | title, debtor, creditor, principal, interest, service/finality facts |
| `judgment-or-decision` | Judgment, decision, settlement, mediation, or equivalent title. | title type, court, parties, adjudicated amount, finality status |
| `service-finality-proof` | Proof of service, finality, certification, or execution clause. | service date, finality date, execution clause, served party |
| `assignment-succession` | Assignment, transfer, succession, merger, or substituted creditor proof. | assignor, assignee, succession basis, notice/consent evidence |
| `identity-evidence` | Party identity or registry evidence with sensitive fields redacted or hashed. | party identity key, organization registry key, relationship to case |
| `insolvency-credit-recovery` | Bankruptcy, discharge, rehabilitation, credit recovery, or workout materials. | proceeding status, discharge flag, protected period, source authority |
| `attachment-target-priority` | Target asset, third-party debtor, exemption, lien, priority, or competing claim material. | target type, priority, exemption, third-party debtor, risk flags |
| `asset-evidence` | Real property, vehicle, insurance, salary, deposit, receivable, or other asset evidence. | asset class, owner/holder, valuation, attachment feasibility |
| `ledger-recovery` | Collection ledger, payment history, cost, interest, or recovery status. | payments, balance, costs, interest base, calculation date |
| `amount-interest-calculation` | Standalone amount, interest, fee, or cost calculation. | principal, interest rate, period, costs, total, formula evidence |
| `legal-rule-source` | Curated legal rule, policy, statute excerpt, or internal compliance source. | rule id, source ref, effective date, version, review state |
| `unknown` | Document cannot be classified safely. | review item, candidate types, missing evidence |

Required metadata per document:

- `document_id`
- `case_packet_id` when resolved
- `document_type`
- `source_hash`
- `source_path_ref` or external source pointer
- `ocr_version`
- `extractor_version`
- `ontology_version`
- `prompt_version`
- `review_status`
- `confidence`
- `source_refs`
- `pii_profile`

## Entity Role Contract

Roles are graph roles attached to entities in a packet, not permanent labels on
the entity across all packets.

| Role ID | Meaning |
| --- | --- |
| `creditor` | Party asserting or owning the claim. |
| `debtor` | Party alleged or adjudicated to owe the claim. |
| `third-party-debtor` | Party owing or holding attachable assets for the debtor. |
| `guarantor` | Party with guarantee or surety exposure. |
| `assignor` | Prior claim holder transferring rights. |
| `assignee` | New claim holder receiving rights. |
| `successor` | Party succeeding to claim or obligation by merger, inheritance, subrogation, or other basis. |
| `court` | Court or adjudicating body. |
| `enforcement-agency` | Court office, enforcement officer, registry, or equivalent enforcement actor. |
| `asset-holder` | Bank, insurer, employer, registry, buyer, or other party holding target assets or debts. |
| `reviewer` | Service-side reviewer or approval actor represented only for governance state. |

Role assertions require:

- source document and span or derived-rule source
- confidence level
- effective packet context
- validity interval if known
- role-specific supporting evidence

## Fact Category Contract

All facts must be either extracted, derived, or reviewed.

| Category | Examples | Required Evidence |
| --- | --- | --- |
| `party-identity` | party type, role, redacted identity key, organization registry key | source span or reviewed key, confidence, PII handling record |
| `claim` | principal, interest base, claim basis, currency, costs | source span, amount normalization, calculation date |
| `assignment-succession` | chain of title, transfer date, notice, merger/succession basis | source span, source document type, rule relevance |
| `enforcement-title` | title type, court, title date, finality, execution clause | source span, title document, service/finality proof |
| `court-procedure` | case number, order status, service, appeal/finality, filing state | source span, court document, status date |
| `attachment-target` | asset/debt target, holder, amount cap, exemption candidate | source span, asset class, third-party debtor |
| `priority-exemption` | competing rights, prohibited target, protected amount, priority | source span or rule source, effective date |
| `insolvency-credit-recovery` | bankruptcy, discharge, rehabilitation, credit recovery, workout | source span, proceeding status, date |
| `ledger` | payments, recovery events, fees, balance, interest calculation | source span or ledger source, calculation version |
| `provenance` | source document, chunk, extractor, ontology, prompt, hash | system-generated pointer and versions |
| `legal-check` | StopGate finding, rule hit, missing evidence, decision | rule source, effective date, supporting facts |
| `governance` | review item, candidate ontology change, promotion/reprocess job | queue item, reason, reviewer/approval metadata |

Derived facts must cite every input fact and rule version used to derive them.

## Confidence Levels

Confidence is not a single floating-point field alone. Every assertion carries a
level, score when available, reason, and provenance.

| Level | Meaning | Use |
| --- | --- | --- |
| `verified` | Confirmed by reviewed source evidence or deterministic registry/hash match. | May support production graph and StopGate checks. |
| `high` | Strong evidence from authoritative legal document and consistent packet context. | May support recommendations, unless a StopGate demands review. |
| `medium` | Plausible extraction with source span but incomplete corroboration. | May be used for tentative graph context; risky actions remain blocked. |
| `low` | Weak OCR, ambiguous language, conflicting fields, or non-authoritative source. | Must enter review before legal-risk use. |
| `conflict` | Two or more incompatible facts exist. | Must block affected recommendations until resolved or scoped. |
| `unknown` | Evidence is missing or classification failed. | Must create a governance item when required for a decision. |

Legal-risk checks may never upgrade confidence by LLM assertion alone.

## StopGate Contract

StopGates are deterministic or reviewed legal/compliance blockers. They return
`가능`, `불가능`, or `보류`, never an execution result.

Each StopGate response includes:

- `decision`
- `recommended_action`
- `required_preconditions`
- `blocked_reasons`
- `missing_evidence`
- `risk_flags`
- `source_refs`
- `rule_refs`
- `confidence`
- `review_queue_items`

### StopGate Categories

| StopGate ID | Blocks or Holds When |
| --- | --- |
| `missing-enforcement-title` | No enforceable title or title type is unknown. |
| `service-finality-unproven` | Service, finality, or execution clause proof is absent or conflicting. |
| `assignment-chain-unproven` | Creditor succession or assignment chain is incomplete. |
| `party-identity-uncertain` | Party merge relies on name-only or weak identity evidence. |
| `amount-inconsistent` | Principal, interest, fees, payments, or totals conflict. |
| `limitation-risk` | limitation or stale-claim risk cannot be cleared from available evidence. |
| `insolvency-or-discharge-risk` | Insolvency, discharge, rehabilitation, or credit-recovery status may restrict collection. |
| `target-exemption-risk` | Target asset may be exempt, protected, or restricted. |
| `priority-conflict` | Competing liens, assignments, attachments, or priority claims exist. |
| `duplicate-enforcement-risk` | Same title/claim may already be enforced or collected elsewhere. |
| `privacy-purpose-risk` | Intended use lacks a permitted purpose or exceeds retention/access policy. |
| `source-provenance-missing` | A required fact lacks source document, chunk, or reviewed-rule provenance. |
| `low-confidence-critical-fact` | A legally material fact is below required confidence. |
| `rule-source-unapproved` | A rule is draft, stale, superseded, or not promoted for production use. |
| `unknown-document-type` | A required document cannot be classified safely. |

StopGate output is advisory domain reasoning. Client systems own approvals and
execution outside this server.

## PII Handling Rules

The domain brain handles sensitive data by minimization, redaction, hashing, and
strict separation between raw source storage and graph-facing output.

Required rules:

- Raw OCR sensitive fields must not appear in committed fixtures, examples,
  logs, reports, prompts, governance notes, or docs.
- Raw source documents may only be stored in approved runtime storage under
  workspace/collection access controls.
- Graph facts should store redacted display values and stable salted hashes for
  matching when exact values are not required for the user-facing answer.
- Identity evidence should use `party_identity_key` and `pii_profile`, not raw
  national ID, phone, account, or full-location strings.
- Source spans exposed through MCP must be redacted when they contain sensitive
  identifiers.
- Tool responses must default to redacted values and expose raw source fetches
  only through separately authorized admin paths, if such paths are implemented.
- Logs must record hashes, document ids, rule ids, and source refs, not raw OCR
  sensitive text.
- Review queues must show enough context to decide the item while preserving
  redaction; reviewers fetch raw source only through approved storage controls.

Minimum `pii_profile` fields:

- `contains_sensitive_person_data`
- `contains_financial_identifier`
- `contains_contact_or_location`
- `redaction_status`
- `hashing_policy`
- `raw_source_access_policy`
- `last_redaction_check_at`

## Single MCP Domain Brain Server

The v0 server shape is one logical MCP server named
`debt-collection-brain-mcp`. It wraps TrustGraph graph/config/document
capabilities and the domain legal-check engine behind purpose-built tools. The
single-server design keeps packet identity, graph provenance, rule checks, and
governance state consistent while still separating capabilities by tool group
and scope.

The server must:

- accept workspace/collection/flow context for TrustGraph isolation.
- enforce Bearer-token or gateway-provided identity and capability checks.
- hide raw SPARQL/graph complexity from client agents for common domain tasks.
- return machine-readable JSON with stable fields.
- include source references for every material fact or decision.
- redact sensitive fields by default.
- preserve a non-execution boundary for all recommendations.

## Tool Groups and Scopes

| Group | Scope | Purpose | Example Tools |
| --- | --- | --- | --- |
| `read` | Read-only packet, document, and summary access. | Query redacted case and document state. | `get_case_packet`, `get_case_documents`, `summarize_case_ledger` |
| `ingest` | Create source documents and ingest registry entries. | Load OCR markdown/text, assign hashes, start flow processing. | `ingest_legal_document`, `ingest_ocr_markdown`, `get_ingest_status` |
| `graph` | Read/build case graph and extraction facts. | Classify documents, resolve packet facts, expose graph projections. | `classify_legal_document`, `extract_case_packet`, `get_case_graph` |
| `stopgate` | Evaluate legal/compliance preconditions. | Return decisions, missing evidence, risk flags, and source refs. | `check_case_stop_gates`, `check_limitation_status`, `check_attachment_target_rules`, `recommend_next_action` |
| `governance` | Manage review queue state and candidate changes. | Review facts, unknown docs, low confidence, and ontology candidates. | `list_unknown_document_types`, `review_extracted_fact`, `promote_ontology_candidate`, `reprocess_case` |
| `admin` | Manage ontology/rule versions and privileged diagnostics. | Promote curated versions and inspect service health. | `get_domain_versions`, `promote_rule_source_version`, `run_packet_regression` |

Scope rules:

- `read` tools may not create facts, queue items, or rule outcomes.
- `ingest` tools may create documents and registry records but may not promote
  ontology or rule versions.
- `graph` tools may create candidate facts with provenance but may not clear
  StopGates by themselves.
- `stopgate` tools may create review items for missing or risky evidence but
  may not execute recommended actions.
- `governance` tools may transition review states according to approval rules
  but may not mutate raw documents.
- `admin` tools require explicit privileged scope and audit logging.

## Decision JSON Contract

Every StopGate or recommendation tool returns this shape at minimum:

```json
{
  "case_packet_id": "case-packet-redacted",
  "decision": "보류",
  "recommended_action": "collect_more_evidence",
  "required_preconditions": ["verified-enforcement-title"],
  "blocked_reasons": ["service-finality-unproven"],
  "missing_evidence": ["finality-proof-document"],
  "risk_flags": ["low-confidence-critical-fact"],
  "source_refs": [
    {
      "document_id": "doc-redacted",
      "chunk_id": "chunk-redacted",
      "span_ref": "span-redacted",
      "redaction_status": "redacted"
    }
  ],
  "rule_refs": [
    {
      "rule_id": "rule-redacted",
      "version": "0.1.0",
      "effective_date": "YYYY-MM-DD",
      "status": "approved"
    }
  ],
  "confidence": "medium",
  "review_queue_items": []
}
```

Allowed `decision` values:

- `가능`: available evidence and approved rules do not block the requested
  domain action, but external approval/execution remains outside the server.
- `불가능`: an approved rule or verified fact blocks the requested domain action.
- `보류`: evidence is missing, conflicting, stale, low confidence, or awaiting
  review.

## Curated Versioned Rule-Source Policy

v0 legal rules are curated artifacts, not live memory. Every rule source must be
reviewed, versioned, and promoted before production use.

Required fields:

- `rule_id`
- `rule_group`
- `statute_ref`
- `source_ref`
- `effective_date`
- `jurisdiction`
- `condition`
- `decision`
- `risk_flags`
- `required_evidence`
- `source_url` when available
- `version`
- `status`
- `reviewed_by`
- `reviewed_at`
- `supersedes`
- `notes`

Allowed statuses:

- `draft`
- `reviewed`
- `approved`
- `deprecated`
- `superseded`

Policy:

- Production StopGate checks may use only `approved` rule versions.
- A newer draft does not replace an approved rule until promoted.
- Rule changes require regression reprocessing over representative fixtures
  before promotion.
- Rule output must include `rule_id`, `version`, `effective_date`, and
  `source_ref`.
- If graph facts and approved rules disagree with a client agent's own memory,
  the MCP response must expose the conflict and return `보류` unless an approved
  rule clearly blocks the action.
- Automated law ingest and law-diff automation are deferred from v0.

## Governance and Review Queue Contract

Governance queues are service contracts for state transitions. They are not a
human UI requirement.

### Queue Types

| Queue ID | Created When | Required Resolution |
| --- | --- | --- |
| `unknown-document-type` | Classifier returns `unknown` or competing types. | assign type, reject, or add ontology candidate. |
| `low-confidence-extraction` | Critical fact below required confidence. | verify, correct, reject, or request more evidence. |
| `fact-conflict` | Two material facts conflict. | select scoped truth, preserve conflict, or mark unresolved. |
| `identity-merge-review` | Packet/party merge is uncertain. | merge, keep separate, or require more evidence. |
| `rule-risk-review` | StopGate depends on draft/stale/ambiguous rule source. | approve rule, deprecate rule, or keep blocked. |
| `ontology-candidate` | New class/property/document type is suggested. | approve candidate for next ontology version or reject. |
| `version-promotion` | Ontology/rule version is proposed for production. | approve only after regression evidence. |
| `case-reprocess` | Source, ontology, extractor, prompt, or rule version changes. | run reprocessing and attach evidence. |

### Review Item Fields

- `review_item_id`
- `queue_id`
- `case_packet_id`
- `document_id`
- `fact_id`
- `candidate_value`
- `current_value`
- `reason`
- `risk_flags`
- `source_refs`
- `redaction_status`
- `status`
- `created_at`
- `updated_at`
- `assigned_to`
- `resolution`
- `resolution_reason`
- `approved_by`
- `approval_evidence_ref`

Allowed item statuses:

- `open`
- `in-review`
- `needs-evidence`
- `approved`
- `rejected`
- `superseded`
- `closed`

No ontology, rule, or case merge promotion may occur from a single unreviewed
document or from an LLM-only assertion.

## Versioning Contract

Every case packet records the version set used to produce its current graph and
StopGate state:

- `ontology_version`
- `extractor_version`
- `prompt_version`
- `rule_source_version`
- `redaction_policy_version`
- `registry_schema_version`

Changing any version that affects material facts or StopGate decisions must
create a reprocess plan. Production promotion requires:

- regression run id
- fixture set id
- changed versions
- pass/fail result
- unresolved risk summary
- approval metadata

## Non-Execution Boundary

This server may recommend, block, or request evidence. It must not execute.

Allowed outputs:

- `decision`
- `recommended_action`
- `required_preconditions`
- `blocked_reasons`
- `missing_evidence`
- `risk_flags`
- `source_refs`
- `rule_refs`
- `review_queue_items`

Disallowed behavior:

- filing or submitting court documents
- contacting a debtor, guarantor, employer, bank, insurer, court, or registry
- initiating payment, transfer, settlement, attachment, collection, or seizure
- updating external business systems as if an action completed
- making final legal representation claims
- hiding missing evidence or conflicts behind a generated summary

Client agents must treat `recommended_action` as a pre-execution domain answer
that still requires their own authorization, approval, and execution workflow.

## Minimal Acceptance Checklist

The v0 implementation conforms to this contract only when:

- each document has a typed, confidence-scored, provenance-linked
  classification.
- every material fact links to source refs or reviewed derived-rule refs.
- `case_packet_id` is the canonical packet id and hybrid evidence keys are
  preserved.
- name-only party or case merging is blocked.
- StopGate checks return `가능`, `불가능`, or `보류` with reasons, rules,
  missing evidence, risk flags, and source refs.
- raw OCR sensitive identifiers are not emitted in docs, fixtures, logs, or
  default MCP responses.
- rule sources are curated, versioned, reviewed, and promoted before production
  use.
- governance queues exist for unknown, low-confidence, conflicting, candidate,
  promotion, and reprocessing states.
- the MCP domain brain remains agent-agnostic, Hermes-agnostic,
  user-UX-agnostic, and non-executing.
