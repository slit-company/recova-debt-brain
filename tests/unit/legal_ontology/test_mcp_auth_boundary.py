from __future__ import annotations

import asyncio
import sys
import types
from pathlib import Path
from typing import Any, List

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
TRUSTGRAPH_MCP_PATH = REPO_ROOT / "trustgraph-mcp"
TRUSTGRAPH_BASE_PATH = REPO_ROOT / "trustgraph-base"


def test_gateway_token_verifier_uses_internal_scope_authorizer(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_mcp_auth_stubs(monkeypatch)
    auth = _mcp_server_module("auth")
    calls: List[str] = []
    identities: List[dict[str, object]] = []

    class FakeWebSocketManager:
        def __init__(self, websocket_url: str, token: str) -> None:
            self.websocket_url = websocket_url
            self.token = token

        async def start(self) -> None:
            calls.append("start")

        async def whoami(self) -> dict[str, object]:
            calls.append("whoami")
            return {"user": {"id": "reader-user"}}

        async def request(self, *args: object, **kwargs: object) -> object:
            raise AssertionError("public websocket IAM request must not authorise MCP scopes")

        async def stop(self) -> None:
            calls.append("stop")

    async def scope_authorizer(identity: dict[str, object]) -> List[str]:
        identities.append(identity)
        return ["read:tools"]

    monkeypatch.setattr(auth, "WebSocketManager", FakeWebSocketManager)

    access = asyncio.run(
        auth.GatewayTokenVerifier(
            "ws://gateway.test/api/v1/socket",
            scope_authorizer=scope_authorizer,
        ).verify_token("reader-token")
    )

    assert access is not None
    assert access.client_id == "reader-user"
    assert access.scopes == ["read:tools"]
    assert calls == ["start", "whoami", "stop"]
    assert identities == [{"user": {"id": "reader-user"}}]


def test_scope_authorizer_failure_is_not_reported_as_bad_token(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_mcp_auth_stubs(monkeypatch)
    auth = _mcp_server_module("auth")

    class FakeWebSocketManager:
        def __init__(self, websocket_url: str, token: str) -> None:
            self.websocket_url = websocket_url
            self.token = token

        async def start(self) -> None:
            pass

        async def whoami(self) -> dict[str, object]:
            return {"user": {"id": "reader-user"}}

        async def stop(self) -> None:
            pass

    async def broken_authorizer(identity: dict[str, object]) -> List[str]:
        raise ModuleNotFoundError("trustgraph.base.iam_client")

    monkeypatch.setattr(auth, "WebSocketManager", FakeWebSocketManager)

    with pytest.raises(RuntimeError, match="scope authorizer"):
        asyncio.run(
            auth.GatewayTokenVerifier(
                "ws://gateway.test/api/v1/socket",
                scope_authorizer=broken_authorizer,
            ).verify_token("reader-token")
        )


def test_lab_bearer_token_verifier_accepts_only_matching_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_mcp_auth_stubs(monkeypatch)
    auth = _mcp_server_module("auth")

    verifier = auth.LabBearerTokenVerifier("lab-token")
    accepted = asyncio.run(verifier.verify_token("lab-token"))
    rejected = asyncio.run(verifier.verify_token("wrong-token"))

    assert accepted is not None
    assert accepted.client_id == "recova-lab-client"
    assert "trustgraph-legal:mcp-domain" in accepted.scopes
    assert "stopgate:check" in accepted.scopes
    assert rejected is None


def test_iam_scope_authorizer_uses_internal_authorise_many(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_mcp_auth_stubs(monkeypatch)
    auth = _mcp_server_module("auth")
    captured: dict[str, object] = {}

    class FakeIamClient:
        def __init__(self, **kwargs: object) -> None:
            captured["init"] = kwargs

        async def start(self) -> None:
            captured["started"] = True

        async def stop(self) -> None:
            captured["stopped"] = True

        async def authorise_many(
            self,
            identity_handle: str,
            checks: List[dict[str, object]],
        ) -> List[tuple[bool, int]]:
            captured["identity_handle"] = identity_handle
            captured["checks"] = checks
            return [
                (str(check["capability"]).startswith("read:"), 30)
                for check in checks
            ]

    class DummyMetrics:
        def __init__(self, **kwargs: object) -> None:
            self.kwargs = kwargs

    monkeypatch.setattr(auth, "IamClient", FakeIamClient)
    monkeypatch.setattr(auth, "ProducerMetrics", DummyMetrics)
    monkeypatch.setattr(auth, "SubscriberMetrics", DummyMetrics)
    monkeypatch.setattr(auth, "IamRequest", object)
    monkeypatch.setattr(auth, "IamResponse", object)
    monkeypatch.setattr(auth, "iam_request_queue", "iam-request")
    monkeypatch.setattr(auth, "iam_response_queue", "iam-response")

    scopes = asyncio.run(
        auth.IamScopeAuthorizer(object(), service_id="test-mcp")(
            {"user": {"id": "reader-user"}}
        )
    )

    assert scopes == ["read:ledger", "read:tools"]
    assert captured["identity_handle"] == "reader-user"
    assert captured["started"] is True
    assert captured["stopped"] is True
    init = captured["init"]
    assert isinstance(init, dict)
    assert init["consumer_name"] == "test-mcp"
    checks = captured["checks"]
    assert isinstance(checks, list)
    assert {check["capability"] for check in checks} >= {"read:tools", "governance:review"}


def _mcp_server_module(name: str) -> Any:
    for path in (TRUSTGRAPH_MCP_PATH, TRUSTGRAPH_BASE_PATH):
        sys.path.insert(0, str(path))
    try:
        module = __import__("trustgraph.mcp_server.{}".format(name), fromlist=[name])
    finally:
        for path in (TRUSTGRAPH_BASE_PATH, TRUSTGRAPH_MCP_PATH):
            try:
                sys.path.remove(str(path))
            except ValueError:
                pass
    return module


def _install_mcp_auth_stubs(monkeypatch: pytest.MonkeyPatch) -> None:
    class AccessToken:
        def __init__(self, token: str, client_id: str, scopes: List[str]) -> None:
            self.token = token
            self.client_id = client_id
            self.scopes = scopes

    class TokenVerifier:
        pass

    modules = {
        "mcp": types.ModuleType("mcp"),
        "mcp.server": types.ModuleType("mcp.server"),
        "mcp.server.auth": types.ModuleType("mcp.server.auth"),
        "mcp.server.auth.middleware": types.ModuleType("mcp.server.auth.middleware"),
        "mcp.server.auth.middleware.auth_context": types.ModuleType(
            "mcp.server.auth.middleware.auth_context"
        ),
        "mcp.server.auth.provider": types.ModuleType("mcp.server.auth.provider"),
    }
    setattr(
        modules["mcp.server.auth.middleware.auth_context"],
        "get_access_token",
        lambda: None,
    )
    setattr(modules["mcp.server.auth.provider"], "AccessToken", AccessToken)
    setattr(modules["mcp.server.auth.provider"], "TokenVerifier", TokenVerifier)
    for name, module in modules.items():
        monkeypatch.setitem(sys.modules, name, module)
    sys.modules.pop("trustgraph.mcp_server.auth", None)
