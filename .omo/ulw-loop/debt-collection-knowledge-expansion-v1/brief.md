Execute .omo/plans/debt-collection-knowledge-expansion-v1.md end-to-end as a HEAVY evidence-bound knowledge expansion, while preserving unrelated deployment/runbook dirty files.

Aggregate constraints:
- Do not deploy MCP, do not run remote MCP smoke, do not update client-facing remote setup docs.
- Do not implement real debt-collection execution, filing, debtor contact, payment demand, seizure initiation, ledger mutation, or production storage mutation.
- Keep local 25-tool MCP source contract intact: existing 21 tools first, four claim-domain tools appended.
- Use Korean-law MCP for legal source discovery/evidence, but freeze deterministic tests/resources to static JSON.
- For finance judgment, inspect available MCP surfaces first; if no dedicated finance MCP exists, use official/public web sources plus Korean-law MCP and freeze adopted source refs.
- Keep all evidence PII/path safe.

Goal 1: Legal and finance source research foundation.
Success criteria:
C1: Produce a PII-safe static legal-source audit for remaining needs_legal_review refs with Korean-law MCP evidence and impacted route/workflow/StopGate/decision surfaces. Evidence: .omo/evidence/debt-collection-knowledge-expansion-v1/task-1-legal-source-audit.json plus failure evidence.
C2: Produce a finance-source channel decision proving which MCPs/sources are available and which official/public sources will be used for finance judgments. Evidence: .omo/evidence/debt-collection-knowledge-expansion-v1/task-6-finance-source-research.json.
C3: Regression: no remote deployment/runbook files are staged or committed for this goal. Evidence: git status/diff check transcript.

Goal 2: Scenario coverage and human-review contract foundation.
Success criteria:
C1: Produce scenario coverage inventory comparing current 9 synthetic scenarios against 32 routes, 19 families, six action packet types, and status coverage. Evidence: .omo/evidence/debt-collection-knowledge-expansion-v1/task-2-scenario-coverage.json plus duplicate/unknown-route failure proof.
C2: Define and validate a human-review operator workflow contract for action packets and governance records. Evidence: .omo/evidence/debt-collection-knowledge-expansion-v1/task-3-human-review-workflow.txt plus forbidden-field failure proof.
C3: Regression: action packets remain direct_execution_allowed=false and no debtor-contact/filing fields appear.

Goal 3: Resource and fixture expansion.
Success criteria:
C1: Replace or explicitly disposition remaining review-needed legal source records and prove validators/tests pass. Evidence: .omo/evidence/debt-collection-knowledge-expansion-v1/task-4-legal-source-happy.json and failure proof.
C2: Expand synthetic rare-case claim-domain fixtures for rare assets, insolvency/recovery, protected-property, inheritance, hidden assets, and finance ambiguity. Evidence: .omo/evidence/debt-collection-knowledge-expansion-v1/task-5-expanded-scenarios-happy.json and failure proof.
C3: Regression: existing v1 resources remain JSON-valid and local MCP tool order remains 25 tools with existing 21 first and four claim-domain tools appended.

Goal 4: Decision, StopGate, finance, and review regression hardening.
Success criteria:
C1: Strengthen finance/review regressions for disputed balance, payment allocation conflict, enforcement cost, assignment/succession, guarantee/surety, subrogation/reimbursement, operator rejection, and needs-more-evidence. Evidence: task-6 finance/review happy and failure JSON.
C2: Strengthen domain decision and StopGate integration for expanded knowledge; scenarios produce stable possible/review_required/blocked/missing_facts with traceable reasons. Evidence: task-7 domain-decision happy and failure JSON.
C3: Regression: no blockers are loosened to make scenarios possible; protected-property, stale source, and review-needed source cases remain review-safe.

Goal 5: Documentation, final eval, and acceptance review.
Success criteria:
C1: Update working log and operator/developer docs for knowledge expansion without remote setup docs. Evidence: task-8 docs smoke and PII/path evidence.
C2: Run final focused suite, JSON validation, final PII/path scan, local MCP order check, and final knowledge expansion eval. Evidence: final-knowledge-expansion-eval.json, final-legal-source-delta.json, final-scenario-coverage.json, final-pii-path-scan.txt.
C3: Final contract review accepts integrated state and confirms no deployment/runbook mutation and execution remains forbidden. Evidence: final-contract-review.md.
