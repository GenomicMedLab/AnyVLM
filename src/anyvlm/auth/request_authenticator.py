"""Handles authenticating inbound requests"""

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import Request

from anyvlm.auth.jwt_validator import JWTValidator
from anyvlm.outbound.node_registry import NodeRegistry
from anyvlm.utils.exceptions import AuthError, AuthErrorReason


class RequestAuthenticator:
    """Handles authenticating inbound requests"""

    NODE_REGISTRY_REFRESH_COOLDOWN_SECONDS = 30

    def __init__(
        self,
        jwt_validator: JWTValidator,
        node_registry: NodeRegistry,
    ) -> None:
        """Initializes a RequestAuthenticator to authenticate inbound requests from other VLM Network nodes

        :param jwt_validator: A 'JWTValidator' instance, used to validate/decode JWT tokens
        :param node_registry: A 'NodeRegistry' instance, used to retrieve a list of all other nodes on the VLM Network

        :raises: `NodeRetrievalError` if unable to initialize a NodeRegistry
        """
        self.jwt_validator: JWTValidator = jwt_validator
        self.node_registry: NodeRegistry = node_registry
        self.last_node_refresh: datetime = datetime.now(tz=UTC)

    def authenticate(self, request: Request) -> None:
        """Authenticate a request: validate and decode request token +
        confirm requesting node is known member of the VLM network.

        :param request: The inbound request to authenticate
        :raises: `AuthError`, if unable to authenticate.
        """
        decoded_token_claims: dict[str, Any] = (
            self.jwt_validator.validate_and_decode_token(request)
        )

        client_id: Any = decoded_token_claims.get("azp")
        self.verify_node_membership(client_id=client_id)

    def verify_node_membership(self, client_id: Any) -> None:  # noqa: ANN401
        """verify that the requesting client node is a known member of the VLM Network"""
        # verify that client_id exists and is a string
        if not client_id or not isinstance(client_id, str):
            raise AuthError(error_reason=AuthErrorReason.MISSING_CLIENT_ID)

        # First, check current node registry
        if client_id in self.node_registry.get_node_ids():
            return

        # If client isn't in current node registry, refresh the registry and try again,
        # UNLESS last refresh was w/in the cool-down period (to protect against DDOS attacks)
        if datetime.now(tz=UTC) <= self.last_node_refresh + timedelta(
            seconds=self.NODE_REGISTRY_REFRESH_COOLDOWN_SECONDS
        ):
            raise AuthError(error_reason=AuthErrorReason.UNRECOGNIZED_NODE)

        self.last_node_refresh = datetime.now(tz=UTC)
        self.node_registry.refresh_nodes()
        if client_id not in self.node_registry.get_node_ids():
            raise AuthError(error_reason=AuthErrorReason.UNRECOGNIZED_NODE)
