# Debt Collection Ontology Planning Evidence

## Goal
Build a TrustGraph-based expert ontology layer for Korean receivables and debt-collection legal document packets, with continuous ingest and an agent-agnostic MCP domain brain server.

## Work Tier
HEAVY. The plan introduces a domain ontology, ingest registry, legal StopGate engine, MCP domain server contract, and verification workflow across multiple TrustGraph layers.

## Skills Used
- `omo:ulw-plan`: user requested `ulw` and an architecture plan.

## Source Evidence
- `README.md:18-24`: TrustGraph is a holonic context graph infrastructure layer for knowledge ingestion, structured storage, graph-grounded retrieval, agent orchestration, and LLM inferencing.
- `README.md:47-58`: Context Cores package ontology, holon/entity relationships, embeddings, provenance, retrieval policies, versioning, rollback, and promotion.
- `README.md:71-89`: TrustGraph uses Workspace, Collection, and Flow as knowledge isolation and processing boundaries; it includes ontology-driven graph construction and MCP integration.
- `README.md:146-158`: existing UI already has Document Ingestion, Ontology Workbench, GraphRAG, Context Explorer, and Prompt Editor surfaces.
- `docs/tech-specs/ontology.md:36-45`: ontologies are config items with type `ontology`, unique key, and JSON value.
- `docs/tech-specs/ontology.md:47-130`: ontology JSON supports metadata, classes, object properties, labels, comments, domains, ranges, and constraints.
- `docs/tech-specs/extraction-flows.md:49-79`: documents enter through librarian `add-document`, then `add-processing` triggers flow processing by document kind.
- `docs/tech-specs/extraction-flows.md:107-168`: chunking emits source-linked chunks into extraction processors; ontology-driven extraction is an existing extraction pattern.
- `docs/tech-specs/ontorag.md:17-34`: OntoRAG constrains extraction using loaded ontologies, semantic matching, and validation.
- `docs/tech-specs/ontorag.md:220-244`: ontology config is loaded dynamically, embedded per flow, selected per chunk, and emitted as triples/entity contexts.
- `trustgraph-flow/trustgraph/extract/kg/ontology/extract.py:109-128`: extractor registers `types=["ontology"]`, tracks per-workspace ontology versions, and keeps per-flow components.
- `trustgraph-flow/trustgraph/extract/kg/ontology/extract.py:211-302`: config updates reload ontology JSON and clear workspace flow components so new ontology embeddings are used.
- `trustgraph-flow/trustgraph/extract/kg/ontology/extract.py:304-350`: chunk processing selects ontology subset, extracts triples, and attaches subgraph provenance.
- `trustgraph-mcp/trustgraph/mcp_server/mcp.py:56-86`: MCP server accepts Bearer token and forwards auth to gateway.
- `trustgraph-mcp/trustgraph/mcp_server/mcp.py:366-397`: MCP registers graph RAG, agent, triples, SPARQL, GraphQL, config, flow, KG core, document, and processing tools.
- `trustgraph-mcp/trustgraph/mcp_server/mcp.py:1775-1835`: MCP has a `load_document` tool that uploads document content with metadata, MIME type, title, comments, tags, and workspace.

## OCR Corpus Evidence
Source: `/Users/cosmos/dev/ocr/MinerU/work/legal_ocr_20260630/legal_docs_markdown.zip`

- Markdown files: 208.
- High-frequency terms:
  - `압류`: 589
  - `제3채무자`: 231
  - `추심`: 206
  - `청구채권`: 186
  - `가압류`: 159
  - `질권`: 145
  - `주민등록`: 85
  - `가지급`: 79
  - `판결`: 69
  - `송달`: 60
  - `파산`: 51
  - `보험금`: 48
  - `채권압류`: 43
  - `추심명령`: 40
  - `신용정보`: 38
  - `면책`: 31
  - `승계`: 32
  - `보증인`: 32
  - `집행문`: 12
  - `소멸시효`: 2
- Keyword document buckets:
  - `송달확정/정본/집행문`: 95 files
  - `지급명령/판결/결정`: 83 files
  - `주민등록/법인등기`: 46 files
  - `채권압류추심신청/결정`: 40 files
  - `압류대상/우선순위`: 35 files
  - `채권양도/승계`: 22 files
  - `보증/상속`: 20 files
  - `파산/면책/신용회복`: 19 files
  - `채권보전/회수현황`: 15 files
  - `시효/이자계산`: 10 files
  - `부동산/자산증빙`: 6 files

## Current Source Fit
- Strong fit:
  - Existing ontology config format can hold the debt-collection ontology.
  - Existing OntoRAG extractor can constrain extraction to ontology elements.
  - Existing provenance paths can tie facts back to source documents/chunks.
  - Existing MCP server already exposes document upload, config, flow, graph, and query tools.
- Gaps:
  - Need a legal-document ingest registry before TrustGraph librarian ingestion.
  - Need domain-specific document classifiers and extractors for Korean legal packets.
  - Need deterministic rule/StopGate checks outside pure LLM extraction.
  - Need ontology version promotion, candidate review, and case reprocessing workflow.
- Need purpose-specific MCP tools for external agents instead of only generic graph/SPARQL tools.

## External Legal/Agent Evidence
- Hermes Agent can be a later MCP client, but this plan must not be Hermes-specific. The product boundary is the MCP domain server contract.
- Korean legal compliance rules must be source-versioned because debt collection duties and restrictions depend on statutes such as fair debt collection, personal financial debtor protection, credit information, civil execution exemptions, and insolvency/discharge law.

## Adopted Defaults
- Product ontology name: `recova-debt-collection` / Korean label `채권추심 사건 온톨로지`.
- Start from post-legal-action receivables packets, not all law.
- Treat laws/regulations as versioned rule sources, not as free-form memory.
- Use TrustGraph as KG/ontology/provenance runtime, with a separate operational case DB for review states, approvals, workflow locks, and reprocessing jobs.
- External agent integration happens through a domain MCP server that wraps TrustGraph and the legal-check engine.

## User-Approved Final Defaults
- MCP server shape: one `debt-collection-brain-mcp` domain brain server with tool group/scope separation (`read`, `ingest`, `graph`, `stopgate`, `governance`, `admin`).
- Case identity: one internal `case_packet_id` plus hybrid evidence keys (`court_case_number`, `claim_id`, `enforcement_title_id`, `party_identity_key`, `document_hash`).
- Rule source: curated, versioned legal rule sources for v0; live legal/law ingest and law diff automation are deferred.
- Action boundary: MCP returns `decision`, `recommended_action`, `required_preconditions`, `blocked_reasons`, `risk_flags`, and `source_refs`; execution is outside this server.

## User Clarification Applied
- The first consumer being a debt-collection practitioner is not a plan driver for this phase.
- This is not a person-facing UX plan and not a Hermes-specific adapter plan.
- The target artifact is the "domain brain": ontology + case graph + evidence + StopGate + MCP tools.
- Agents perform the business workflow; this server provides the domain world model and pre-action reasoning interface.
- Destructive/legal-risk actions must be represented as explicit blocked/precondition states; execution and approval flows live outside the domain brain server.
