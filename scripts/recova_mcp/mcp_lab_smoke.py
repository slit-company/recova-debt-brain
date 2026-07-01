from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[2]
for package_path in (
    REPO_ROOT,
    REPO_ROOT / "trustgraph-mcp",
    REPO_ROOT / "trustgraph-base",
):
    path = str(package_path)
    if path not in sys.path:
        sys.path.insert(0, path)

import httpx
from trustgraph_legal.lab_trace import (
    TraceInvocation,
    supabase_config_from_env,
    tool_trace_row,
    write_rows_to_supabase,
)

EXPECTED_TOOL_COUNT = 16
GENERIC_TOOL_NAMES = {
    "embeddings",
    "put_config",
    "load_document",
    "delete_kg_core",
}
EXECUTION_TOOL_NAMES = {
    "direct_file_court_document",
    "contact_debtor",
    "initiate_attachment",
    "collect_payment",
}


async def run_smoke(
    url: str,
    token: str,
    expect_auth_failure: bool,
) -> Dict[str, Any]:
    headers = {"Authorization": "Bearer {}".format(token)} if token else {}
    try:
        client_session = importlib.import_module("mcp").ClientSession
        streamable_http_client = importlib.import_module(
            "mcp.client.streamable_http"
        ).streamable_http_client
        async with httpx.AsyncClient(
            headers=headers,
            timeout=httpx.Timeout(30, read=60),
            follow_redirects=True,
        ) as http_client:
            async with streamable_http_client(
                url=url,
                http_client=http_client,
            ) as streams:
                read_stream, write_stream = streams[0], streams[1]
                async with client_session(read_stream, write_stream) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    tool_names = [tool.name for tool in tools.tools]
                    stopgate_arguments = {
                        "manifest_path": "tests/fixtures/legal-ocr/manifest.json"
                    }
                    stopgate = await session.call_tool(
                        "check_case_stop_gates",
                        stopgate_arguments,
                    )
    except Exception as exc:
        if expect_auth_failure:
            return {
                "status": "auth_rejected",
                "auth_failure": True,
                "error_type": type(exc).__name__,
            }
        raise

    if expect_auth_failure:
        raise RuntimeError("expected auth failure but MCP request succeeded")

    generic_tools = sorted(set(tool_names).intersection(GENERIC_TOOL_NAMES))
    execution_tools = sorted(set(tool_names).intersection(EXECUTION_TOOL_NAMES))
    stopgate_envelope = _content_json(stopgate.content)
    stopgate_result = _object(stopgate_envelope.get("result"))
    decision = str(stopgate_result.get("decision") or "")
    trace_status = _record_trace_if_configured(stopgate_arguments, stopgate_envelope)
    return {
        "status": "ok",
        "auth_failure": False,
        "tool_count": len(tool_names),
        "expected_tool_count": EXPECTED_TOOL_COUNT,
        "generic_tools": generic_tools,
        "execution_tools": execution_tools,
        "tools": tool_names,
        "decision": decision,
        "trace_status": trace_status,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test the Recova MCP lab.")
    parser.add_argument("--url", required=True)
    parser.add_argument("--token-env", default="MCP_LAB_BEARER_TOKEN")
    parser.add_argument("--out", required=True)
    parser.add_argument("--expect-auth-failure", action="store_true")
    args = parser.parse_args()

    token = "" if args.expect_auth_failure else os.environ.get(args.token_env, "")
    if not token and not args.expect_auth_failure:
        raise SystemExit("missing token env: {}".format(args.token_env))
    result = asyncio.run(run_smoke(args.url, token, args.expect_auth_failure))
    _validate_result(result, args.expect_auth_failure)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("PASS mcp_lab_smoke {}".format(result["status"]))


def _content_json(content: List[Any]) -> Dict[str, Any]:
    for item in content:
        text = getattr(item, "text", None)
        if isinstance(text, str):
            decoded = json.loads(text)
            if isinstance(decoded, dict):
                return decoded
    return {}


def _record_trace_if_configured(
    arguments: Dict[str, Any],
    envelope: Dict[str, Any],
) -> str:
    if not os.environ.get("SUPABASE_URL") or not os.environ.get(
        "SUPABASE_SERVICE_ROLE_KEY"
    ):
        return "not_recorded"
    row = tool_trace_row(
        TraceInvocation(
            tool_name="check_case_stop_gates",
            arguments=arguments,
            envelope=envelope,
            latency_ms=0,
        )
    )
    result = write_rows_to_supabase([row], supabase_config_from_env())
    return str(result.get("status") or "recorded")


def _object(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _validate_result(result: Dict[str, Any], expect_auth_failure: bool) -> None:
    if expect_auth_failure:
        if result.get("status") != "auth_rejected":
            raise RuntimeError("expected auth_rejected")
        return
    if result.get("tool_count") != EXPECTED_TOOL_COUNT:
        raise RuntimeError("unexpected tool_count")
    if result.get("generic_tools"):
        raise RuntimeError("generic tools exposed")
    if result.get("execution_tools"):
        raise RuntimeError("execution tools exposed")
    if result.get("decision") not in {"가능", "보류", "불가능"}:
        raise RuntimeError("missing Korean decision")


if __name__ == "__main__":
    main()
