# debt-collection-ontology - Work Plan

## TL;DR (For humans)
**What you'll get:** TrustGraph 위에 올라가는 `채권추심 사건 온톨로지`와, 새 법률 문서가 계속 들어와도 사건 그래프와 법률 체크가 갱신되는 **agent-agnostic MCP 도메인 두뇌 서버**를 만든다. 어떤 에이전트든 이 MCP 서버에 붙어서 사건 구조, 증거, StopGate, 다음 실행 전제조건을 질의한다.

**Why this approach:** 이 레포는 이미 ontology config, OntoRAG, provenance, document ingest, MCP 서버를 갖고 있다. 그래서 코어를 크게 갈아엎기보다, 채권추심 전용 ontology, ingest registry, case graph, deterministic StopGate engine, domain MCP contract를 얇게 얹는 것이 가장 안전하다.

**What it will NOT do:** 사람용 SaaS UX, 특정 에이전트 전용 플러그인, 자동 법률대리/제출 실행기를 만들지 않는다. LLM이 뽑은 사실만으로 법률 결론을 내리지 않는다. 법령과 규칙을 클라이언트 에이전트의 native memory에만 저장하지 않는다.

**Effort:** Large
**Risk:** High - 법률/개인정보/집행행위가 걸린 도메인이라 provenance, governance state, rule versioning이 실패하면 제품 신뢰가 깨진다.
**Finalized architecture decisions:** v0 범위는 “모든 법”이 아니라 “채권추심 및 집행 사건 패킷”이다. MCP는 **단일 domain brain server + tool group/scope 분리**로 시작한다. 사건 식별은 **`case_packet_id` 중심 hybrid evidence key 모델**로 간다. 법령/규칙은 **curated versioned rule source**로 시작한다. MCP는 **판단/전제조건/근거만 반환하고 실행하지 않는다**.

Your next move: 이 계획을 구현하려면 `$start-work .omo/plans/debt-collection-ontology.md`로 넘기면 된다. Full execution detail follows below.

---

> TL;DR (machine): Large/High plan to add a Korean debt-collection ontology package, continuous ingest registry, case graph builder, StopGate engine, agent-agnostic MCP domain server tools, and regression evaluation on OCR legal packets.

## Scope
### Finalized Architecture Decisions
- **MCP server shape:** start with one `debt-collection-brain-mcp` service and separate capabilities by tool group/scope: `read`, `ingest`, `graph`, `stopgate`, `governance`, `admin`. Physical server split is deferred until scale or security boundaries require it.
- **Case identity model:** create an internal `case_packet_id` as the canonical ID and attach evidence keys including `court_case_number`, `claim_id`, `enforcement_title_id`, `party_identity_key`, and `document_hash`. Merging must be confidence-based, not name-only.
- **Rule source model:** v0 uses curated, versioned legal rule sources with `rule_id`, `statute_ref`, `effective_date`, `condition`, `decision`, `source_url`, and `version`. Automated law ingest/diff is deferred.
- **Action boundary:** MCP tools return `decision`, `recommended_action`, `required_preconditions`, `blocked_reasons`, `risk_flags`, and `source_refs`. They do not file, send, collect, contact, or execute irreversible business actions.

### Must have
- `recova-debt-collection` ontology config in TrustGraph JSON format.
- Domain modules for parties, identity evidence, claims, amounts, assignment, succession, enforcement title, court procedure, attachment targets, exemptions, priority, insolvency/credit recovery, asset evidence, operational ledger, document provenance, legal checks, and StopGates.
- OCR markdown ingest lane for `/Users/cosmos/dev/ocr/MinerU/work/legal_ocr_20260630/legal_docs_markdown.zip`.
- Document registry with `document_id`, source hash, source path, OCR version, extractor version, ontology version, prompt version, review status, confidence, and provenance pointers.
- Case graph builder that resolves documents into case-level facts: debtor, creditor, third-party debtor, guarantor, successor, claim amount, enforcement title, attachment target, legal action history, recovery ledger, costs, and StopGate facts.
- Hybrid identity resolver that produces `case_packet_id` and stores all supporting evidence keys, confidence, and merge/reject reasons.
- Deterministic legal check engine. It must return `가능`, `불가능`, or `보류`, plus reason, source evidence, missing evidence, risk flags, and next action.
- Agent-facing MCP tools that hide raw graph complexity and expose domain operations through stable machine-readable contracts.
- Tool group/scope enforcement for the single MCP domain brain server.
- Curated rule-source registry for v0 legal rules.
- Regression/evaluation suite over representative OCR fixtures plus synthetic adversarial documents.
- Governance/review queues for unknown document types, low-confidence extractions, legal-risk rule states, and ontology candidate promotion. These queues are service contracts, not a human UI requirement.

### Must NOT have (guardrails, anti-slop, scope boundaries)
- Must not implement final legal advice, filing automation, or irreversible enforcement actions inside the domain brain server. The server reports action prerequisites and risk states; execution belongs to external agents/tools.
- Must not put raw resident IDs, addresses, phone numbers, or bank/account data into logs, prompts, screenshots, or final reports.
- Must not treat any client agent's native memory as the legal source of truth.
- Must not fine-tune or modify a specific agent runtime for v0.
- Must not create multiple physical MCP services in v0 unless a concrete security boundary requires it.
- Must not merge cases on a single weak key such as name, phone number, or one OCR'd case number.
- Must not fetch or auto-update statutes into production rules without curated review/version promotion in v0.
- Must not bypass TrustGraph provenance or store extracted facts without source document/chunk references.
- Must not accept a new ontology version into production without regression reprocessing and review.
- Must not weaken extractor validation to “make more triples appear”.

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: TDD for validators, classifiers, rule engine, and MCP contracts; tests-after for CLI ingest smoke because it depends on the implemented entrypoint.
- Evidence root: `.omo/evidence/debt-collection-ontology/`.
- Unit tests: ontology schema validation, URI/property consistency, document classifier, field extractor, case resolver, StopGate rules.
- Integration tests: ingest 10 fixed OCR markdown fixtures, build case graph, query triples, run StopGate engine, call MCP tools.
- Real-surface proof: run the implemented CLI against a small OCR fixture set and call the MCP domain tools with `curl` or MCP client, capturing JSON responses and source evidence.

## Execution strategy
### Parallel execution waves
> Target 5-8 todos per wave. Fewer than 3 (except the final) means you under-split.
- Wave 1: domain contract and ontology foundation.
- Wave 2: ingest, extraction, and case graph assembly.
- Wave 3: legal StopGate engine and agent-facing MCP domain tools.
- Wave 4: MCP server contract, governance workflow, regression suite, and documentation.

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1 | none | 2, 3, 4, 5, 6, 7, 8 | none |
| 2 | 1 | 3, 5, 6, 7 | 4 |
| 3 | 1, 2 | 5, 6, 7, 8 | 4 |
| 4 | 1 | 5, 8 | 2, 3 |
| 5 | 2, 3, 4 | 6, 7, 8, 9 | none |
| 6 | 5 | 7, 8, 9 | none |
| 7 | 5, 6 | 9, 10 | 8 |
| 8 | 5, 6 | 9, 10 | 7 |
| 9 | 7, 8 | 10 | none |
| 10 | 9 | final verification | none |

## Todos
> Implementation + Test = ONE todo. Never separate.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->
- [x] 1. Lock the domain contract, server boundary, and fixture map
  What to do / Must NOT do: Create `docs/product/debt-collection-ontology/domain-contract.md` that defines v0 document types, entity roles, fact categories, StopGate categories, confidence levels, PII handling rules, the single MCP domain brain server shape, tool groups/scopes, hybrid `case_packet_id` identity model, curated rule-source policy, and non-execution boundary. Create `tests/fixtures/legal-ocr/manifest.json` that references a copied/minimized representative subset from the OCR markdown zip. Do not copy full PII-heavy raw documents into git; redact or synthesize where needed.
  Parallelization: Wave 1 | Blocked by: none | Blocks: 2, 3, 4, 5, 6, 7, 8
  References (executor has NO interview context - be exhaustive): `README.md:18-24`, `README.md:47-58`, `README.md:71-89`, `.omo/evidence/debt-collection-ontology-findings.md`
  Acceptance criteria (agent-executable): `python3 -m json.tool tests/fixtures/legal-ocr/manifest.json` exits 0; `rg -n "resident|주민등록번호|[0-9]{6}-[0-9]{7}" docs/product/debt-collection-ontology tests/fixtures/legal-ocr` finds no unredacted PII.
  QA scenarios (name the exact tool + invocation): happy: `python3 scripts/legal_ontology/check_fixture_manifest.py tests/fixtures/legal-ocr/manifest.json` prints `PASS manifest`; failure: add a temp manifest entry missing `document_type` and verify the same command exits nonzero with `missing document_type`. Evidence `.omo/evidence/debt-collection-ontology/task-1-manifest.txt`.
  Commit: Y | `docs(legal-ontology): define debt collection domain contract`

- [x] 2. Add the v0 TrustGraph ontology config
  What to do / Must NOT do: Add `resources/ontologies/recova-debt-collection.json` in TrustGraph ontology JSON shape. Include modules/classes/properties for Party and Identity, Claim and Amount, Assignment and Succession, Enforcement Title and Procedure, Attachment Target, Exemption and Priority, Insolvency and Credit Recovery, Asset Evidence, Operational Ledger, Document Provenance, Legal Check and StopGate. Keep identifiers kebab-case. Do not add laws as unstructured comments only; model law/rule source as versioned evidence classes/properties.
  Parallelization: Wave 1 | Blocked by: 1 | Blocks: 3, 5, 6, 7
  References: `docs/tech-specs/ontology.md:36-130`, `trustgraph-flow/trustgraph/extract/kg/ontology/ontology_loader.py:1-220`, `.omo/evidence/debt-collection-ontology-findings.md`
  Acceptance criteria: `python3 scripts/legal_ontology/validate_ontology.py resources/ontologies/recova-debt-collection.json` exits 0 and reports class/property counts; no validation issue for missing domain/range classes.
  QA scenarios: happy: run validator on the ontology and capture `PASS`; failure: run validator on a generated temp copy where one object property range points to `missing-class` and capture nonzero failure. Evidence `.omo/evidence/debt-collection-ontology/task-2-ontology-validator.txt`.
  Commit: Y | `feat(ontology): add recova debt collection ontology`

- [x] 3. Fix ontology extraction prompt semantics for legal IDs
  What to do / Must NOT do: Update ontology extraction prompt/template and tests so LLM output uses exact ontology class/property IDs, bilingual labels help comprehension, and source evidence instructions require document/chunk references. Preserve existing generic extraction behavior. Do not use examples that contradict ontology IDs.
  Parallelization: Wave 1 | Blocked by: 1, 2 | Blocks: 5, 6, 7, 8
  References: `ontology-prompt.md:1-52`, `docs/tech-specs/ontology-extract-phase-2.md`, `trustgraph-flow/trustgraph/extract/kg/ontology/extract.py:304-350`
  Acceptance criteria: existing ontology extraction tests pass; new prompt snapshot test proves examples use `recova-debt-collection#...` or exact configured IDs, not unprefixed generic names.
  QA scenarios: happy: `pytest tests/unit/test_ontology_prompt.py -q` captures expected legal ontology prompt section; failure: mutate a fixture to use an unconfigured predicate and verify parser rejects it. Evidence `.omo/evidence/debt-collection-ontology/task-3-prompt.txt`.
  Commit: Y | `fix(ontology): make extraction IDs source-safe`

- [x] 4. Build legal document ingest registry and OCR markdown loader
  What to do / Must NOT do: Add a domain ingest module or CLI that reads OCR markdown files/zips, computes content hashes, records registry metadata, redacts configured PII from logs, assigns or links `case_packet_id` using hybrid evidence keys, and calls TrustGraph `load_text`/librarian flow with workspace, collection, document title, tags, and metadata. Do not bypass TrustGraph document provenance.
  Parallelization: Wave 2 | Blocked by: 1 | Blocks: 5, 8
  References: `docs/tech-specs/extraction-flows.md:49-79`, `trustgraph-base/trustgraph/api/flow.py:766-910`, `trustgraph-mcp/trustgraph/mcp_server/mcp.py:1775-1835`, `trustgraph-flow/trustgraph/librarian/service.py:423-470`
  Acceptance criteria: `python3 -m trustgraph_legal.ingest --zip /Users/cosmos/dev/ocr/MinerU/work/legal_ocr_20260630/legal_docs_markdown.zip --dry-run --limit 5 --evidence .omo/evidence/debt-collection-ontology/task-4-dry-run.json` exits 0, outputs 5 registry records with hashes, versions, and no raw PII.
  QA scenarios: happy: dry-run zip ingest of 5 files returns deterministic registry JSON; failure: ingest the same file twice and verify duplicate status instead of duplicate insert. Evidence `.omo/evidence/debt-collection-ontology/task-4-ingest.txt`.
  Commit: Y | `feat(legal-ingest): add OCR markdown registry loader`

- [x] 5. Implement document classification and field extraction contracts
  What to do / Must NOT do: Implement deterministic+LLM-assisted classifiers for document buckets: attachment/collection order, payment order/judgment, service/finality/execution-clause, assignment/succession, identity evidence, insolvency/discharge/credit recovery, attachment target/priority, asset evidence, operational ledger, amount/interest calculation. Extract normalized fields with source spans. Do not accept classification without confidence and evidence.
  Parallelization: Wave 2 | Blocked by: 2, 3, 4 | Blocks: 6, 7, 8, 9
  References: `.omo/evidence/debt-collection-ontology-findings.md`, `docs/tech-specs/extraction-flows.md:146-168`, `docs/tech-specs/ontorag.md:232-244`
  Acceptance criteria: `pytest tests/unit/legal_ontology/test_document_classifier.py tests/unit/legal_ontology/test_field_extractors.py -q` exits 0; classifier reaches expected labels for fixture manifest.
  QA scenarios: happy: run classifier over fixture subset and capture per-file labels/confidence/source spans; failure: feed a low-signal unknown markdown and verify `unknown_doc_type` with review status. Evidence `.omo/evidence/debt-collection-ontology/task-5-classifier.json`.
  Commit: Y | `feat(legal-extract): classify debt collection documents`

- [x] 6. Build hybrid case graph resolver
  What to do / Must NOT do: Resolve extracted facts into case-level graph entities and edges: Case, CasePacket, Document, SourceSpan, Person, Organization, Creditor, Debtor, ThirdPartyDebtor, Guarantor, Successor, Claim, Amount, EnforcementTitle, CourtProcedure, AttachmentTarget, Asset, LedgerEvent, RecoveryTransaction, Cost, RuleFinding. Generate `case_packet_id` and attach `court_case_number`, `claim_id`, `enforcement_title_id`, `party_identity_key`, and `document_hash` as evidence keys with confidence and merge/reject reasons. Do not merge parties or cases on name alone.
  Parallelization: Wave 2 | Blocked by: 5 | Blocks: 7, 8, 9
  References: `docs/tech-specs/ontology.md:107-130`, `trustgraph-flow/trustgraph/extract/kg/ontology/extract.py:346-350`, `.omo/evidence/debt-collection-ontology-findings.md`
  Acceptance criteria: `pytest tests/unit/legal_ontology/test_case_graph_builder.py -q` exits 0; `python3 -m trustgraph_legal.case_graph --fixtures tests/fixtures/legal-ocr/manifest.json --out .omo/evidence/debt-collection-ontology/task-6-case-graph.json` writes a graph with document provenance on every non-derived fact.
  QA scenarios: happy: build a case graph from a fixture packet and verify debtor/creditor/claim/enforcement/attachment facts; failure: two similar debtor names without identity evidence must remain unresolved with `identity_uncertain`. Evidence `.omo/evidence/debt-collection-ontology/task-6-case-graph.txt`.
  Commit: Y | `feat(legal-graph): resolve extracted facts into case graphs`

- [x] 7. Implement deterministic legal StopGate engine
  What to do / Must NOT do: Add a versioned rule engine backed by curated v0 legal rule sources. It evaluates case graphs for enforcement title status, service/finality proof, assignment chain, succession, amount consistency, limitation, insolvency/discharge/credit recovery, attachment target/exemption/priority, identity uncertainty, duplicate enforcement, and credit-information/privacy purpose. Return decision, reasons, missing evidence, risk flags, source spans, rule IDs, statute refs, and effective dates. Do not use LLM-only legal conclusions or live auto-updated statutes in production rules.
  Parallelization: Wave 3 | Blocked by: 5, 6 | Blocks: 9, 10
  References: `.omo/evidence/debt-collection-ontology-findings.md`, `docs/tech-specs/ontorag.md:17-34`
  Acceptance criteria: `pytest tests/unit/legal_ontology/test_stop_gates.py -q` exits 0 and includes red/green fixtures for `discharge_proceeding_detected`, `missing_execution_clause`, `limitation_risk`, `exempt_claim_targeted`, `assignment_chain_broken`, `amount_mismatch`, and `identity_uncertain`.
  QA scenarios: happy: `python3 -m trustgraph_legal.check --case .omo/evidence/debt-collection-ontology/task-6-case-graph.json` returns `보류` with specific StopGates and source docs; failure: remove source span from a blocking fact and verify engine returns `invalid_fact_without_provenance`. Evidence `.omo/evidence/debt-collection-ontology/task-7-stopgates.json`.
  Commit: Y | `feat(legal-check): add debt collection stop gate engine`

- [x] 8. Add ontology candidate and reprocessing workflow
  What to do / Must NOT do: Add review queues/data files for unknown document types, low-confidence fields, proposed new classes/properties, ontology version promotion, and case reprocessing jobs. Wire config promotion so TrustGraph ontology updates trigger component refresh cleanly. Do not auto-promote ontology changes from one document.
  Parallelization: Wave 3 | Blocked by: 5, 6 | Blocks: 9, 10
  References: `trustgraph-flow/trustgraph/extract/kg/ontology/extract.py:211-302`, `docs/tech-specs/ontorag.md:220-244`
  Acceptance criteria: `pytest tests/unit/legal_ontology/test_ontology_governance.py -q` exits 0; a low-confidence unknown fixture creates an ontology candidate, review item, and reprocess plan without changing production ontology.
  QA scenarios: happy: run unknown fixture through ingest and capture candidate JSON; failure: attempt promotion without required approval metadata and verify rejection. Evidence `.omo/evidence/debt-collection-ontology/task-8-governance.txt`.
  Commit: Y | `feat(legal-ontology): add candidate promotion workflow`

- [x] 9. Build the single agent-agnostic MCP domain brain server tools
  What to do / Must NOT do: Add one domain MCP wrapper or extend TrustGraph MCP as `debt-collection-brain-mcp`, with tool groups/scopes: `read`, `ingest`, `graph`, `stopgate`, `governance`, `admin`. Expose purpose tools: `ingest_legal_document`, `ingest_ocr_markdown`, `get_ingest_status`, `classify_legal_document`, `extract_case_packet`, `get_case_graph`, `check_case_stop_gates`, `check_limitation_status`, `check_attachment_target_rules`, `summarize_case_ledger`, `recommend_next_action`, `list_unknown_document_types`, `review_extracted_fact`, `promote_ontology_candidate`, `reprocess_case`. These tools must be stable contracts for any external agent, not Hermes-specific methods. Do not expose raw PII by default and do not split into multiple physical MCP services in v0 without a documented security boundary.
  Parallelization: Wave 3 | Blocked by: 7, 8 | Blocks: 10
  References: `trustgraph-mcp/trustgraph/mcp_server/mcp.py:56-86`, `trustgraph-mcp/trustgraph/mcp_server/mcp.py:366-397`, `trustgraph-mcp/trustgraph/mcp_server/mcp.py:1775-1835`
  Acceptance criteria: `pytest tests/integration/legal_ontology/test_mcp_tools.py -q` exits 0; every tool returns JSON schema with `case_id`, `decision`, `risk_flags`, `source_refs`, and redacted outputs where applicable.
  QA scenarios: happy: `curl -i -H "Authorization: Bearer test" -H "Content-Type: application/json" <local-mcp-tool-call>` returns HTTP 200 and a `check_case_stop_gates` JSON body; failure: call without Bearer token and verify auth failure or gateway rejection. Evidence `.omo/evidence/debt-collection-ontology/task-9-mcp.txt`.
  Commit: Y | `feat(legal-mcp): expose debt collection domain brain tools`

- [x] 10. Add MCP server contract, regression eval, and integration notes
  What to do / Must NOT do: Add `docs/product/debt-collection-ontology/mcp-domain-server-contract.md`, sample generic MCP client configuration, evaluation runbook, and agent integration notes. Include tool schemas, tool group/scope matrix, expected JSON outputs, error states, source citation contract, redaction policy, hybrid case identity contract, curated rule-source contract, non-execution action boundary, and how a client agent should behave when graph/rules disagree with its own memory. Do not make the contract depend on Hermes-specific config or prompts.
  Parallelization: Wave 4 | Blocked by: 9 | Blocks: final verification
  References: `README.md:87-89`, `trustgraph-mcp/trustgraph/mcp_server/mcp.py:366-397`, `.omo/evidence/debt-collection-ontology-findings.md`
  Acceptance criteria: `python3 scripts/legal_ontology/evaluate_packet.py --fixtures tests/fixtures/legal-ocr/manifest.json --out .omo/evidence/debt-collection-ontology/task-10-eval.json` exits 0; docs contain MCP tool schemas, generic client config, machine-readable decision contract, source_refs examples, and memory-conflict policy.
  QA scenarios: happy: run one complete packet from ingest to MCP `recommend_next_action`, capture response with source_refs; failure: ask for a direct filing/execution command and verify the domain server returns a blocked/precondition response rather than executing. Evidence `.omo/evidence/debt-collection-ontology/task-10-mcp-contract.txt`.
  Commit: Y | `docs(legal-ontology): document MCP domain server contract`

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.
- [x] F1. Plan compliance audit: verify every Must Have is implemented and every Must NOT Have is enforced. Evidence `.omo/evidence/debt-collection-ontology/f1-plan-compliance.md`.
- [x] F2. Code quality review: run tests, lint/type checks available in this repo, and review no raw PII/log leakage. Evidence `.omo/evidence/debt-collection-ontology/f2-code-quality.md`.
- [x] F3. Real manual QA: execute a complete local flow on representative OCR markdown fixtures, then call MCP domain tools through the running MCP surface. Evidence `.omo/evidence/debt-collection-ontology/f3-real-qa.txt`.
- [x] F4. Scope fidelity: confirm no specific agent runtime modification, no auto legal filing inside the domain brain server, no unversioned legal memory, no person-facing UX dependency, and no unrelated TrustGraph refactor. Evidence `.omo/evidence/debt-collection-ontology/f4-scope-fidelity.md`.

## Commit strategy
- Commit each todo as one conventional commit after its tests and evidence pass.
- Do not commit OCR raw PII or local-only legal documents.
- Final branch can be one feature branch, e.g. `codex/debt-collection-ontology`.
- Suggested final PR title: `feat(legal-ontology): add debt collection MCP domain brain`.

## Success criteria
- A worker can run a documented ingest command against OCR markdown fixtures and get deterministic registry records.
- TrustGraph has a valid `recova-debt-collection` ontology config with source-safe classes/properties.
- Representative legal documents classify into the expected buckets with confidence and source spans.
- A case graph can be built with a canonical `case_packet_id`, hybrid evidence keys, and provenance on every extracted legal fact.
- StopGate checks return `가능`, `불가능`, or `보류` with reasons, missing evidence, risk flags, source refs, rule IDs, statute refs, and effective dates.
- Any MCP-compatible external agent can access the single scoped MCP domain brain server and receive domain-level answers without raw graph-query knowledge.
- MCP action recommendations contain preconditions and blocked reasons only; they do not execute filings, contacts, collections, or irreversible actions.
- Unknown document types and ontology changes enter a review/promotion path instead of silently changing production behavior.
