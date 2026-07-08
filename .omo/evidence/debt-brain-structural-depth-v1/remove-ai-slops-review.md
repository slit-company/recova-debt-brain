# AI SLOP REMOVAL REPORT

Scope: explicit structural-depth caveat-hardening files.

Files:
- `trustgraph_legal/domain_workflow_integration.py`
- `trustgraph_legal/workflow_judgments.py`
- `trustgraph_legal/domain_decisions.py`
- `trustgraph_legal/domain_decision_resources.py`
- `trustgraph_legal/mcp_claim_domain_handlers.py`
- `tests/integration/legal_ontology/test_domain_ontology_v1_pipeline.py`
- `tests/unit/legal_ontology/test_workflow_judgments_v1.py`
- structural-depth evidence/docs touched by the caveat-hardening pass

Behavior Lock:
- Existing coverage: workflow judgment, domain decision, MCP decision, and integration pipeline tests were already present.
- Tests added: `test_claim_domain_workflow_support_survives_without_projection` and `test_review_items_scrub_nested_unsafe_support_fields`.
- Baseline status: RED was captured before fixes; GREEN after fixes.

Cleanup Plan:
- `trustgraph_legal/workflow_judgments.py`: simplify in place; category order missing-test -> defensive boundary scrub. Risk medium because it controls support-surface output safety.
- `trustgraph_legal/domain_decisions.py`: split oversized module by responsibility; category oversized-module. Risk medium because it is the public domain decision surface.
- `trustgraph_legal/mcp_claim_domain_handlers.py`: simplify typed JSON boundary; category over-defensive/type leakage. Risk low because behavior stays as JSON object validation.
- Integration and unit tests: add adversarial regression coverage without implementation-mirroring assertions.

Per-File Results:
- `trustgraph_legal/workflow_judgments.py`
  - Missing test: added nested unsafe support-signal test that fails when nested raw/contact/filing/path/balance fields leak through review items.
  - Defensive boundary scrub: replaced shallow key filtering with recursive JSON-compatible scrubbing for unsafe review item keys.
  - Skipped: did not remove the advisory-only fallback or support-surface ordering because those are behavior, not slop.
- `trustgraph_legal/domain_decisions.py`
  - Oversized module: extracted resource loading, version validation, JSON object loading, and typed resource bundle into `trustgraph_legal/domain_decision_resources.py`.
  - Public compatibility: `DomainDecisionError` remains importable from `trustgraph_legal.domain_decisions`.
  - Result: pure LOC dropped from 256 to 199.
- `trustgraph_legal/domain_decision_resources.py`
  - New responsibility module: resource paths, typed JSON loading, domain-source/finance-version checks, and resource bundle construction only.
  - Pure LOC: 96.
- `trustgraph_legal/mcp_claim_domain_handlers.py`
  - Typed JSON boundary: uses the same typed JSON loading pattern as the domain decision resource path; the prior `reportAny` warning is clean.

Quality Gates:
- Regression tests: PASS. Focused pytest 30 passed; regression pytest 18 passed; reopened boundary pytest 11 passed; domain/MCP boundary pytest 8 passed.
- Lint: PASS. Scoped ruff passed.
- Typecheck: PASS. Scoped basedpyright returned 0 errors, 0 warnings, 0 notes.
- Compile: PASS. `python3 -m compileall trustgraph_legal tests/unit/legal_ontology tests/integration/legal_ontology`.
- Static/security scan: PASS for scoped structural-depth deliverables and live direct/MCP outputs; broad older docs still contain out-of-scope environment variable names only.

Critical Review:
- Safety: PASS. Recursive scrub preserves safe structured fields while removing unsafe payload keys at any depth.
- Behavior: PASS. Exact domain and MCP workflow stage/action/posture/remediation-loop outcomes still pass for all eight semireal scenarios.
- Quality: PASS. No scenario-id or expected-label branching was added to product code; oversized touched file is split below the 250 pure-LOC ceiling.

Issues Found & Fixed:
- Nested support signals could leak unsafe review item fields. Fixed with adversarial test plus recursive scrub.
- `domain_decisions.py` exceeded the 250 pure-LOC review ceiling. Fixed by extracting resource responsibilities.
- Caveat-hardening RED evidence was summary-only. Fixed by adding `caveat-hardening-red-transcript.txt`.

Net Impact:
- New source module: `trustgraph_legal/domain_decision_resources.py`.
- New adversarial unit test: nested unsafe support-signal scrub.
- `domain_decisions.py` pure LOC: 199.
- `workflow_judgments.py` pure LOC: 243.
- No new runtime dependency.

Remaining Risks / Deferred:
- Fully stripped support cannot recover exact workflow semantics from missing information; it intentionally falls back to conservative advisory-only evidence completion.
- System `python3` lacks pytest; uv runner tests passed with explicit dependencies.

Final Status: CLEAN
