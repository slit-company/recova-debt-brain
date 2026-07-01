from __future__ import annotations

import logging
import uuid
from typing import Any

from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken, TokenVerifier

from trustgraph_legal.mcp_domain import list_tools as list_debt_collection_tools

from .legal_tools import AuthContext, LEGAL_MCP_GATEWAY_SCOPE
from .tg_socket import WebSocketManager

logger = logging.getLogger(__name__)

IamClient = None
ProducerMetrics = None
SubscriberMetrics = None
IamRequest = None
IamResponse = None
iam_request_queue = None
iam_response_queue = None


class GatewayTokenVerifier(TokenVerifier):
    def __init__(
        self,
        websocket_url: str,
        scope_authorizer: Any = None,
    ):
        self.websocket_url = websocket_url
        self.scope_authorizer = scope_authorizer

    async def verify_token(self, token: str) -> AccessToken | None:
        if not token:
            return None
        manager = WebSocketManager(self.websocket_url, token=token)
        try:
            await manager.start()
            identity = await manager.whoami()
        except Exception as exc:  # noqa: BROAD_EXCEPT_OK - auth boundary converts gateway failures to denial.
            logger.warning(
                "MCP Bearer token rejected by gateway: %s",
                type(exc).__name__,
            )
            return None
        finally:
            try:
                await manager.stop()
            except Exception:  # noqa: BROAD_EXCEPT_OK - cleanup must not turn denial into token acceptance.
                pass

        try:
            authorised_scopes = await _authorised_legal_scopes(
                self.scope_authorizer,
                identity,
            )
        except Exception as exc:
            logger.exception(
                "MCP IAM scope authorizer failed: %s",
                type(exc).__name__,
            )
            raise RuntimeError("MCP IAM scope authorizer failed") from exc

        return AccessToken(
            token=token,
            client_id=_identity_client_id(identity),
            scopes=authorised_scopes,
        )


class IamScopeAuthorizer:
    def __init__(self, iam_backend: Any, service_id: str = "mcp-server"):
        self.iam_backend = iam_backend
        self.service_id = service_id

    async def __call__(self, identity: Any) -> list[str]:
        scopes = _debt_tool_scopes()
        client = self._make_client()
        await client.start()
        try:
            decisions = await client.authorise_many(
                _identity_client_id(identity),
                _scope_checks(scopes),
            )
        finally:
            try:
                await client.stop()
            except Exception:  # noqa: BROAD_EXCEPT_OK - cleanup must not mask auth denial.
                pass
        return [
            scope
            for scope, decision in zip(scopes, decisions)
            if bool(decision[0])
        ]

    def _make_client(self) -> Any:
        _load_iam_dependencies()
        rr_id = str(uuid.uuid4())
        return IamClient(
            backend=self.iam_backend,
            subscription="{}--iam--{}".format(self.service_id, rr_id),
            consumer_name=self.service_id,
            request_topic=iam_request_queue,
            request_schema=IamRequest,
            request_metrics=ProducerMetrics(
                processor=self.service_id,
                flow=None,
                name="iam-request",
            ),
            response_topic=iam_response_queue,
            response_schema=IamResponse,
            response_metrics=SubscriberMetrics(
                processor=self.service_id,
                flow=None,
                name="iam-response",
            ),
        )


def require_token(required_scope: str = "") -> AuthContext:
    access = get_access_token()
    if access is None or not access.token:
        raise RuntimeError(
            "Authentication required - send a Bearer token in the "
            "Authorization header"
        )
    scopes = set(access.scopes or [])
    if required_scope and not (
        LEGAL_MCP_GATEWAY_SCOPE in scopes
        or required_scope in scopes
        or "*" in scopes
    ):
        raise PermissionError("MCP auth context lacks required scope")
    return AuthContext(
        token=access.token,
        verified_by_gateway=True,
        scopes=tuple(sorted(scopes)),
    )


def _identity_client_id(identity: Any) -> str:
    if isinstance(identity, dict):
        user = identity.get("user")
        if isinstance(user, dict):
            for key in ("id", "username", "handle", "email"):
                value = user.get(key)
                if isinstance(value, str) and value:
                    return value
        for key in ("id", "username", "handle", "client_id"):
            value = identity.get(key)
            if isinstance(value, str) and value:
                return value
    return "mcp-caller"


def _debt_tool_scopes() -> list[str]:
    return sorted({str(tool["scope"]) for tool in list_debt_collection_tools()})


def _scope_checks(scopes: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "capability": scope,
            "resource": {"service": "debt-collection-brain-mcp"},
            "parameters": {"scope": scope},
        }
        for scope in scopes
    ]


async def _authorised_legal_scopes(
    scope_authorizer: Any,
    identity: Any,
) -> list[str]:
    if scope_authorizer is None:
        return []
    return list(await scope_authorizer(identity))


def _load_iam_dependencies() -> None:
    global IamClient
    global ProducerMetrics
    global SubscriberMetrics
    global IamRequest
    global IamResponse
    global iam_request_queue
    global iam_response_queue

    if IamClient is not None:
        return

    from trustgraph.base.iam_client import IamClient as LoadedIamClient
    from trustgraph.base.metrics import ProducerMetrics as LoadedProducerMetrics
    from trustgraph.base.metrics import SubscriberMetrics as LoadedSubscriberMetrics
    from trustgraph.schema import IamRequest as LoadedIamRequest
    from trustgraph.schema import IamResponse as LoadedIamResponse
    from trustgraph.schema import iam_request_queue as loaded_iam_request_queue
    from trustgraph.schema import iam_response_queue as loaded_iam_response_queue

    IamClient = LoadedIamClient
    ProducerMetrics = LoadedProducerMetrics
    SubscriberMetrics = LoadedSubscriberMetrics
    IamRequest = LoadedIamRequest
    IamResponse = LoadedIamResponse
    iam_request_queue = loaded_iam_request_queue
    iam_response_queue = loaded_iam_response_queue
