# S final-eval-pack preflight

Member: S `final-eval-pack`
Thread: `codex://threads/019f36ec-8b52-7430-a61c-0ac57c722c09`
Date: 2026-07-06

## Status

Blocked for final Todo 15 evidence and commit until the leader confirms Todo 13 and Todo 14 are integrated.

This preflight created no final evidence files and made no commit.

## Current observations

- Worktree is ready: `/Users/cosmos/dev/ontology/trustgraph/.omo/teams/debtor-context-graph-v0-20260706/worktrees/S`.
- Branch is `team/debtor-context-graph-v0-20260706/S`.
- Current HEAD is `880cba38`, the same commit as local `master` at preflight time.
- Worktree status was clean before this artifact.
- Todo 11/12 are integrated in current master.
- `trustgraph_legal.mcp_domain.list_tools()` returns 21 tools, including the five debtor graph tools:
  - `assemble_debtor_documents`
  - `build_debtor_context_graph`
  - `get_debtor_graph_snapshot`
  - `list_debtor_route_candidates`
  - `explain_debtor_route_candidate`
- Outside-root MCP preflight probe returned `status=rejected` and `reason=path_outside_repo_root`.
- Local real OCR root exists; rough preflight count found 209 markdown/text-like files. Final evidence must rely on the summary-only pipeline output, not this rough count.
- Current S branch has Todo 13 test files present:
  - `tests/unit/legal_ontology/test_mcp_debtor_context_tools.py`
  - `tests/integration/legal_ontology/test_debtor_context_pipeline.py`
- Q reported Todo 13 ready for leader integration:
  - commit `836d2f46` on `team/debtor-context-graph-v0-20260706/Q`
  - report `Q-integration-contracts-report.md`
  - task-13 evidence under `.omo/evidence/debtor-context-graph-v0/task-13-*`
  - task-13 evidence/report keep local paths and token sentinels out
- Current S branch does not yet have Todo 14 docs:
  - missing `docs/product/debt-collection-ontology/debtor-context-graph-v0.md`
- R reported Todo 14 ready for leader integration:
  - commit `5fe665a1` on `team/debtor-context-graph-v0-20260706/R`
  - report `R-debtor-docs-report.md`
  - docs use `$RECOVA_REAL_OCR_ROOT` / redacted placeholders for real OCR examples
  - task-14 PII/path scan reports `NO_FINDINGS`
- Current S branch still needs leader-confirmed integration of the Q and R commits before Todo 15 final evidence.
- `git diff --check` was clean before this artifact.

## Final evidence rules

- Write final files only under `.omo/evidence/debtor-context-graph-v0/`.
- Use summary-only OCR commands.
- Do not persist raw OCR text, classifier excerpts, source OCR paths, phone numbers, resident-registration-number patterns, account-like identifiers, or full source document content.
- Evidence JSON may include counts, statuses, schema versions, route ids, redaction flags, and aggregate review/unknown totals.
- Evidence JSON must not include source OCR file paths. If a source label is necessary, use an alias such as `real_ocr_corpus`.
- Commit only final Todo 15 evidence files after leader confirmation.

## Required final files

- `final-real-ocr-assembly-summary.json`
- `final-real-ocr-debtor-summary.json`
- `final-route-candidate-summary.json`
- `final-mcp-tool-list.json`
- `final-mcp-path-failure.json`
- `final-focused-pytest.txt`
- `final-json-tool.txt`
- `final-pii-scan.txt`
- `final-diff-check.txt`
- `final-dirty-scope.txt`
- `final-real-ocr-eval.json`
- `final-evidence-summary.md`

## Final command checklist

Run only after leader confirms Todo 13 and Todo 14 are integrated.

```bash
cd /Users/cosmos/dev/ontology/trustgraph/.omo/teams/debtor-context-graph-v0-20260706/worktrees/S
git status --short --branch
git merge --ff-only master
mkdir -p .omo/evidence/debtor-context-graph-v0
export EVIDENCE=.omo/evidence/debtor-context-graph-v0
export REAL_OCR_ROOT=/Users/cosmos/dev/ocr/MinerU/work/legal_ocr_20260630
```

Assembly summary:

```bash
/opt/homebrew/bin/python3 -m trustgraph_legal.document_assembly \
  --ocr-root "$REAL_OCR_ROOT" \
  --out "$EVIDENCE/final-real-ocr-assembly-summary.json" \
  --summary-only
```

Debtor graph summary:

```bash
/opt/homebrew/bin/python3 -m trustgraph_legal.debtor_context \
  --ocr-root "$REAL_OCR_ROOT" \
  --route-resources resources/legal_routes/debt_collection_routes_v0.json \
  --legal-sources resources/legal_rules/debt_collection_route_sources_v0.json \
  --out "$EVIDENCE/final-real-ocr-debtor-summary.json" \
  --summary-only
```

Focused tests:

```bash
/opt/homebrew/bin/python3 -m pytest \
  tests/unit/legal_ontology/test_document_assembly.py \
  tests/unit/legal_ontology/test_debtor_context.py \
  tests/unit/legal_ontology/test_route_candidates.py \
  tests/unit/legal_ontology/test_mcp_debtor_context_tools.py \
  tests/integration/legal_ontology/test_debtor_context_pipeline.py \
  tests/unit/legal_ontology/test_mcp_domain_tools.py \
  tests/integration/legal_ontology/test_mcp_tools.py \
  -q > "$EVIDENCE/final-focused-pytest.txt"
```

MCP tool list and outside-root path probe:

```bash
/opt/homebrew/bin/python3 - <<'PY'
import json
from pathlib import Path
from trustgraph_legal.mcp_domain import invoke_tool, list_tools

evidence = Path(".omo/evidence/debtor-context-graph-v0")
tools = list_tools()
tool_summary = {
    "schema_version": "recova-debtor-context-graph/final-eval-v1",
    "tool_count": len(tools),
    "tool_names": [tool["tool_name"] for tool in tools],
    "debtor_graph_tool_names": [
        tool["tool_name"] for tool in tools if tool["group"] == "debtor_graph"
    ],
}
(evidence / "final-mcp-tool-list.json").write_text(
    json.dumps(tool_summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
path_failure = invoke_tool(
    "get_debtor_graph_snapshot",
    {"graph_path": "/tmp/outside-debtor-graph.json"},
    Path.cwd(),
)
(evidence / "final-mcp-path-failure.json").write_text(
    json.dumps(path_failure, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY
```

Route candidate summary and final aggregate eval:

```bash
/opt/homebrew/bin/python3 - <<'PY'
import json
from pathlib import Path

evidence = Path(".omo/evidence/debtor-context-graph-v0")
assembly = json.loads((evidence / "final-real-ocr-assembly-summary.json").read_text())
debtor = json.loads((evidence / "final-real-ocr-debtor-summary.json").read_text())
tools = json.loads((evidence / "final-mcp-tool-list.json").read_text())

route_summary = {
    "schema_version": "recova-debtor-context-graph/final-route-summary-v1",
    "route_candidates": debtor.get("summary", {}).get("route_candidates", 0),
    "review_items": debtor.get("summary", {}).get("review_items", 0),
    "unknown_assemblies": debtor.get("summary", {}).get("unknown_assemblies", 0),
    "raw_text_included": debtor.get("pii_profile", {}).get("raw_text_included", False),
}
(evidence / "final-route-candidate-summary.json").write_text(
    json.dumps(route_summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)

final_eval = {
    "schema_version": "recova-debtor-context-graph/final-eval-v1",
    "corpus_alias": "real_ocr_corpus",
    "pages": assembly.get("summary", {}).get("pages", 0),
    "assemblies": assembly.get("summary", {}).get("assemblies", 0),
    "snapshots": debtor.get("summary", {}).get("snapshots", 0),
    "route_candidates": route_summary["route_candidates"],
    "review_items": route_summary["review_items"],
    "unknown_assemblies": route_summary["unknown_assemblies"],
    "mcp_tool_count": tools["tool_count"],
    "debtor_graph_tool_count": len(tools["debtor_graph_tool_names"]),
    "raw_text_included": False,
    "source_paths_included": False,
}
(evidence / "final-real-ocr-eval.json").write_text(
    json.dumps(final_eval, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY
```

JSON validation:

```bash
{
  for file in "$EVIDENCE"/final-*.json; do
    /opt/homebrew/bin/python3 -m json.tool "$file" >/dev/null
    printf 'VALID %s\n' "$file"
  done
} > "$EVIDENCE/final-json-tool.txt"
```

PII scan:

```bash
/opt/homebrew/bin/python3 - <<'PY'
import re
from pathlib import Path

evidence = Path(".omo/evidence/debtor-context-graph-v0")
pattern = re.compile(
    r"[0-9]{6}-[0-9]{7}"
    r"|(?:\+82[-.[:space:]]?)?0[0-9]{1,2}[-.[:space:]]?[0-9]{3,4}[-.[:space:]]?[0-9]{4}"
    r"|(" + "계좌|은행|입금|송금|acc" + "ount|ba" + "nk" + r").{0,24}[0-9]{2,6}[-.[:space:]][0-9]{2,6}[-.[:space:]][0-9]{2,8}"
    r"|" + "주민등록" + "번호"
)
findings = []
for path in sorted(evidence.glob("final-*")):
    if path.name == "final-pii-scan.txt":
        continue
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if pattern.search(line):
            findings.append(f"{path}:{lineno}")
if findings:
    (evidence / "final-pii-scan.txt").write_text("\n".join(findings) + "\n", encoding="utf-8")
    raise SystemExit(1)
(evidence / "final-pii-scan.txt").write_text("NO_FINDINGS\n", encoding="utf-8")
PY
```

Diff and dirty scope:

```bash
git diff --check > "$EVIDENCE/final-diff-check.txt"
{
  git status --short --branch
  printf '\nChanged files:\n'
  git diff --name-only
} > "$EVIDENCE/final-dirty-scope.txt"
```

Final evidence summary:

```bash
/opt/homebrew/bin/python3 - <<'PY'
import json
from pathlib import Path

evidence = Path(".omo/evidence/debtor-context-graph-v0")
final_eval = json.loads((evidence / "final-real-ocr-eval.json").read_text())
lines = [
    "# Final Debtor Context Graph v0 eval evidence",
    "",
    "- Corpus: real OCR corpus summary-only eval",
    f"- Pages: {final_eval['pages']}",
    f"- Assemblies: {final_eval['assemblies']}",
    f"- Snapshots: {final_eval['snapshots']}",
    f"- Route candidates: {final_eval['route_candidates']}",
    f"- Review items: {final_eval['review_items']}",
    f"- Unknown assemblies: {final_eval['unknown_assemblies']}",
    f"- MCP tools: {final_eval['mcp_tool_count']}",
    f"- Debtor graph MCP tools: {final_eval['debtor_graph_tool_count']}",
    "- Raw OCR text included: false",
    "- Source OCR paths included: false",
    "- PII scan: see final-pii-scan.txt",
]
(evidence / "final-evidence-summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
PY
```

Final commit only after all gates pass:

```bash
git add .omo/evidence/debtor-context-graph-v0/final-*
git commit -m "test(legal-graph): add debtor context eval evidence"
```

## Ready-to-run gate before final commit

- Leader confirms Todo 13 integrated.
- Leader confirms Todo 14 integrated.
- S branch fast-forwards to current master.
- `docs/product/debt-collection-ontology/debtor-context-graph-v0.md` exists.
- Focused tests pass.
- JSON validation passes.
- PII scan writes `NO_FINDINGS`.
- `final-real-ocr-eval.json` reports `raw_text_included=false` and `source_paths_included=false`.
- `final-mcp-tool-list.json` reports exactly 21 tools.
- `final-mcp-path-failure.json` rejects outside-root path without echoing sensitive paths or file contents.
- `final-dirty-scope.txt` shows only final Todo 15 evidence files before commit.
