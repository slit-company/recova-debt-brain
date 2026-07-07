from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trustgraph_legal.mcp_domain import invoke_tool, list_tools

JsonObject = Dict[str, Any]
PROTOCOL_VERSION = "2025-06-18"
SERVER_INFO = {
    "name": "recova-debt-brain-lab",
    "title": "Recova Debt Collection Brain",
    "version": "lab-vercel-v1",
}


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        self._send_empty(204, extra_headers=_cors_headers())

    def do_GET(self) -> None:
        if not _authorized(self.headers.get("Authorization", "")):
            self._send_auth_required()
            return
        self._send_json(
            405,
            {
                "error": "method_not_allowed",
                "message": "Use POST for Streamable HTTP MCP JSON-RPC calls.",
            },
            extra_headers={"Allow": "POST, OPTIONS"},
        )

    def do_DELETE(self) -> None:
        if not _authorized(self.headers.get("Authorization", "")):
            self._send_auth_required()
            return
        self._send_empty(204)

    def do_POST(self) -> None:
        if not _authorized(self.headers.get("Authorization", "")):
            self._send_auth_required()
            return
        try:
            payload = self._read_json()
        except ValueError as exc:
            self._send_json(400, _jsonrpc_error(None, -32700, str(exc)))
            return

        status, response = _handle_payload(payload)
        if response is None:
            self._send_empty(status)
            return
        self._send_json(status, response)

    def _read_json(self) -> JsonObject:
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8") if raw else "{}")
        except json.JSONDecodeError as exc:
            raise ValueError("invalid JSON body") from exc
        if not isinstance(payload, dict):
            raise ValueError("JSON-RPC payload must be an object")
        return payload

    def _send_auth_required(self) -> None:
        self._send_json(
            401,
            {"error": "invalid_token", "error_description": "Authentication required"},
            extra_headers={
                "WWW-Authenticate": 'Bearer error="invalid_token", error_description="Authentication required"',
            },
        )

    def _send_empty(
        self,
        status: int,
        extra_headers: Optional[JsonObject] = None,
    ) -> None:
        self.send_response(status)
        for key, value in {**_cors_headers(), **(extra_headers or {})}.items():
            self.send_header(key, str(value))
        self.end_headers()

    def _send_json(
        self,
        status: int,
        payload: JsonObject,
        extra_headers: Optional[JsonObject] = None,
    ) -> None:
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode(
            "utf-8"
        )
        self.send_response(status)
        headers = {
            "Content-Type": "application/json",
            "Content-Length": str(len(encoded)),
            **_cors_headers(),
            **(extra_headers or {}),
        }
        for key, value in headers.items():
            self.send_header(key, str(value))
        self.end_headers()
        self.wfile.write(encoded)


def _handle_payload(payload: JsonObject) -> Tuple[int, Optional[JsonObject]]:
    if "jsonrpc" not in payload:
        return 400, _jsonrpc_error(payload.get("id"), -32600, "Missing jsonrpc")
    method = str(payload.get("method") or "")
    request_id = payload.get("id")

    if method == "initialize":
        return 200, _jsonrpc_result(
            request_id,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": SERVER_INFO,
                "instructions": "Use Recova tools only for debt-collection domain reasoning, StopGate checks, source refs, and review-safe recommendations.",
            },
        )
    if method == "notifications/initialized":
        return 202, None
    if method == "ping":
        return 200, _jsonrpc_result(request_id, {})
    if method == "tools/list":
        return 200, _jsonrpc_result(request_id, {"tools": _mcp_tools()})
    if method == "tools/call":
        return 200, _jsonrpc_result(request_id, _call_tool(payload.get("params")))
    return 200, _jsonrpc_error(request_id, -32601, "Method not found")


def _call_tool(params: Any) -> JsonObject:
    if not isinstance(params, dict):
        params = {}
    name = str(params.get("name") or "")
    arguments = params.get("arguments")
    if not isinstance(arguments, dict):
        arguments = {}
    envelope = invoke_tool(name, arguments, ROOT)
    text = json.dumps(envelope, ensure_ascii=False, sort_keys=True)
    return {
        "content": [{"type": "text", "text": text}],
        "structuredContent": envelope,
        "isError": bool(envelope.get("warnings") and _result_status(envelope) == "unknown_tool"),
    }


def _mcp_tools() -> list[JsonObject]:
    tools = []
    for item in list_tools():
        tools.append(
            {
                "name": item["tool_name"],
                "title": item["tool_name"],
                "description": item.get("description", ""),
                "inputSchema": item.get("input_schema", {"type": "object"}),
                "outputSchema": item.get("output_schema"),
                "annotations": {
                    "readOnlyHint": item.get("group") in {"read", "graph", "stopgate"},
                    "destructiveHint": False,
                    "idempotentHint": True,
                },
            }
        )
    return tools


def _authorized(header: str) -> bool:
    expected = os.environ.get("MCP_LAB_BEARER_TOKEN", "")
    if not expected:
        return False
    prefix = "Bearer "
    return header.startswith(prefix) and header[len(prefix) :] == expected


def _result_status(envelope: JsonObject) -> str:
    result = envelope.get("result")
    if not isinstance(result, dict):
        return ""
    status = result.get("status")
    return status if isinstance(status, str) else ""


def _jsonrpc_result(request_id: Any, result: JsonObject) -> JsonObject:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _jsonrpc_error(request_id: Any, code: int, message: str) -> JsonObject:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def _cors_headers() -> JsonObject:
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept, Mcp-Session-Id, MCP-Protocol-Version",
        "Access-Control-Allow-Methods": "POST, GET, DELETE, OPTIONS",
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8765"))
    HTTPServer(("127.0.0.1", port), handler).serve_forever()
