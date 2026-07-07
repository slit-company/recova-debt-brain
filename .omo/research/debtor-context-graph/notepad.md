# Debtor Context Graph Research Notepad

Started: 2026-07-06 15:31 Asia/Seoul
Tier: HEAVY
Justification: New domain model and architecture planning for long-lived debtor context graphs, legal-source-grounded route ontology, OCR evidence mapping, and MCP-facing agent use.

## Skills
- `omo:ulw-loop`: explicit `ulw` request; evidence-led research and planning loop.
- `omo:ulw-plan`: architecture-scale planning before implementation; outcome is decision-complete plan input, not immediate code.
- `omo:ulw-research`: user requested deeper research using OCR, supplied MD route manual, and legal review before proceeding.

## Scope
- Analyze OCR folder `/Users/cosmos/dev/ocr/MinerU/work/legal_ocr_20260630`.
- Analyze supplied route manual `/Users/cosmos/Downloads/채권추심_장기채권_법조치_루트_총정리.md`.
- Use current TrustGraph/Recova source and MCP surface as implementation constraints.
- Attempt Korean-law MCP discovery; if unavailable, use official legal sources as fallback and record limitation.

## Success Criteria
1. OCR and current Recova MCP behavior are characterized with PII-safe evidence.
2. Long-term collection route manual is transformed into graph/ontology requirements.
3. Legal-source review identifies statutes/rule-source categories needed for graph and route ontology.
4. A concrete recommendation is produced for the next build plan: Debtor Context Graph v0 plus route/evidence/legal-source work.

## Initial Findings
- Current working tree has unrelated deployment docs/scripts and deployment evidence changes; avoid touching those.
- Dedicated `korean-law` MCP tool is not currently exposed by tool discovery; Recova Debt Brain MCP is exposed.
