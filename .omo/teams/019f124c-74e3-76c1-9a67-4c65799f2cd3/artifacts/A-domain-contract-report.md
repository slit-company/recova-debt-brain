# A Domain Contract Report

Member: A / domain-contract
Worktree: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/019f124c-74e3-76c1-9a67-4c65799f2cd3/worktrees/A`
Branch: `team/019f124c-74e3-76c1-9a67-4c65799f2cd3/A`

## Changed Files

- `docs/product/debt-collection-ontology/domain-contract.md`

## Summary

Created the v0 debt-collection ontology domain-brain contract. It defines:

- document types and required document metadata
- entity roles and role assertion requirements
- fact categories with provenance expectations
- confidence levels
- StopGate categories and output contract
- PII minimization, redaction, hashing, and default-output rules
- single `debt-collection-brain-mcp` server shape
- MCP tool groups/scopes
- hybrid `case_packet_id` identity model
- curated versioned rule-source policy
- governance/review queue contract
- versioning and reprocessing expectations
- explicit non-execution boundary

The contract is Hermes-agnostic, agent-agnostic, and user-UX-agnostic.

## Commands and Results

- `git status --short`
  - Result: no output before editing; worktree was clean.
- `test -e .git; git status --short; git rev-parse --abbrev-ref HEAD; git rev-parse --show-toplevel`
  - Result: confirmed assigned worktree and branch.
- `test -f docs/product/debt-collection-ontology/domain-contract.md`
  - Result: PASS.
- `rg -n "<PII-scan-pattern>" docs/product/debt-collection-ontology || true`
  - Result: PASS; no matches.
- `git diff --cached --check`
  - Result: PASS after removing two Markdown hard-break trailing spaces before
    commit; no remaining whitespace errors.
- `wc -l docs/product/debt-collection-ontology/domain-contract.md`
  - Result: 529 lines.

## Risks and Notes

- This slice is a documentation contract only. It does not implement ontology JSON,
  ingest, classifiers, rule engine, MCP tools, or governance persistence.
- Later slices must map the contract's type IDs and queue IDs into concrete
  schemas/tests to avoid drift.
- Rule-source policy is intentionally curated/versioned for v0; live legal
  source ingestion remains deferred.
- Raw sensitive OCR values were not copied into the document or this report.
