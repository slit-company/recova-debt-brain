---
slug: debt-collection-ontology
status: drafting
intent: unclear
pending-action: write .omo/plans/debt-collection-ontology.md
approach: TrustGraph core remains the ontology/KG/provenance runtime; add a Korean debt-collection MCP domain brain server with ontology JSON, document ingest registry, deterministic legal StopGate engine, case graph builder, and agent-agnostic MCP tool contracts.
---

# Draft: debt-collection-ontology

## Components (topology ledger)
<!-- Lock the SHAPE before depth. One row per top-level component that can succeed or fail independently. -->
<!-- id | outcome (one line) | status: active|deferred | evidence path -->
| C1 | Domain ontology models Korean receivables/debt-collection legal packets, not all law | active | .omo/evidence/debt-collection-ontology-findings.md |
| C2 | Continuous ingest registry dedupes documents, preserves OCR/source provenance, and feeds TrustGraph librarian/flows | active | .omo/evidence/debt-collection-ontology-findings.md |
| C3 | Case graph builder resolves party/claim/procedure/asset/legal-action facts into one case packet graph | active | .omo/evidence/debt-collection-ontology-findings.md |
| C4 | Legal StopGate engine runs deterministic checks for enforcement, insolvency, limitation, attachment exemptions, identity, and privacy risk | active | .omo/evidence/debt-collection-ontology-findings.md |
| C5 | Agent-agnostic MCP domain server exposes purpose-built tools over TrustGraph and StopGate results | active | .omo/evidence/debt-collection-ontology-findings.md |
| C6 | Evaluation and governance pipeline handles ontology candidate promotion, reprocessing, and regression tests | active | .omo/evidence/debt-collection-ontology-findings.md |

## Open assumptions (announced defaults)
<!-- Intent is UNCLEAR: research resolves ambiguity, defaults are adopted (not asked), and each is surfaced in the plan's human TL;DR for veto. -->
<!-- assumption | adopted default | rationale | reversible? -->
| Product scope | Start with post-legal-action receivables/debt-collection packets | OCR corpus is dominated by attachment/collection, judgments, service/finality, insolvency, identity, asset, and ledger docs | yes |
| Runtime boundary | TrustGraph remains KG/ontology/provenance runtime; operational status lives outside KG | Review states, approvals, reprocessing jobs, and legal holds need transactional workflow semantics | yes |
| Agent integration | Connect through MCP tools, not a specific agent runtime | MCP is the product boundary; Hermes or any later agent is only a client | yes |
| Legal rules | Treat statutes/rules as versioned rule sources, not native memory | Legal facts change and need act-as-of-time provenance | yes |
| Execution stance | The domain brain never executes irreversible actions; it returns preconditions, blockers, and evidence for external execution layers | Domain is regulated and high risk | yes |
| Ontology format | Use TrustGraph `type=ontology` JSON first; export/import OWL/Turtle later | Existing extractor and config pipeline already consume this format | yes |
| MCP server shape | Single `debt-collection-brain-mcp` service with tool group/scope separation | Fits TrustGraph's existing MCP surface and keeps v0 integration coherent | yes |
| Case identity | Internal `case_packet_id` plus hybrid evidence keys | Legal packets span court cases, claims, enforcement titles, parties, and document hashes | yes |
| Rule source | Curated versioned rule source for v0 | Safer than live law ingest while extraction/rule quality is still being proven | yes |
| Action boundary | MCP returns decisions, prerequisites, blocked reasons, risks, and source refs only | Execution belongs to external agents/tools, not the domain brain server | yes |

## Findings (cited - path:lines)
- TrustGraph's README positions the repo as a holonic context graph infrastructure for ingestion, structured storage, graph retrieval, orchestration, and LLM inferencing: `README.md:18-24`.
- Context Cores include ontology, holon/entity relationships, embeddings, provenance, retrieval policies, versioning, rollback, and promotion: `README.md:47-58`.
- Workspace, Collection, and Flow are the correct isolation and processing boundaries for customers, portfolios, and pipelines: `README.md:71-89`.
- The existing UI already mentions Document Ingestion and Ontology Workbench, so the product can start API/MCP-first without inventing UI as the core: `README.md:146-158`.
- TrustGraph stores ontologies as config items with type `ontology`, a unique key, and JSON value: `docs/tech-specs/ontology.md:36-45`.
- The ontology format supports metadata, classes, object properties, labels, comments, domains, ranges, and constraints: `docs/tech-specs/ontology.md:47-130`.
- Documents enter through librarian `add-document`, then `add-processing` sends them to a flow/collection: `docs/tech-specs/extraction-flows.md:49-79`.
- Chunks preserve document hierarchy and can feed ontology-driven extraction: `docs/tech-specs/extraction-flows.md:107-168`.
- OntoRAG constrains extraction to loaded ontologies and validates semantic consistency: `docs/tech-specs/ontorag.md:17-34`.
- Ontology config is loaded dynamically, embedded per flow, selected per chunk, and emitted as triples/entity contexts: `docs/tech-specs/ontorag.md:220-244`.
- The ontology extractor registers config updates for `types=["ontology"]`, tracks workspace versions, and holds per-flow components: `trustgraph-flow/trustgraph/extract/kg/ontology/extract.py:109-128`.
- Ontology config updates reload JSON and clear flow components for a workspace so new embeddings apply: `trustgraph-flow/trustgraph/extract/kg/ontology/extract.py:211-302`.
- The MCP server already registers generic graph, SPARQL, GraphQL, config, flow, KG core, document, and processing tools: `trustgraph-mcp/trustgraph/mcp_server/mcp.py:366-397`.
- MCP document upload supports document content, metadata, MIME type, title, comments, tags, and workspace: `trustgraph-mcp/trustgraph/mcp_server/mcp.py:1775-1835`.
- OCR corpus has 208 markdown files and high concentrations of attachment, third-party debtor, claim amount, judgment, service, insolvency, surety, succession, identity, priority, and ledger terms: `.omo/evidence/debt-collection-ontology-findings.md`.

## Decisions (with rationale)
- Build `recova-debt-collection` as a TrustGraph ontology config, not as an unconstrained prompt pack.
- Build one `debt-collection-brain-mcp` server for v0 and separate capabilities by tool group/scope: `read`, `ingest`, `graph`, `stopgate`, `governance`, `admin`.
- Use `case_packet_id` as the internal canonical case packet ID and attach `court_case_number`, `claim_id`, `enforcement_title_id`, `party_identity_key`, and `document_hash` as evidence keys.
- Start with curated, versioned legal rule sources carrying `rule_id`, `statute_ref`, `effective_date`, `condition`, `decision`, `source_url`, and `version`.
- Keep MCP action responses non-executing: return `decision`, `recommended_action`, `required_preconditions`, `blocked_reasons`, `risk_flags`, and `source_refs`.
- Split the ontology into domain modules: Party and Identity, Claim and Amount, Assignment and Succession, Enforcement Title and Procedure, Attachment Target, Exemption and Priority, Insolvency and Credit Recovery, Asset Evidence, Operational Ledger, Document Provenance, Legal Check and StopGate.
- Add a legal ingest registry before TrustGraph librarian ingestion. TrustGraph stores and processes documents, but the product needs dedupe, source hash, OCR version, extractor version, ontology version, review state, and reprocess state.
- Add deterministic StopGate checks outside LLM extraction. LLM extraction can populate facts, but high-risk legal decisions must be rule-evaluated.
- Expose the domain brain through purpose-built MCP tools, not raw SPARQL only. Raw graph queries remain available for debugging, but client agents should call domain tools like `check_case_stop_gates`.
- Keep any client agent's native memory as auxiliary context only. The ontology/KG/rule outputs are the source of truth.
- Start with OCR markdown ingestion because the current corpus is already OCR'd; binary PDF/image upload can be the second ingest lane.

## Scope IN
- Initial ontology JSON and validation fixture set.
- OCR markdown ingest from `/Users/cosmos/dev/ocr/MinerU/work/legal_ocr_20260630/legal_docs_markdown.zip`.
- Document registry with source hash, OCR version, extractor version, ontology version, review status, and provenance pointers.
- Document classifiers for legal packet types found in the OCR corpus.
- Field extraction and case graph construction for debt collection packets.
- Legal StopGate engine for enforcement title, service/finality, assignment/succession, amount consistency, limitation, insolvency/discharge/credit recovery, attachment target, exemption/priority, identity, and privacy purpose risk.
- MCP domain server tools for ingest, case graph retrieval, StopGate checks, ledger summary, and next-action precondition recommendation.
- Single MCP server with tool group/scope separation.
- Hybrid case identity resolver with `case_packet_id`.
- Curated versioned rule registry for v0.
- Non-executing action contract for all MCP recommendations.
- Regression evaluation over representative OCR fixtures and synthetic adversarial fixtures.

## Scope OUT (Must NOT have)
- Must not claim to provide final legal advice or replace licensed legal review.
- Must not automate destructive legal filing/submission inside the domain brain server; represent those as blocked/precondition states for external execution layers.
- Must not fine-tune or modify a specific agent runtime in the first version.
- Must not create multiple physical MCP services in v0 unless a concrete security boundary requires it.
- Must not merge cases using one weak key such as name, phone number, or one OCR'd case number.
- Must not auto-update live statutes into production rule decisions in v0.
- Must not execute filings, contacts, collections, or irreversible actions from this server.
- Must not store raw PII in logs, prompts, or user-visible artifacts.
- Must not treat LLM-extracted facts as true without source provenance and confidence.
- Must not fold legal statutes into unversioned native memory.

## Open questions
- None blocking. The plan adopts reversible defaults and should be treated as a first implementation plan for the domain core.

## Approval gate
status: plan-written
<!-- When exploration is exhausted and unknowns are answered, set status: awaiting-approval. -->
<!-- That durable record is the loop guard: on a later turn read it and resume at the gate instead of re-running exploration. -->
