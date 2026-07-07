#!/usr/bin/env sh
set -eu

OUT="${1:-/tmp/recova-vercel-mcp}"

rm -rf "$OUT"
mkdir -p "$OUT/api" "$OUT/resources" "$OUT/tests/fixtures"

cp deploy/vercel-mcp/api/mcp.py "$OUT/api/mcp.py"
cp deploy/vercel-mcp/vercel.json "$OUT/vercel.json"
cp deploy/vercel-mcp/requirements.txt "$OUT/requirements.txt"
cp deploy/vercel-mcp/pyproject.toml "$OUT/pyproject.toml"

cp -R trustgraph_legal "$OUT/trustgraph_legal"
cp -R resources/legal_rules "$OUT/resources/legal_rules"
cp -R resources/ontologies "$OUT/resources/ontologies"
cp -R tests/fixtures/legal-ocr "$OUT/tests/fixtures/legal-ocr"

find "$OUT" -type d -name __pycache__ -prune -exec rm -rf {} +
find "$OUT" -type f -name '*.pyc' -delete

printf '%s\n' "recova_vercel_bundle=$OUT"
