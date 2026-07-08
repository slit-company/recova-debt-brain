# debt-brain-structural-depth-v1 - Work Plan

## TL;DR (For humans)
**What you'll get:** Recova will become better at collection-workflow judgment: it should identify where a case sits in the collection process, what the next practical move is, why a route is premature or ready, and what review/remediation loop is needed.

**Why this approach:** The center is not lawyer-like document handling. The center is collection operator know-how, with legal, evidence, finance, and StopGate checks acting as guardrails.

**What it will NOT do:** It will not deploy remotely, add public admin/write tools, contact debtors, file anything, mutate ledgers, or claim an authoritative balance.

**Effort:** Large
**Risk:** Medium - the main risk is accidentally making legal/evidence checks dominate the product instead of supporting workflow judgment.
**Decisions I made for you:** Preserve the current 25-tool local MCP surface and order; keep every new ambiguous law, evidence, finance, and conflict state in review/hold; use only PII-safe synthetic or semireal fixtures.

Your next move: approve execution with `$start-work` or ask for another interview round to refine the workflow taxonomy. Full execution detail follows below.

---

> TL;DR (machine): Large, medium-risk structural-depth wave adding a collection workflow judgment brain, evidence/finance/legal checkpoints, decision integration, fixture coverage, and deploy-readiness evidence without remote deployment.

## Scope
### Must have
- A first-class collection workflow judgment model that answers: current stage, operational posture, next best action, premature actions, missing inputs, review/remediation loop, and source-backed reasons.
- A versioned operator playbook resource that captures practical collection stages and next-action logic, not just legal route catalogs.
- Evidence quality/conflict checks that support workflow judgment without becoming the product center.
- Finance review bridge that lets fixture-only finance ambiguity influence workflow and route judgment without creating an authoritative balance.
- Legal precondition checkpoints for 시효, 집행권원, 송달, 확정, 집행문, and source approval as workflow blockers or review loops.
- Integration into the existing claim-domain decision output and MCP response envelope without changing the accepted 25-tool order.
- Semireal, no-PII scenario coverage that proves practical workflow behavior: premature litigation, evidence-completion loop, title-acquisition loop, asset-discovery loop, enforcement-ready case, low-yield monitoring, finance-reconciliation hold, insolvency/protected-asset hold.
- Evidence artifacts under `.omo/evidence/debt-brain-structural-depth-v1/`.

### Must NOT have (guardrails, anti-slop, scope boundaries)
- No remote MCP deployment, remote smoke, production service changes, or client-facing remote setup docs.
- No public admin MCP tools, public write tools, mutation tools, or change that removes/reorders the current local 25-tool surface.
- No direct execution of collection actions, court filings, debtor contact, seizure, payment demand, or production ledger mutation.
- No raw PII, raw OCR text, debtor contact payloads, filing destinations, court destination payloads, or local absolute paths in output evidence.
- No free-form LLM/web/legal-memory inference that clears StopGates; adopted legal facts must be static, reviewed resources.
- No authoritative balance calculation; finance remains fixture/review support only.
- No conflation of route status with StopGate decision semantics. Test them separately.

## Verification strategy
> Zero human intervention for verification; user approval is a planning/release gate, not a test substitute.
- Test decision: TDD for new deterministic engines/resources; tests-after only for docs/evidence packaging.
- Focused pytest:
  - `python3 -m pytest tests/unit/legal_ontology/test_operator_playbook_v1.py tests/unit/legal_ontology/test_workflow_judgments_v1.py tests/unit/legal_ontology/test_evidence_quality_v1.py tests/unit/legal_ontology/test_finance_claim_model_v1.py tests/unit/legal_ontology/test_domain_decision_engine_v1.py tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py`
- Regression pytest:
  - `python3 -m pytest tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py tests/unit/legal_ontology/test_stop_gates_domain_v1.py tests/unit/legal_ontology/test_route_decisions_v1.py tests/unit/legal_ontology/test_action_packets_v1.py`
- JSON validation:
  ```bash
  python3 - <<'PY'
from pathlib import Path
import json
roots = [Path("resources"), Path("tests/fixtures/claim-domain-v1"), Path(".omo/evidence/debt-brain-structural-depth-v1")]
paths = [path for root in roots if root.exists() for path in root.rglob("*.json")]
for path in paths:
    json.loads(path.read_text(encoding="utf-8"))
    print("OK", path)
print("JSON_VALIDATION_OK files={}".format(len(paths)))
PY
  ```
- Compile/type:
  - `python3 -m compileall trustgraph_legal tests/unit/legal_ontology tests/integration/legal_ontology`
  - existing typecheck command if present in repo scripts/evidence history.
- Safety scans:
  - PII/path scan over `.omo/evidence/debt-brain-structural-depth-v1/` and changed JSON/docs:
    ```bash
    python3 - <<'PY'
from pathlib import Path
import re
paths = []
for root in [Path(".omo/evidence/debt-brain-structural-depth-v1"), Path("docs/product/debt-collection-ontology"), Path("resources"), Path("tests/fixtures/claim-domain-v1")]:
    if root.exists():
        paths.extend(path for path in root.rglob("*") if path.is_file() and path.suffix in {".json", ".md", ".txt"})
patterns = {
    "absolute_user_path": re.compile("/" + "Users" + "/" + "slit"),
    "secret_env": re.compile(
        "MCP_LAB_" + "BEARER_TOKEN"
        + "|SUPABASE_" + "SERVICE_ROLE_KEY"
        + r"|Authorization\\s*:|Bearer\\s+[A-Za-z0-9._-]{12,}"
    ),
    "raw_payload": re.compile(r'"(?:raw_text|source_text|debtor_contact_payload|filing_destination|court_destination)"\\s*:\\s*(?!(?:false|null|\\[\\]|\\{\\}|""|0))'),
}
findings = []
for path in paths:
    text = path.read_text(encoding="utf-8", errors="ignore")
    for name, pattern in patterns.items():
        for match in pattern.finditer(text):
            findings.append((str(path), name, match.group(0)[:120]))
if findings:
    for finding in findings:
        print("FINDING", *finding)
    raise SystemExit(1)
print("NO_FINDINGS files={}".format(len(paths)))
PY
    ```
  - MCP tool-order smoke must still report 25 tools with existing 21 first and claim-domain tools appended as before:
    ```bash
    python3 - <<'PY'
from trustgraph_legal.mcp_domain import list_tools
from tests.utils.legal_mcp_support import CLAIM_DOMAIN_TOOL_SCOPES, EXPECTED_21_TOOL_NAMES
names = [str(tool["tool_name"]) for tool in list_tools()]
assert names[:21] == EXPECTED_21_TOOL_NAMES, names[:21]
assert names[21:] == list(CLAIM_DOMAIN_TOOL_SCOPES), names[21:]
assert len(names) == 25, len(names)
print("MCP_ORDER_OK count=25 tail={}".format(",".join(names[21:])))
PY
    ```
- Evidence: `.omo/evidence/debt-brain-structural-depth-v1/task-*.{txt,json,md}` plus `final-*`.

## Execution strategy
### Parallel execution waves
- Wave 1, foundations: Todo 1, Todo 3, Todo 4, Todo 5. Build independent support contracts: operator playbook, evidence checkpoint, finance bridge, legal checkpoint policy.
- Wave 2, brain integration: Todo 2, Todo 6, Todo 7, Todo 8. Build workflow judgment, wire decision/MCP output, expand scenarios, update docs/evidence.
- Final wave: F1-F4 run after all todos and must approve before the work is called complete.

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1. Operator playbook resource | none | 2, 7, 8 | 3, 4, 5 |
| 2. Workflow judgment engine | 1, 3, 4, 5 | 6, 7, 8 | none |
| 3. Evidence quality/conflict checkpoint | none | 2, 6, 7 | 1, 4, 5 |
| 4. Finance review bridge | none | 2, 6, 7 | 1, 3, 5 |
| 5. Legal precondition checkpoint policy | none | 2, 6, 7 | 1, 3, 4 |
| 6. Domain decision/MCP integration | 2, 3, 4, 5 | 8, final | 7 after 2 exists |
| 7. Semireal scenario expansion | 1, 2, 3, 4, 5 | 8, final | 6 after shared schema stabilizes |
| 8. Docs, evidence, deploy-readiness gate | 6, 7 | final | none |

## Todos
> Implementation + Test = ONE todo. Never separate.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->
- [x] 1. Define the collection operator playbook resource
  What to do / Must NOT do: Add a versioned repo-local playbook resource, likely `resources/workflows/debt_collection_operator_playbook_v1.json`, describing practical collection stages, operational postures, next-action types, premature-action reasons, remediation loops, and required checkpoint inputs. Add validator/tests in `tests/unit/legal_ontology/test_operator_playbook_v1.py`. Must not replace the existing workflow resource or legal route catalog.
  Parallelization: Wave 1 | Blocked by: none | Blocks: 2, 7, 8
  References: `.omo/drafts/debt-brain-structural-depth-v1.md`; `resources/workflows/debt_collection_workflow_v1.json`; `docs/product/debt-collection-ontology/claim-domain-ontology-v1.md:139`
  Acceptance criteria: `python3 -m pytest tests/unit/legal_ontology/test_operator_playbook_v1.py tests/unit/legal_ontology/test_workflow_v1.py`
  QA scenarios: validate playbook has stages for intake, evidence completion, title acquisition, asset discovery, execution route selection, enforcement-ready, monitoring, settlement/restructuring, insolvency/protected-asset review, closure. Evidence `.omo/evidence/debt-brain-structural-depth-v1/task-1-operator-playbook.txt`
  Commit: Y | feat(collection-brain): add operator playbook resource

- [x] 2. Build the workflow judgment engine
  What to do / Must NOT do: Add deterministic workflow judgment code, likely `trustgraph_legal/workflow_judgments.py`, returning `trustgraph-collection-workflow-judgment/v1` with stage, posture, next_best_actions, premature_actions, missing_inputs, review_items, remediation_loop, reasons, source_refs, pii_profile, and non_execution_semantics. It should consume claim-domain payload, route decisions, evidence checkpoints, finance review signals, legal checkpoints, and the operator playbook. Must not call an LLM or infer legal clearance from free text.
  Parallelization: Wave 2 | Blocked by: 1, 3, 4, 5 | Blocks: 6, 7, 8
  References: `trustgraph_legal/domain_decisions.py:74`; `trustgraph_legal/route_decisions.py:126`; `trustgraph_legal/domain_graph_adapter.py:46`; `.omo/drafts/debt-brain-structural-depth-v1.md`
  Acceptance criteria: `python3 -m pytest tests/unit/legal_ontology/test_workflow_judgments_v1.py`
  QA scenarios: one case routes to evidence completion, one to title acquisition, one to asset discovery, one to enforcement-ready advisory packet, one to low-yield monitoring. Evidence `.omo/evidence/debt-brain-structural-depth-v1/task-2-workflow-judgments.json`
  Commit: Y | feat(collection-brain): add workflow judgment engine

- [x] 3. Add evidence quality and conflict checkpoints as workflow inputs
  What to do / Must NOT do: Add `trustgraph_legal/evidence_quality.py` or equivalent deterministic module that summarizes fact-handle source quality, directness, confidence, staleness, placeholder refs, missing provenance, derived facts, and contradictory fact values. It should output review/hold signals for the workflow engine and route decisions. Must not become a free-form document analysis engine and must not include raw excerpts.
  Parallelization: Wave 1 | Blocked by: none | Blocks: 2, 6, 7
  References: `trustgraph_legal/domain_graph_adapter_handles.py:82`; `trustgraph_legal/domain_graph_adapter_case_graph.py:54`; `docs/product/debt-collection-ontology/claim-domain-ontology-v1.md:70`
  Acceptance criteria: `python3 -m pytest tests/unit/legal_ontology/test_evidence_quality_v1.py tests/unit/legal_ontology/test_domain_graph_adapter_v1.py`
  QA scenarios: source-backed direct proof passes, placeholder source ref creates review item, stale/low-confidence fact creates review item, conflicting payment/title facts create hold. Evidence `.omo/evidence/debt-brain-structural-depth-v1/task-3-evidence-quality.json`
  Commit: Y | feat(collection-brain): add evidence quality checkpoints

- [x] 4. Bridge fixture finance review into workflow judgment
  What to do / Must NOT do: Add a small adapter/bridge, likely in `trustgraph_legal/finance_claims.py` or `trustgraph_legal/finance_review_bridge.py`, that maps finance calculation review items into workflow judgment signals such as finance_reconciliation_needed, disputed_balance_hold, unsupported_interest_review, payment_allocation_review. Must preserve fixture-only/non-authoritative semantics and never emit collectable balance authority.
  Parallelization: Wave 1 | Blocked by: none | Blocks: 2, 6, 7
  References: `trustgraph_legal/finance_claims.py:175`; `tests/unit/legal_ontology/test_finance_claim_model_v1.py`
  Acceptance criteria: `python3 -m pytest tests/unit/legal_ontology/test_finance_claim_model_v1.py tests/unit/legal_ontology/test_finance_workflow_bridge_v1.py`
  QA scenarios: clean fixture can support advisory readiness, ambiguous allocation causes finance reconciliation loop, disputed amount prevents authoritative balance and creates review item. Evidence `.omo/evidence/debt-brain-structural-depth-v1/task-4-finance-bridge.json`
  Commit: Y | feat(collection-brain): bridge finance review into workflow judgment

- [x] 5. Model legal precondition checkpoints as workflow gates
  What to do / Must NOT do: Convert 시효, 집행권원, 송달, 확정, 집행문, source approval, insolvency/protected-asset checks into explicit workflow checkpoint outputs that the workflow judgment engine can use. Reuse existing StopGate/domain resources where possible; add only static reviewed resource fields when needed. Must not weaken StopGate behavior or clear blockers from memory/web/LLM analysis.
  Parallelization: Wave 1 | Blocked by: none | Blocks: 2, 6, 7
  References: `trustgraph_legal/stop_gates_domain_v1.py:98`; `resources/legal_rules/debt_collection_stopgate_domain_v1.json`; `tests/unit/legal_ontology/test_stop_gates_domain_v1.py`
  Acceptance criteria: `python3 -m pytest tests/unit/legal_ontology/test_stop_gates_domain_v1.py tests/unit/legal_ontology/test_legal_workflow_checkpoints_v1.py`
  QA scenarios: missing title routes to title-acquisition loop, missing service/finality/execution clause routes to legal-precondition review, limitation ambiguity routes to review/hold, protected-asset signal blocks enforcement readiness. Evidence `.omo/evidence/debt-brain-structural-depth-v1/task-5-legal-checkpoints.json`
  Commit: Y | feat(collection-brain): expose legal preconditions as workflow gates

- [x] 6. Integrate workflow judgment into claim-domain decision output and MCP envelope
  What to do / Must NOT do: Extend `evaluate_claim_domain_decision` and the existing MCP handler so decision output includes workflow judgment and operator-facing next steps while keeping existing route_decisions, review_items, action_packet_candidates, source_refs, pii_profile, and non_execution_semantics stable. Must preserve 25-tool order and avoid adding public admin/write tools.
  Parallelization: Wave 2 | Blocked by: 2, 3, 4, 5 | Blocks: 8, final
  References: `trustgraph_legal/domain_decisions.py:74`; `trustgraph_legal/mcp_claim_domain_handlers.py:80`; `tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py`
  Acceptance criteria: `python3 -m pytest tests/unit/legal_ontology/test_domain_decision_engine_v1.py tests/unit/legal_ontology/test_mcp_domain_ontology_v1_tools.py tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py`
  QA scenarios: MCP decision response includes workflow_judgment, current tool order remains 25, old route/action fields remain backward-compatible, unsafe fields remain absent. Evidence `.omo/evidence/debt-brain-structural-depth-v1/task-6-domain-integration.json`
  Commit: Y | feat(collection-brain): integrate workflow judgment into domain decisions

- [x] 7. Expand semireal workflow scenario fixtures
  What to do / Must NOT do: Extend or add PII-safe fixtures under `tests/fixtures/claim-domain-v1/` to cover practical operator judgment, not just route status. Include scenario IDs and expected workflow stage/action/posture. Must not use raw real debtor data, raw OCR, contact payloads, filing destinations, or local paths.
  Parallelization: Wave 2 | Blocked by: 1, 2, 3, 4, 5 | Blocks: 8, final
  References: `tests/fixtures/claim-domain-v1/synthetic_claim_states.json`; `tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py`; `.omo/evidence/debt-collection-knowledge-expansion-v1/final-scenario-coverage.json`
  Acceptance criteria: `python3 -m pytest tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py tests/unit/legal_ontology/test_workflow_judgments_v1.py`
  QA scenarios: at least eight named scenarios: premature litigation, evidence completion, title acquisition, asset discovery, enforcement-ready, monitoring/low yield, finance reconciliation, insolvency/protected-asset hold. Evidence `.omo/evidence/debt-brain-structural-depth-v1/task-7-scenario-coverage.json`
  Commit: Y | test(collection-brain): expand workflow judgment scenarios

- [x] 8. Update docs, evidence, and local deploy-readiness gate
  What to do / Must NOT do: Update product/operator docs and working log to explain the new workflow judgment brain, support-layer relationship, evidence artifacts, and deferred deployment boundary. Run final validation suite, JSON validation, compile/type checks, PII/path scan, and MCP tool-order smoke. Must not claim remote deployment or remote smoke occurred.
  Parallelization: Wave 2 | Blocked by: 6, 7 | Blocks: final
  References: `docs/product/debt-collection-ontology/claim-domain-ontology-v1.md`; `.omo/notes/recova-brain-working-log.md`; `.omo/drafts/debt-brain-structural-depth-v1.md`
  Acceptance criteria: focused/regression test commands in Verification strategy pass; JSON validation prints `JSON_VALIDATION_OK`; compile/type passes or pre-existing gaps are documented; PII/path scan prints `NO_FINDINGS`; MCP tool-order smoke prints `MCP_ORDER_OK count=25`.
  QA scenarios: final docs describe workflow judgment as center; deployment boundary states local deploy-ready only; final evidence files exist under `.omo/evidence/debt-brain-structural-depth-v1/final-*`. Evidence `.omo/evidence/debt-brain-structural-depth-v1/final-summary.md`
  Commit: Y | docs(collection-brain): document workflow judgment brain

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit release okay before declaring the phase complete.
- [x] F1. Plan compliance audit: run `git diff --name-only` and inspect touched paths; reject if `deploy/`, remote runbooks, public admin/write surfaces, production ledger/storage mutation, raw PII fixtures, or tool-order removals appear. Expected evidence line: `PLAN_COMPLIANCE_APPROVED no_remote_deploy no_admin no_write no_pii no_ledger`.
- [x] F2. Code quality review: run focused/regression pytest commands, JSON validation command, `python3 -m compileall trustgraph_legal tests/unit/legal_ontology tests/integration/legal_ontology`, and typecheck if available. Inspect new modules for deterministic structured parsing and narrow public contracts. Expected evidence line: `CODE_QUALITY_APPROVED tests=pass json=pass compile=pass`.
- [x] F3. Real manual QA: run the local decision surface against representative fixture scenarios:
  ```bash
  python3 - <<'PY'
from tests.utils.claim_domain_pipeline_support import load_bundle, scenario_list, adapter_payload
from trustgraph_legal.domain_decisions import DomainDecisionRequest, evaluate_claim_domain_decision
bundle = load_bundle()
scenarios = {scenario.scenario_id: scenario for scenario in scenario_list(bundle)}
required = [
    "premature_litigation_review",
    "evidence_completion_loop",
    "title_acquisition_loop",
    "asset_discovery_loop",
    "enforcement_ready_review",
    "monitoring_low_yield",
    "finance_reconciliation_hold",
    "insolvency_protected_asset_hold",
]
missing = [scenario_id for scenario_id in required if scenario_id not in scenarios]
assert not missing, missing
for scenario_id in required:
    scenario = scenarios[scenario_id]
    decision = evaluate_claim_domain_decision(DomainDecisionRequest(claim_domain_payload=adapter_payload(scenario), workflow_state=scenario.workflow_state, route_ids=(scenario.route_id,), finance_review_codes=scenario.finance_review_codes))
    judgment = decision.get("workflow_judgment")
    assert isinstance(judgment, dict), scenario_id
    assert judgment.get("current_stage"), scenario_id
    assert judgment.get("next_best_actions") or judgment.get("remediation_loop"), scenario_id
    assert judgment.get("non_execution_semantics") == "advisory_only_human_review_required", scenario_id
print("MANUAL_QA_APPROVED scenarios={}".format(len(required)))
PY
  ```
- [x] F4. Scope fidelity: run a text/output contract check that proves the final story is collection workflow intelligence first and legal/evidence/finance are support layers:
  ```bash
  python3 - <<'PY'
from pathlib import Path
import json
doc = Path("docs/product/debt-collection-ontology/claim-domain-ontology-v1.md").read_text(encoding="utf-8")
working_log = Path(".omo/notes/recova-brain-working-log.md").read_text(encoding="utf-8")
sample_paths = list(Path(".omo/evidence/debt-brain-structural-depth-v1").glob("*workflow*.json"))
assert "workflow judgment" in doc.lower() or "워크플로우 판단" in doc, "docs must name workflow judgment"
assert "collection workflow" in doc.lower() or "추심 워크플로우" in doc, "docs must center collection workflow"
assert "legal" in doc.lower() and "evidence" in doc.lower() and "finance" in doc.lower(), "docs must name support layers"
assert "workflow judgment" in working_log.lower() or "워크플로우 판단" in working_log, "working log must record workflow judgment"
assert sample_paths, "sample workflow judgment evidence JSON is required"
for path in sample_paths:
    payload = json.loads(path.read_text(encoding="utf-8"))
    encoded = json.dumps(payload, ensure_ascii=False).lower()
    assert "workflow_judgment" in encoded or "current_stage" in encoded, path
    assert "next_best" in encoded or "remediation_loop" in encoded, path
    assert "advisory_only_human_review_required" in encoded, path
print("SCOPE_FIDELITY_APPROVED workflow_first support_layers_ok samples={}".format(len(sample_paths)))
PY
  ```

## Commit strategy
- Commit each completed todo or tightly related pair once its tests/evidence pass.
- Keep commits on the current branch unless the user requests a branch.
- Do not amend prior accepted commits.
- Commit messages should use `feat(collection-brain): ...`, `test(collection-brain): ...`, or `docs(collection-brain): ...`.

## Success criteria
- Recova can return a structured workflow judgment for claim-domain cases.
- The workflow judgment explains case stage, next best operational move, premature actions, missing inputs, review/remediation loop, reasons, and source refs.
- Legal, evidence, finance, and StopGate layers support workflow judgment without becoming the product identity.
- Ambiguous law, evidence conflict, finance ambiguity, missing legal preconditions, and protected/insolvency states hold or require review.
- Existing decision/action packet fields remain backward-compatible.
- Local MCP tool surface remains 25 tools with accepted ordering.
- No remote deployment occurs.
- Final evidence proves focused tests, regression tests, JSON validation, compile/type checks, PII/path scan, and local deploy-readiness.
