# Final manual QA

- Real OCR assembly summary-only CLI produced 208 pages and 1 assemblies.
- Real OCR debtor context summary-only CLI produced 18 route candidates and 1 review item.
- MCP `list_debt_collection_tools` domain surface reports 21 tools, with debtor graph tools appended after the existing 16.
- MCP `list_debtor_route_candidates` was driven against the repo synthetic OCR fixture and returned 18 route candidates.
- MCP `explain_debtor_route_candidate` for `bank_account_attachment` returned status `missing_facts` with `no_direct_execution=True`.
- MCP outside-root graph path probe returned `path_outside_repo_root` without echoing file content or input path.
