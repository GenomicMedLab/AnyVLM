"""Handles authenticating inbound requests"""

from typing import Any

from fastapi import Request

from anyvlm.auth.jwt_validator import JWTValidator
from anyvlm.outbound.node_registry import NodeRegistry
from anyvlm.utils.exceptions import AuthError, AuthErrorReason


class RequestAuthenticator:
    """Handles authenticating inbound requests"""

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

    def authenticate(self, request: Request) -> None:
        """Authenticate a request: validate and decode request token +
        confirm requesting node is known member of the VLM network.

        :param request: The inbound request to authenticate
        :raises: `AuthError`, if unable to authenticate.
        """
        decoded_token_claims: dict[str, Any] = (
            self.jwt_validator.validate_and_decode_token(request)
        )

        client_id: str | None = decoded_token_claims.get("azp")

        if not isinstance(client_id, str) or not client_id:
            raise AuthError(error_reason=AuthErrorReason.MISSING_CLIENT_ID)

        # First check cached node list
        if self._is_known_node(client_id=client_id):
            return

        # If not in cached node list, refresh and try again
        self.node_registry.refresh_nodes()
        if not self._is_known_node(client_id):
            raise AuthError(error_reason=AuthErrorReason.UNRECOGNIZED_NODE)

    def _is_known_node(self, client_id: str) -> bool:
        return client_id in self.node_registry.get_node_ids()
