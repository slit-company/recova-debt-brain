# Debt-Collection Ontology On TrustGraph

## TL;DR
> Summary:      Build a Korean receivables/debt-collection legal ontology as an immutable, versioned TrustGraph Context Core, fed by continuous document-packet ingest and guarded by deterministic legal StopGates before any agent or MCP tool can use extracted facts for external action.
> Deliverables:
> - Versioned debt-collection ontology JSON/Turtle plus release manifest
> - Continuous ingest driver for OCR markdown/legal packets
> - Legal packet normalization, PII redaction, provenance, and confidence quarantine
> - StopGate rule service over SPARQL/graph queries
> - MCP/Hermes-facing read and decision tools
> - QA/evidence harness for ingest, ontology extraction, provenance, StopGates, and MCP tools
> Effort:       Large
> Risk:         High - legal/compliance failures and OCR provenance defects can produce harmful collection actions.

## Scope
### Must have
- Treat TrustGraph as the system-of-record graph, document, provenance, and query backend, aligned to Workspace -> Collection -> Flow isolation from `README.md:71` and `README.md:73`.
- Ingest the existing OCR markdown packet archive at `/Users/cosmos/dev/ocr/MinerU/work/legal_ocr_20260630/legal_docs_markdown.zip`, which currently contains 209 entries under `markdown_flat/`.
- Normalize Korean legal packet artifacts: 채권, 채무자, 채권자, 지급명령, 판결/집행권원, 부동산/등기/권리관계, 압류/가압류/경매, 송달, 변제, 회생/파산, 개인정보/신용정보.
- Preserve source hierarchy as source document -> page/section -> chunk -> extracted subgraph using the repo's `urn:graph:source` provenance pattern in `docs/tech-specs/extraction-flows.md:277`.
- Version ontologies with immutable semantic releases, not just config version numbers. Store ontology version in ontology metadata and extraction provenance.
- Implement StopGates as deterministic graph/rule checks before agent finalization or external collection action.
- Expose only safe tools through MCP/Hermes: read/query, packet status, StopGate evaluation, evidence bundle generation. Any write/escalation/legal-action tool must require a passed StopGate result and explicit workflow state.
- Use current official Korean statutes as rule references: Fair Debt Collection Practices Act, Personal Information Protection Act, Credit Information Use and Protection Act, Civil Execution Act, Civil Procedure Act, Debtor Rehabilitation and Bankruptcy Act.

### Must NOT have (guardrails, anti-slop, scope boundaries)
- Do not mutate TrustGraph core behavior without tests and evidence for workspace, collection, and provenance boundaries.
- Do not treat OCR text as legally reliable unless every extracted claim has source coordinates, confidence metadata, and provenance.
- Do not let an LLM decide StopGate pass/fail. LLMs may propose facts; deterministic rule queries decide.
- Do not index or expose unredacted resident registration numbers, phone numbers, account numbers, addresses, or employer/contact information to general agent tools.
- Do not rely on no-auth or anonymous workspace behavior for production legal data.
- Do not overwrite an existing ontology version in place. Publish a new version and migration note.
- Do not expose Hermes writable external directories as a security boundary.
- Do not produce legal advice. The system emits structured evidence, status, and blocked/allowed workflow decisions.

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: TDD + pytest/pytest-asyncio, CLI smoke tests, SPARQL assertions, MCP tool invocation checks
- QA policy: every task has agent-executed scenarios
- Evidence: `.omo/evidence/task-<N>-<slug>.<ext>`

## Execution strategy
### Parallel execution waves
> Target 5-8 tasks per wave. <3 per wave (except final) = under-splitting.
> Extract shared dependencies as Wave-1 tasks to maximize parallelism.

Wave 1 (no dependencies):
- Task 1: Define ontology release and legal packet schema
- Task 2: Build OCR markdown packet inventory and normalization contracts
- Task 3: Define provenance/evidence contract and confidence model
- Task 4: Define StopGate rule registry and statutory references
- Task 5: Establish workspace/collection/flow deployment blueprint

Wave 2 (after Wave 1):
- Task 6: Implement continuous ingest driver for zip/directory/object-store inputs; depends [2, 5]
- Task 7: Implement ontology-constrained extraction configuration; depends [1, 2, 3]
- Task 8: Implement StopGate evaluator service; depends [3, 4, 7]
- Task 9: Implement ontology version publish/promote/rollback workflow; depends [1, 3, 5]
- Task 10: Implement MCP/Hermes tool surfaces; depends [4, 5, 8]

Wave 3 (after Wave 2):
- Task 11: Build end-to-end legal packet evidence harness; depends [6, 7, 8, 9, 10]
- Task 12: Harden observability, audit, and failure quarantine; depends [6, 7, 8, 10]

Critical path: Task 1 -> Task 7 -> Task 8 -> Task 10 -> Task 11

### Dependency matrix
| Task | Depends on | Blocks | Can parallelize with |
|------|------------|--------|----------------------|
| 1    | none       | 7, 9   | 2, 3, 4, 5           |
| 2    | none       | 6, 7   | 1, 3, 4, 5           |
| 3    | none       | 7, 8, 9 | 1, 2, 4, 5          |
| 4    | none       | 8, 10  | 1, 2, 3, 5           |
| 5    | none       | 6, 9, 10 | 1, 2, 3, 4         |
| 6    | 2, 5       | 11, 12 | 7, 8, 9, 10          |
| 7    | 1, 2, 3    | 8, 11, 12 | 6, 9, 10         |
| 8    | 3, 4, 7    | 10, 11, 12 | 6, 9            |
| 9    | 1, 3, 5    | 11     | 6, 7, 8, 10          |
| 10   | 4, 5, 8    | 11, 12 | 6, 7, 9              |
| 11   | 6, 7, 8, 9, 10 | F1-F4 | 12              |
| 12   | 6, 7, 8, 10 | F1-F4 | 11                 |

## Todos
> Implementation + Test = ONE task. Never separate.
> Every task MUST have: References + Acceptance Criteria + QA Scenarios + Commit.

- [ ] 1. Define ontology release and legal packet schema

  What to do: Create a debt-collection ontology package with immutable semantic version metadata, Korean/English labels, namespace policy, class/property model, and SHACL-like validation fixtures. Include at minimum parties, claims, obligations, debt instruments, legal titles, court events, service events, execution actions, asset/property records, payments, disputes, insolvency events, consent/privacy controls, and evidence nodes.
  Must NOT do: Do not rely on the current root `schema.ttl` as the domain ontology; it is only a small label seed.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [7, 9] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `docs/tech-specs/ontology.md:36` - Ontologies are stored as config items with type `ontology`, key, and JSON value.
  - API/Type: `docs/tech-specs/ontology.md:47` - Ontology metadata includes version, timestamps, namespace, and imports.
  - API/Type: `docs/tech-specs/ontology.md:76` - Classes use URI, type, labels, comments, subclass/equivalence/disjoint fields.
  - API/Type: `docs/tech-specs/ontology.md:107` - Object properties define domain/range and inverse/functional behavior.
  - API/Type: `docs/tech-specs/ontology.md:139` - Datatype properties define literal fields and XSD ranges.
  - Pattern:  `schema.ttl:1` - Current checked-in schema is only generic label vocabulary, not domain ontology.
  - Pattern:  `ontology-prompt.md:25` - Extraction prompt requires only provided ontology classes/properties.
  - External: `https://www.w3.org/TR/owl2-syntax/` - OWL ontology IRI/version IRI model.
  - External: `https://www.law.go.kr/법령/채권의공정한추심에관한법률` - Fair debt collection statutory anchor.

  Acceptance criteria (agent-executable only):
  - [ ] `python -m json.tool ontology/debt-collection/v1/ontology.json > .omo/evidence/task-1-ontology-json.txt` exits 0.
  - [ ] `python scripts/validate_ontology.py ontology/debt-collection/v1/ontology.json --require-version --require-labels ko,en --require-uris | tee .omo/evidence/task-1-ontology-validate.txt` exits 0.
  - [ ] `rg -n '"version"|채권|채무자|지급명령|집행권원|회생|파산|개인정보|신용정보' ontology/debt-collection/v1/ontology.json | tee .omo/evidence/task-1-domain-coverage.txt` returns all required concepts.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: ontology loads and validates
    Tool:     bash
    Steps:    python scripts/validate_ontology.py ontology/debt-collection/v1/ontology.json --sample ontology/debt-collection/v1/samples/legal-packet-minimal.json | tee .omo/evidence/task-1-ontology-happy.txt
    Expected: exit 0 and output contains "ontology valid"
    Evidence: .omo/evidence/task-1-ontology-happy.txt

  Scenario: invalid domain/range is rejected
    Tool:     bash
    Steps:    python scripts/validate_ontology.py ontology/debt-collection/v1/fixtures/invalid-domain-range.json 2>&1 | tee .omo/evidence/task-1-ontology-error.txt; test ${PIPESTATUS[0]} -ne 0
    Expected: output contains "unknown domain" or "domain violation"
    Evidence: .omo/evidence/task-1-ontology-error.txt
  ```

  Commit: YES | Message: `feat(ontology): define debt collection legal ontology` | Files: [ontology/debt-collection/v1/**, scripts/validate_ontology.py, tests/**]

- [ ] 2. Build OCR markdown packet inventory and normalization contracts

  What to do: Implement a packet inventory tool that reads `/Users/cosmos/dev/ocr/MinerU/work/legal_ocr_20260630/legal_docs_markdown.zip`, fingerprints every markdown file, classifies likely document type, extracts basic Korean legal fields, flags OCR noise, and writes normalized packet manifests without altering the archive.
  Must NOT do: Do not assume one image equals one case packet. Do not discard malformed OCR tables; quarantine them with reason codes.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [6, 7] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Input:    `/Users/cosmos/dev/ocr/MinerU/work/legal_ocr_20260630/legal_docs_markdown.zip` - OCR markdown archive, 209 zip entries under `markdown_flat/`.
  - Pattern:  `trustgraph-unstructured/trustgraph/decoding/universal/processor.py:2` - Universal decoder accepts PDF/DOCX/XLSX/HTML/Markdown/plain text and preserves tables as HTML.
  - Pattern:  `trustgraph-unstructured/trustgraph/decoding/universal/processor.py:73` - Text/table/image assembly logic separates text, HTML tables, and images.
  - Pattern:  `trustgraph-unstructured/trustgraph/decoding/universal/processor.py:116` - Universal decoder is a flow processor with document input, text output, triples output, and librarian access.
  - Pattern:  `trustgraph-flow/trustgraph/chunking/recursive/chunker.py:30` - Chunker persists downstream chunks with provenance.
  - Test:     `tests/unit/test_decoding/test_universal_processor.py` - Existing decoder test family to follow.

  Acceptance criteria (agent-executable only):
  - [ ] `python scripts/legal_packet_inventory.py /Users/cosmos/dev/ocr/MinerU/work/legal_ocr_20260630/legal_docs_markdown.zip --out .omo/evidence/task-2-inventory.json` exits 0.
  - [ ] `.omo/evidence/task-2-inventory.json` contains `entry_count: 209`, per-entry SHA-256, byte length, guessed document type, PII flags, OCR quality flags, and quarantine status.
  - [ ] `python -m pytest tests/unit/test_legal_packet_inventory.py -q | tee .omo/evidence/task-2-tests.txt` exits 0.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: real OCR archive is inventoried
    Tool:     bash
    Steps:    python scripts/legal_packet_inventory.py /Users/cosmos/dev/ocr/MinerU/work/legal_ocr_20260630/legal_docs_markdown.zip --out .omo/evidence/task-2-real-inventory.json && python scripts/assert_inventory.py .omo/evidence/task-2-real-inventory.json --entries 209 --require-pii-flags --require-quarantine
    Expected: exit 0 and all 209 archive entries are represented exactly once
    Evidence: .omo/evidence/task-2-real-inventory.json

  Scenario: corrupt zip fails closed
    Tool:     bash
    Steps:    printf 'not-a-zip' > /tmp/not-a-legal-packet.zip; python scripts/legal_packet_inventory.py /tmp/not-a-legal-packet.zip --out .omo/evidence/task-2-corrupt.json 2>&1 | tee .omo/evidence/task-2-corrupt-error.txt; test ${PIPESTATUS[0]} -ne 0
    Expected: output contains "invalid zip" and no partial manifest is produced
    Evidence: .omo/evidence/task-2-corrupt-error.txt
  ```

  Commit: YES | Message: `feat(ingest): inventory legal OCR packet archives` | Files: [scripts/legal_packet_inventory.py, scripts/assert_inventory.py, tests/unit/test_legal_packet_inventory.py]

- [ ] 3. Define provenance/evidence contract and confidence model

  What to do: Create the evidence contract that every extracted legal fact must satisfy: source document ID, root packet ID, page/section/chunk URI, character span or table cell reference when available, extraction component/version, ontology ID/version, OCR confidence or quality class, redaction state, and named graph.
  Must NOT do: Do not place source provenance in the default graph. Do not make source coordinates optional for facts used by StopGates.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [7, 8, 9] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `docs/tech-specs/extraction-flows.md:277` - Named graphs separate default facts, `urn:graph:source`, and `urn:graph:retrieval`.
  - Pattern:  `docs/tech-specs/extraction-time-provenance.md:30` - Desired source DAG is document -> page -> chunk -> extracted fact.
  - Pattern:  `docs/tech-specs/extraction-time-provenance.md:49` - Provenance DAG is stored in the same knowledge graph.
  - Pattern:  `trustgraph-base/trustgraph/schema/core/metadata.py:4` - Metadata has source `id`, root document, and collection.
  - Pattern:  `trustgraph-flow/trustgraph/chunking/recursive/chunker.py:143` - Chunks are saved as child documents before downstream extraction.
  - Pattern:  `trustgraph-flow/trustgraph/chunking/recursive/chunker.py:152` - Chunk provenance triples are emitted into `GRAPH_SOURCE`.
  - Pattern:  `trustgraph-flow/trustgraph/extract/kg/ontology/extract.py:346` - OntoRAG generates subgraph provenance for extracted triples.
  - API/Type: `trustgraph-cli/trustgraph/cli/show_extraction_provenance.py:44` - CLI uses `urn:graph:source`.
  - API/Type: `trustgraph-cli/trustgraph/cli/show_explain_trace.py:42` - Query trace separates `urn:graph:retrieval` and `urn:graph:source`.
  - External: `https://www.w3.org/TR/prov-o/` - PROV-O model.

  Acceptance criteria (agent-executable only):
  - [ ] `python scripts/validate_evidence_contract.py docs/legal/evidence-contract.yaml | tee .omo/evidence/task-3-contract-validate.txt` exits 0.
  - [ ] `python -m pytest tests/unit/test_legal_evidence_contract.py -q | tee .omo/evidence/task-3-tests.txt` exits 0.
  - [ ] `rg -n 'urn:graph:source|componentVersion|ontologyVersion|redactionState|ocrQuality|chunkUri' docs/legal/evidence-contract.yaml | tee .omo/evidence/task-3-fields.txt` returns all required fields.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: extracted fact with full lineage is accepted
    Tool:     bash
    Steps:    python scripts/validate_evidence_contract.py docs/legal/evidence-contract.yaml --sample tests/fixtures/legal_evidence/valid-fact.json | tee .omo/evidence/task-3-valid-fact.txt
    Expected: exit 0 and output contains "evidence valid"
    Evidence: .omo/evidence/task-3-valid-fact.txt

  Scenario: extracted fact without chunk provenance is rejected
    Tool:     bash
    Steps:    python scripts/validate_evidence_contract.py docs/legal/evidence-contract.yaml --sample tests/fixtures/legal_evidence/missing-chunk.json 2>&1 | tee .omo/evidence/task-3-missing-chunk.txt; test ${PIPESTATUS[0]} -ne 0
    Expected: output contains "chunkUri is required"
    Evidence: .omo/evidence/task-3-missing-chunk.txt
  ```

  Commit: YES | Message: `feat(provenance): define legal evidence contract` | Files: [docs/legal/evidence-contract.yaml, scripts/validate_evidence_contract.py, tests/unit/test_legal_evidence_contract.py, tests/fixtures/legal_evidence/**]

- [ ] 4. Define StopGate rule registry and statutory references

  What to do: Build a versioned StopGate registry with deterministic rules, rule IDs, statutory anchors, required graph evidence, failure state, safe user-facing message, and audit severity. Include gates for redaction, source provenance, jurisdiction, claim/legal-title sufficiency, statute/date freshness, debtor dispute/insolvency, contact restrictions, authority/delegation, and external-action review.
  Must NOT do: Do not encode legal conclusions as prompt text only. Do not let a passed StopGate bypass human/legal workflow states for external notices or filings.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [8, 10] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `docs/tech-specs/tool-group.md:14` - Tool-group spec identifies security risk from all tools being available in all contexts.
  - Pattern:  `docs/tech-specs/tool-group.md:143` - Agent requests filter available tools by requested group and state.
  - Pattern:  `docs/tech-specs/tool-group.md:301` - Audit trail should log requested groups, state transitions, denied attempts, and suspicious workflows.
  - API/Type: `trustgraph-base/trustgraph/api/flow.py:1005` - SPARQL query API for deterministic graph checks.
  - API/Type: `trustgraph-mcp/trustgraph/mcp_server/mcp.py:739` - MCP exposes SPARQL query with collection, flow, workspace, and limit.
  - External: `https://www.law.go.kr/법령/채권의공정한추심에관한법률` - Collection conduct and contact restrictions.
  - External: `https://www.law.go.kr/법령/개인정보보호법` - Personal data processing/redaction.
  - External: `https://www.law.go.kr/법령/신용정보의이용및보호에관한법률` - Credit information handling.
  - External: `https://www.law.go.kr/법령/민사집행법` - Execution procedures and enforceable claims.
  - External: `https://www.law.go.kr/법령/민사소송법` - Payment order/litigation procedural anchors.
  - External: `https://www.law.go.kr/법령/채무자회생및파산에관한법률` - Insolvency/rehabilitation stop conditions.

  Acceptance criteria (agent-executable only):
  - [ ] `python -m json.tool config/stopgates/debt-collection.v1.json > .omo/evidence/task-4-stopgate-json.txt` exits 0.
  - [ ] `python scripts/validate_stopgates.py config/stopgates/debt-collection.v1.json --require-statutory-anchors --require-failure-state | tee .omo/evidence/task-4-stopgate-validate.txt` exits 0.
  - [ ] `python -m pytest tests/unit/test_stopgate_registry.py -q | tee .omo/evidence/task-4-tests.txt` exits 0.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: complete evidence passes read-only answer gates
    Tool:     bash
    Steps:    python scripts/evaluate_stopgates.py --rules config/stopgates/debt-collection.v1.json --facts tests/fixtures/stopgates/pass-readonly.json --mode answer | tee .omo/evidence/task-4-pass-answer.txt
    Expected: exit 0 and JSON contains `"decision":"allow"` plus non-empty `passedRuleIds`
    Evidence: .omo/evidence/task-4-pass-answer.txt

  Scenario: unredacted resident number blocks tool use
    Tool:     bash
    Steps:    python scripts/evaluate_stopgates.py --rules config/stopgates/debt-collection.v1.json --facts tests/fixtures/stopgates/unredacted-pii.json --mode agent-tool 2>&1 | tee .omo/evidence/task-4-pii-block.txt; test ${PIPESTATUS[0]} -ne 0
    Expected: JSON contains `"decision":"block"` and rule id `redaction_required`
    Evidence: .omo/evidence/task-4-pii-block.txt
  ```

  Commit: YES | Message: `feat(stopgate): define legal rule registry` | Files: [config/stopgates/debt-collection.v1.json, scripts/validate_stopgates.py, scripts/evaluate_stopgates.py, tests/unit/test_stopgate_registry.py, tests/fixtures/stopgates/**]

- [ ] 5. Establish workspace/collection/flow deployment blueprint

  What to do: Define a TrustGraph deployment blueprint for Korean legal packets: workspace per tenant or legal operator, collections per customer/case/corpus, flow per ingest/extraction variant, queues per workspace/flow, and isolated tool groups for read-only, stopgate, admin, and external-action operations.
  Must NOT do: Do not depend on payload-only workspace fields for authorization-sensitive boundaries.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [6, 9, 10] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `README.md:71` - TrustGraph organizes Workspaces, Collections, and Flows.
  - Pattern:  `README.md:75` - Workspace is the tenancy boundary.
  - Pattern:  `README.md:77` - Collection groups related holons, graph structures, embeddings, and documents.
  - Pattern:  `README.md:79` - Flow is the ingestion/extraction/storage pipeline.
  - Pattern:  `docs/tech-specs/flow-blueprint-definition.md:63` - Interfaces are flow entry points and interaction contracts.
  - Pattern:  `docs/tech-specs/flow-blueprint-definition.md:86` - Interfaces include entry points, service interfaces, and data interfaces.
  - Pattern:  `docs/tech-specs/flow-blueprint-definition.md:222` - Flow blueprints use Pulsar queue naming.
  - Pattern:  `docs/tech-specs/flow-blueprint-definition.md:249` - Dataflow combines document processing, query services, shared services, and storage writers.
  - Pattern:  `docs/tech-specs/workspace-scoped-services.md:47` - Workspace-scoped services should use per-workspace queues.
  - Pattern:  `docs/tech-specs/collection-management.md:11` - Collections must be explicitly created before use and synchronized across stores.

  Acceptance criteria (agent-executable only):
  - [ ] `python scripts/validate_flow_blueprint.py config/flows/legal-packet-ontorag.json | tee .omo/evidence/task-5-flow-validate.txt` exits 0.
  - [ ] `python scripts/validate_tool_groups.py config/tool-groups/legal-agent-tools.json --require-groups readonly,stopgate,admin,external-action | tee .omo/evidence/task-5-toolgroups.txt` exits 0.
  - [ ] `rg -n 'workspace|collection|legal-packet|kg-extract-ontology|stopgate|readonly|external-action' config/flows config/tool-groups | tee .omo/evidence/task-5-blueprint-fields.txt` returns expected wiring.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: legal flow blueprint resolves all interfaces
    Tool:     bash
    Steps:    python scripts/validate_flow_blueprint.py config/flows/legal-packet-ontorag.json --expand workspace=legal-demo flow=legal-demo-flow | tee .omo/evidence/task-5-flow-expanded.txt
    Expected: exit 0 and output contains document-load, text-load, triples, entity-contexts, sparql, graph-rag
    Evidence: .omo/evidence/task-5-flow-expanded.txt

  Scenario: external action tools are absent from read-only group
    Tool:     bash
    Steps:    python scripts/validate_tool_groups.py config/tool-groups/legal-agent-tools.json --assert-group-excludes readonly external-action | tee .omo/evidence/task-5-readonly-excludes.txt
    Expected: exit 0 and output contains "readonly excludes external-action"
    Evidence: .omo/evidence/task-5-readonly-excludes.txt
  ```

  Commit: YES | Message: `feat(flow): define legal packet ontology flow` | Files: [config/flows/legal-packet-ontorag.json, config/tool-groups/legal-agent-tools.json, scripts/validate_flow_blueprint.py, scripts/validate_tool_groups.py, tests/**]

- [ ] 6. Implement continuous ingest driver for zip/directory/object-store inputs

  What to do: Implement a continuous ingest driver that can read the existing zip, watch a directory, or poll object storage; deduplicate by SHA-256; call TrustGraph librarian add-document/load-processing APIs; tag source kind, case key, tenant/workspace, collection, and packet manifest; and record idempotent ingest state.
  Must NOT do: Do not add a repo-native file watcher into low-level TrustGraph processors. Keep it as an integration driver that calls public APIs.

  Parallelization: Can parallel: YES | Wave 2 | Blocks: [11, 12] | Blocked by: [2, 5]

  References (executor has NO interview context - be exhaustive):
  - API/Type: `trustgraph-base/trustgraph/api/library.py:96` - `Library.add_document()` stores document bytes with metadata/title/kind/tags.
  - API/Type: `trustgraph-base/trustgraph/api/library.py:210` - Small-document add request uses `add-document`, workspace, metadata, content.
  - API/Type: `trustgraph-cli/trustgraph/cli/add_library_document.py:45` - CLI loader reads file bytes, hashes/generates document URI, and calls `api.add_document`.
  - API/Type: `trustgraph-cli/trustgraph/cli/start_library_processing.py:13` - CLI starts library processing with document ID, flow, collection, tags.
  - Pattern:  `docs/tech-specs/extraction-flows.md:49` - Documents enter through librarian `add-document`.
  - Pattern:  `docs/tech-specs/extraction-flows.md:58` - `add-processing` triggers extraction to a flow and collection.

  Acceptance criteria (agent-executable only):
  - [ ] `python scripts/legal_packet_ingest.py --dry-run --zip /Users/cosmos/dev/ocr/MinerU/work/legal_ocr_20260630/legal_docs_markdown.zip --workspace legal-demo --collection demo-case --manifest .omo/evidence/task-6-dry-run.json` exits 0.
  - [ ] Dry-run manifest has 208 markdown documents plus directory entry skipped or explicitly marked non-document, no network/API writes, and stable IDs.
  - [ ] `python -m pytest tests/unit/test_legal_packet_ingest.py -q | tee .omo/evidence/task-6-tests.txt` exits 0.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: dry-run zip ingest is deterministic
    Tool:     bash
    Steps:    python scripts/legal_packet_ingest.py --dry-run --zip /Users/cosmos/dev/ocr/MinerU/work/legal_ocr_20260630/legal_docs_markdown.zip --workspace legal-demo --collection demo-case --manifest .omo/evidence/task-6-run1.json && python scripts/legal_packet_ingest.py --dry-run --zip /Users/cosmos/dev/ocr/MinerU/work/legal_ocr_20260630/legal_docs_markdown.zip --workspace legal-demo --collection demo-case --manifest .omo/evidence/task-6-run2.json && diff -u .omo/evidence/task-6-run1.json .omo/evidence/task-6-run2.json | tee .omo/evidence/task-6-diff.txt
    Expected: diff exits 0; document IDs and checksums are stable
    Evidence: .omo/evidence/task-6-run1.json

  Scenario: duplicate packet is skipped
    Tool:     bash
    Steps:    python scripts/legal_packet_ingest.py --dry-run --zip tests/fixtures/legal_packets/duplicate-two-files.zip --workspace legal-demo --collection demo-case --manifest .omo/evidence/task-6-duplicates.json && python scripts/assert_ingest_manifest.py .omo/evidence/task-6-duplicates.json --expect-duplicates 1
    Expected: exit 0 and manifest marks one duplicate skipped
    Evidence: .omo/evidence/task-6-duplicates.json
  ```

  Commit: YES | Message: `feat(ingest): add continuous legal packet driver` | Files: [scripts/legal_packet_ingest.py, scripts/assert_ingest_manifest.py, tests/unit/test_legal_packet_ingest.py, tests/fixtures/legal_packets/**]

- [ ] 7. Implement ontology-constrained extraction configuration

  What to do: Wire the debt-collection ontology into OntoRAG extraction, tune selector thresholds for noisy Korean OCR/table text, ensure entity URI normalization is stable across documents, and emit extracted facts plus ontology version/provenance metadata.
  Must NOT do: Do not widen extraction by allowing classes/properties outside the selected ontology subset unless explicitly configured and tested.

  Parallelization: Can parallel: YES | Wave 2 | Blocks: [8, 11, 12] | Blocked by: [1, 2, 3]

  References (executor has NO interview context - be exhaustive):
  - API/Type: `trustgraph-flow/trustgraph/extract/kg/ontology/extract.py:55` - Main OntoRAG processor class.
  - Pattern:  `trustgraph-flow/trustgraph/extract/kg/ontology/extract.py:109` - Processor registers config handler for type `ontology`.
  - Pattern:  `trustgraph-flow/trustgraph/extract/kg/ontology/extract.py:121` - Selector settings include top_k, similarity_threshold, and bypass_selector_below.
  - Pattern:  `trustgraph-flow/trustgraph/extract/kg/ontology/extract.py:211` - Ontology config updates are versioned by workspace.
  - Pattern:  `trustgraph-flow/trustgraph/extract/kg/ontology/extract.py:321` - Selector chooses ontology subset per chunk.
  - Pattern:  `trustgraph-flow/trustgraph/extract/kg/ontology/extract.py:341` - Extraction uses prompt `extract-with-ontologies`.
  - Pattern:  `trustgraph-flow/trustgraph/extract/kg/ontology/extract.py:361` - Extracted, ontology, and provenance triples are combined.
  - API/Type: `trustgraph-flow/trustgraph/extract/kg/ontology/ontology_loader.py:125` - Loader validates circular inheritance and property domains/ranges.
  - API/Type: `trustgraph-flow/trustgraph/extract/kg/ontology/ontology_selector.py:75` - Selector picks relevant subsets from text segments.
  - API/Type: `trustgraph-flow/trustgraph/extract/kg/ontology/triple_converter.py:151` - Converter enforces relationship domain/range.
  - Risk:     `docs/tech-specs/ontology-extract-phase-2.md:67` - Current prompt/URI handling has known URI loss and inconsistent ID risks.

  Acceptance criteria (agent-executable only):
  - [ ] `python -m pytest tests/unit/test_legal_ontology_extraction.py -q | tee .omo/evidence/task-7-tests.txt` exits 0.
  - [ ] `python scripts/run_ontology_extraction_fixture.py --ontology ontology/debt-collection/v1/ontology.json --input tests/fixtures/legal_packets/sample-ocr.md --out .omo/evidence/task-7-triples.json` exits 0.
  - [ ] Output triples include ontology version, source chunk URI, and no fallback `https://trustgraph.ai/ontology/<id>#<lost-name>` URI where a declared URI exists.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: legal OCR sample extracts ontology-valid triples
    Tool:     bash
    Steps:    python scripts/run_ontology_extraction_fixture.py --ontology ontology/debt-collection/v1/ontology.json --input tests/fixtures/legal_packets/sample-ocr.md --out .omo/evidence/task-7-sample-triples.json && python scripts/assert_triples.py .omo/evidence/task-7-sample-triples.json --require-class DebtClaim --require-class Debtor --require-provenance --require-ontology-version
    Expected: exit 0 and extracted triples pass domain/range validation
    Evidence: .omo/evidence/task-7-sample-triples.json

  Scenario: hallucinated property is rejected
    Tool:     bash
    Steps:    python scripts/run_ontology_extraction_fixture.py --ontology ontology/debt-collection/v1/ontology.json --input tests/fixtures/legal_packets/hallucinated-property.md --out .omo/evidence/task-7-hallucinated.json 2>&1 | tee .omo/evidence/task-7-hallucinated-error.txt
    Expected: exit 0 and output contains zero triples for undeclared property plus a quarantine warning
    Evidence: .omo/evidence/task-7-hallucinated-error.txt
  ```

  Commit: YES | Message: `feat(extract): constrain legal packet facts to ontology` | Files: [ontology/debt-collection/v1/**, config/flows/**, prompts/**, scripts/run_ontology_extraction_fixture.py, scripts/assert_triples.py, tests/unit/test_legal_ontology_extraction.py, tests/fixtures/legal_packets/**]

- [ ] 8. Implement StopGate evaluator service

  What to do: Implement a service and CLI that runs StopGate rules over collection-scoped graph/SPARQL queries, returns allow/block/review, records evidence triples in the retrieval/audit graph, and emits machine-readable reasons. Integrate gates before agent final answer and before any MCP/tool-service operation marked external-action.
  Must NOT do: Do not run external-action tools when StopGate state is missing, stale, failed, or from a different ontology/rule version.

  Parallelization: Can parallel: YES | Wave 2 | Blocks: [10, 11, 12] | Blocked by: [3, 4, 7]

  References (executor has NO interview context - be exhaustive):
  - API/Type: `trustgraph-base/trustgraph/api/flow.py:1005` - Flow SPARQL query method.
  - API/Type: `trustgraph-mcp/trustgraph/mcp_server/mcp.py:739` - MCP SPARQL tool uses query, collection, limit, flow, workspace.
  - Pattern:  `trustgraph-flow/trustgraph/agent/react/service.py:141` - Agent tool configuration reloads per workspace.
  - Pattern:  `trustgraph-flow/trustgraph/agent/react/service.py:319` - Agent request path has session ID and collection context.
  - Pattern:  `trustgraph-flow/trustgraph/agent/react/tools.py:11` - KnowledgeQueryImpl already forwards explainability events to agent responses.
  - Pattern:  `docs/tech-specs/query-time-explainability.md:65` - Explainability events stream while query executes.
  - Pattern:  `docs/tech-specs/query-time-explainability.md:72` - Explain messages carry explain ID, graph, and triples inline.
  - External: `https://www.law.go.kr/법령/채권의공정한추심에관한법률` - Collection conduct StopGate anchor.

  Acceptance criteria (agent-executable only):
  - [ ] `python -m pytest tests/unit/test_stopgate_evaluator.py tests/integration/test_stopgate_agent_gate.py -q | tee .omo/evidence/task-8-tests.txt` exits 0.
  - [ ] `python -m trustgraph.cli.evaluate_stopgate --rules config/stopgates/debt-collection.v1.json --collection demo-case --case-id fixture-case --mode answer --mock-graph tests/fixtures/stopgates/pass-readonly.json | tee .omo/evidence/task-8-cli-pass.json` exits 0 and outputs `allow`.
  - [ ] Blocked external-action scenario returns non-zero and writes no external-action event.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: StopGate allows sourced answer mode
    Tool:     bash
    Steps:    python -m trustgraph.cli.evaluate_stopgate --rules config/stopgates/debt-collection.v1.json --collection demo-case --case-id fixture-case --mode answer --mock-graph tests/fixtures/stopgates/pass-readonly.json | tee .omo/evidence/task-8-allow.json
    Expected: exit 0, JSON contains `"decision":"allow"`, and includes provenance rule evidence
    Evidence: .omo/evidence/task-8-allow.json

  Scenario: StopGate blocks external action on insolvency event
    Tool:     bash
    Steps:    python -m trustgraph.cli.evaluate_stopgate --rules config/stopgates/debt-collection.v1.json --collection demo-case --case-id fixture-case --mode external-action --mock-graph tests/fixtures/stopgates/insolvency-event.json 2>&1 | tee .omo/evidence/task-8-insolvency-block.json; test ${PIPESTATUS[0]} -ne 0
    Expected: JSON contains `"decision":"block"` and rule id `insolvency_check_required`
    Evidence: .omo/evidence/task-8-insolvency-block.json
  ```

  Commit: YES | Message: `feat(stopgate): enforce legal gates over graph evidence` | Files: [trustgraph-flow/**/stopgate*, trustgraph-cli/trustgraph/cli/evaluate_stopgate.py, config/stopgates/**, tests/unit/test_stopgate_evaluator.py, tests/integration/test_stopgate_agent_gate.py]

- [ ] 9. Implement ontology version publish/promote/rollback workflow

  What to do: Add commands/scripts to package ontology JSON, Turtle labels, StopGate registry, prompts, extraction settings, and migration notes into a versioned release manifest. Support publish to config, promote to workspace/flow, rollback by version, and evidence that facts extracted under old versions remain queryable with their original version.
  Must NOT do: Do not delete or overwrite old ontology releases. Do not silently re-extract existing cases without explicit migration.

  Parallelization: Can parallel: YES | Wave 2 | Blocks: [11] | Blocked by: [1, 3, 5]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `trustgraph-flow/trustgraph/extract/kg/ontology/extract.py:126` - Processor tracks config versions per workspace.
  - Pattern:  `trustgraph-flow/trustgraph/extract/kg/ontology/extract.py:276` - Config version is updated after ontology reload.
  - API/Type: `trustgraph-cli/trustgraph/cli/load_turtle.py:38` - Turtle loader parses RDF with `rdflib`.
  - API/Type: `trustgraph-cli/trustgraph/cli/put_kg_core.py:63` - KG core upload path stores triples/embeddings/library metadata/blobs.
  - API/Type: `trustgraph-cli/trustgraph/cli/load_kg_core.py:17` - KG core load targets flow and collection.
  - Risk:     `docs/tech-specs/knowledge-core-completeness.md:16` - Existing core export/import may lose provenance/named graph/source material.
  - Risk:     `docs/tech-specs/knowledge-core-completeness.md:35` - Complete core goal is self-contained triples, embeddings, provenance, and source attribution.
  - External: `https://www.w3.org/TR/rdf11-concepts/` - RDF datasets/named graphs for version snapshots.

  Acceptance criteria (agent-executable only):
  - [ ] `python scripts/package_ontology_release.py ontology/debt-collection/v1 --out .omo/evidence/task-9-release-manifest.json` exits 0.
  - [ ] Manifest includes ontology version, config version target, StopGate version, prompt version, schema checksum, migration note, and rollback pointer.
  - [ ] `python -m pytest tests/unit/test_ontology_release_workflow.py -q | tee .omo/evidence/task-9-tests.txt` exits 0.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: ontology release manifest is reproducible
    Tool:     bash
    Steps:    python scripts/package_ontology_release.py ontology/debt-collection/v1 --out .omo/evidence/task-9-release-a.json && python scripts/package_ontology_release.py ontology/debt-collection/v1 --out .omo/evidence/task-9-release-b.json && diff -u .omo/evidence/task-9-release-a.json .omo/evidence/task-9-release-b.json | tee .omo/evidence/task-9-release-diff.txt
    Expected: diff exits 0 and manifest checksum is stable
    Evidence: .omo/evidence/task-9-release-a.json

  Scenario: rollback refuses unknown version
    Tool:     bash
    Steps:    python scripts/promote_ontology_release.py --workspace legal-demo --release does-not-exist --dry-run 2>&1 | tee .omo/evidence/task-9-unknown-version.txt; test ${PIPESTATUS[0]} -ne 0
    Expected: output contains "unknown release"
    Evidence: .omo/evidence/task-9-unknown-version.txt
  ```

  Commit: YES | Message: `feat(ontology): add release lifecycle workflow` | Files: [scripts/package_ontology_release.py, scripts/promote_ontology_release.py, ontology/debt-collection/**, tests/unit/test_ontology_release_workflow.py]

- [ ] 10. Implement MCP/Hermes tool surfaces

  What to do: Expose a narrow tool set for Hermes/MCP clients: `legal_packet_search`, `legal_packet_evidence`, `legal_stopgate_evaluate`, `legal_case_status`, and `legal_ontology_version`. Register tools through TrustGraph MCP or tool-service configuration with workspace-aware auth and safe argument schemas.
  Must NOT do: Do not expose raw graph write/admin/delete actions to Hermes by default. Do not assume Hermes code exists in this repo.

  Parallelization: Can parallel: YES | Wave 2 | Blocks: [11, 12] | Blocked by: [4, 5, 8]

  References (executor has NO interview context - be exhaustive):
  - API/Type: `trustgraph-mcp/trustgraph/mcp_server/mcp.py:337` - MCP server configures auth settings and token verifier.
  - API/Type: `trustgraph-mcp/trustgraph/mcp_server/mcp.py:365` - MCP server registers tools including graph RAG, agent, triples, SPARQL, GraphQL, config, KG core, flow, and document operations.
  - API/Type: `trustgraph-mcp/trustgraph/mcp_server/tg_socket.py:17` - One WebSocket manager per caller token preserves identity/workspace/capability scoping.
  - API/Type: `trustgraph-mcp/trustgraph/mcp_server/tg_socket.py:55` - Gateway auth is first-frame bearer token.
  - API/Type: `trustgraph-mcp/trustgraph/mcp_server/tg_socket.py:146` - WebSocket request envelope supports service, flow, request, and workspace override.
  - API/Type: `trustgraph-flow/trustgraph/agent/react/tools.py:86` - Agent-side `McpToolImpl` forwards configured arguments to MCP tool service.
  - API/Type: `trustgraph-flow/trustgraph/agent/mcp_tool/service.py:27` - MCP invoker registers config handler for type `mcp`.
  - API/Type: `trustgraph-flow/trustgraph/agent/mcp_tool/service.py:69` - External MCP call supports optional bearer auth token.
  - CLI:      `trustgraph-cli/trustgraph/cli/set_mcp_tool.py:26` - CLI stores MCP config including remote name, URL, and auth-token.
  - CLI:      `trustgraph-cli/trustgraph/cli/invoke_mcp_tool.py:17` - CLI invokes named MCP tool with JSON parameters.
  - External: `https://modelcontextprotocol.io/specification/2025-11-25/` - MCP tools/resources/prompts and security guidance.
  - External: `https://github.com/NousResearch/hermes-agent` - Hermes reference integration target; no local adapter found.

  Acceptance criteria (agent-executable only):
  - [ ] `python -m pytest tests/unit/test_legal_mcp_tools.py tests/integration/test_legal_mcp_stopgate.py -q | tee .omo/evidence/task-10-tests.txt` exits 0.
  - [ ] `tg-set-mcp-tool --id legal-stopgate --tool-url http://localhost:8088/mcp --auth-token test-token --api-url http://localhost:8088/ --workspace legal-demo` can be dry-run or mocked in test.
  - [ ] `tg-invoke-mcp-tool -n legal_stopgate_evaluate -P '{"case_id":"fixture-case","mode":"answer"}' -w legal-demo -f legal-demo-flow | tee .omo/evidence/task-10-invoke.txt` returns allow/block JSON in integration environment.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: MCP StopGate tool returns structured decision
    Tool:     bash
    Steps:    TRUSTGRAPH_WORKSPACE=legal-demo python -m pytest tests/integration/test_legal_mcp_stopgate.py::test_mcp_stopgate_evaluate_allows_readonly_answer -q | tee .omo/evidence/task-10-mcp-allow.txt
    Expected: exit 0 and test asserts structured JSON contains case_id, decision, rule_version, evidence_ids
    Evidence: .omo/evidence/task-10-mcp-allow.txt

  Scenario: MCP tool denies workspace override without permission
    Tool:     bash
    Steps:    TRUSTGRAPH_WORKSPACE=legal-demo python -m pytest tests/integration/test_legal_mcp_stopgate.py::test_mcp_workspace_override_denied -q | tee .omo/evidence/task-10-workspace-denied.txt
    Expected: exit 0 and test asserts access denied, no cross-workspace data returned
    Evidence: .omo/evidence/task-10-workspace-denied.txt
  ```

  Commit: YES | Message: `feat(mcp): expose guarded legal packet tools` | Files: [trustgraph-mcp/**/legal*, trustgraph-flow/**/legal*, config/mcp/**, tests/unit/test_legal_mcp_tools.py, tests/integration/test_legal_mcp_stopgate.py]

- [ ] 11. Build end-to-end legal packet evidence harness

  What to do: Build a full E2E harness that ingests the local OCR archive, normalizes/inventories it, loads a small controlled subset into a legal demo workspace/collection, extracts ontology facts, runs StopGates, invokes MCP tools, and captures evidence artifacts for every step.
  Must NOT do: Do not require a human to inspect the app or manually confirm correctness. Legal human review must be represented as a machine-readable state.

  Parallelization: Can parallel: YES | Wave 3 | Blocks: [F1-F4] | Blocked by: [6, 7, 8, 9, 10]

  References (executor has NO interview context - be exhaustive):
  - Test:     `TESTS.md:99` - Basic test execution uses pytest.
  - Test:     `TEST_STRATEGY.md:7` - Test framework is pytest + pytest-asyncio.
  - Test:     `TEST_STRATEGY.md:48` - Mock external services, not core transformations.
  - Test:     `TEST_STRATEGY.md:68` - Unit/integration/contract test categories.
  - Pattern:  `docs/tech-specs/extraction-flows.md:13` - End-to-end flow is librarian -> decoder -> chunker -> extraction -> triples/contexts/rows.
  - Pattern:  `docs/tech-specs/extraction-flows.md:182` - Triples schema carries metadata and named graph field.
  - Pattern:  `docs/tech-specs/extraction-flows.md:199` - EntityContexts carry source chunk IDs.
  - Pattern:  `docs/tech-specs/extraction-flows.md:223` - Embeddings generation follows entity contexts and chunks.

  Acceptance criteria (agent-executable only):
  - [ ] `bash scripts/run_legal_packet_e2e.sh --fixture tests/fixtures/legal_packets/e2e-mini.zip --evidence-dir .omo/evidence/task-11 | tee .omo/evidence/task-11-e2e.txt` exits 0.
  - [ ] Evidence directory contains ingest manifest, normalized docs, extracted triples, provenance trace, StopGate decisions, MCP response, and audit log.
  - [ ] `python scripts/assert_e2e_evidence.py .omo/evidence/task-11 --require-provenance --require-stopgate --require-mcp | tee .omo/evidence/task-11-assert.txt` exits 0.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: mini legal packet runs through full pipeline
    Tool:     bash
    Steps:    bash scripts/run_legal_packet_e2e.sh --fixture tests/fixtures/legal_packets/e2e-mini.zip --workspace legal-demo --collection demo-case --evidence-dir .omo/evidence/task-11-mini | tee .omo/evidence/task-11-mini.txt
    Expected: exit 0 and evidence includes triples.json, provenance.json, stopgate-answer.json, mcp-stopgate.json
    Evidence: .omo/evidence/task-11-mini.txt

  Scenario: malformed packet is quarantined without graph writes
    Tool:     bash
    Steps:    bash scripts/run_legal_packet_e2e.sh --fixture tests/fixtures/legal_packets/malformed.zip --workspace legal-demo --collection demo-case --evidence-dir .omo/evidence/task-11-malformed 2>&1 | tee .omo/evidence/task-11-malformed.txt; test ${PIPESTATUS[0]} -ne 0
    Expected: output contains "quarantined"; evidence contains quarantine.json and no triples.json
    Evidence: .omo/evidence/task-11-malformed.txt
  ```

  Commit: YES | Message: `test(legal): add end-to-end packet evidence harness` | Files: [scripts/run_legal_packet_e2e.sh, scripts/assert_e2e_evidence.py, tests/fixtures/legal_packets/**, tests/integration/test_legal_packet_e2e.py]

- [ ] 12. Harden observability, audit, and failure quarantine

  What to do: Add metrics/logging/evidence for ingest latency, OCR quality, extraction confidence, ontology version, StopGate allow/block/review counts, cross-workspace denials, MCP invocation outcomes, and quarantine reasons. Ensure all high-risk failures fail closed.
  Must NOT do: Do not log secrets, bearer tokens, raw resident numbers, account numbers, or full unredacted documents.

  Parallelization: Can parallel: YES | Wave 3 | Blocks: [F1-F4] | Blocked by: [6, 7, 8, 10]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `docs/tech-specs/tool-group.md:326` - Tool-group metrics include requests, availability, filtered tools, transitions, and security counters.
  - Pattern:  `trustgraph-mcp/trustgraph/mcp_server/tg_socket.py:12` - Token cache keys hash tokens instead of storing raw secrets in map keys.
  - Pattern:  `trustgraph-mcp/trustgraph/mcp_server/tg_socket.py:27` - Caller bearer token must not be logged, persisted, or shared.
  - Pattern:  `trustgraph-flow/trustgraph/chunking/recursive/chunker.py:53` - Existing Prometheus histogram pattern for chunk size.
  - Pattern:  `docs/tech-specs/extraction-time-provenance.md:78` - Provenance supports debugging extraction quality.
  - Pattern:  `docs/tech-specs/extraction-time-provenance.md:86` - Provenance supports deletion/right-to-be-forgotten tracing.

  Acceptance criteria (agent-executable only):
  - [ ] `python -m pytest tests/unit/test_legal_audit_redaction.py tests/integration/test_legal_metrics.py -q | tee .omo/evidence/task-12-tests.txt` exits 0.
  - [ ] `python scripts/run_legal_packet_e2e.sh --fixture tests/fixtures/legal_packets/e2e-mini.zip --evidence-dir .omo/evidence/task-12 --emit-metrics | tee .omo/evidence/task-12-e2e.txt` exits 0 and emits metrics.
  - [ ] `python scripts/assert_no_sensitive_logs.py .omo/evidence/task-12 --patterns resident_number,account_number,bearer_token | tee .omo/evidence/task-12-log-redaction.txt` exits 0.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: metrics and audit are emitted without secrets
    Tool:     bash
    Steps:    python scripts/assert_legal_audit.py .omo/evidence/task-12 --require-metrics stopgate_blocks_total,legal_ingest_documents_total,legal_quarantine_total --forbid-secret-patterns | tee .omo/evidence/task-12-audit.txt
    Expected: exit 0 and all required metrics exist with no forbidden secret patterns
    Evidence: .omo/evidence/task-12-audit.txt

  Scenario: backend timeout fails closed
    Tool:     bash
    Steps:    python -m pytest tests/integration/test_legal_metrics.py::test_stopgate_timeout_blocks_external_action -q | tee .omo/evidence/task-12-timeout.txt
    Expected: exit 0 and test asserts decision is block/review, not allow
    Evidence: .omo/evidence/task-12-timeout.txt
  ```

  Commit: YES | Message: `feat(observability): audit guarded legal ontology flows` | Files: [trustgraph-flow/**/legal*, scripts/assert_no_sensitive_logs.py, scripts/assert_legal_audit.py, tests/unit/test_legal_audit_redaction.py, tests/integration/test_legal_metrics.py]

## Final verification wave (MANDATORY - after all implementation tasks)
> Runs in PARALLEL. ALL must APPROVE. Surface results to the caller and wait for an explicit "okay" before declaring complete.
- [ ] F1. Plan compliance audit - every task done, every acceptance criterion met
- [ ] F2. Code quality review - diagnostics clean, idioms match, no dead code
- [ ] F3. Real manual QA - every QA scenario executed with evidence captured
- [ ] F4. Scope fidelity - nothing extra shipped beyond Must-Have, nothing Must-NOT-Have introduced

## Commit strategy
- One logical change per commit. Conventional Commits (`<type>(<scope>): <subject>` body + footer).
- Atomic: every commit builds and passes tests on its own.
- No "WIP" / "fix typo squash later" commits on the final branch - clean up before merge.
- Reference the plan file path in the final commit footer: `Plan: .omo/plans/debt-collection-ontology-trustgraph.md`.

## Success criteria
- All Must-Have shipped; all QA scenarios pass with captured evidence; F1-F4 approved; commit history clean.
