"""Handles authenticating inbound requests"""

from collections import OrderedDict
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import Request

from anyvlm.auth.jwt_validator import JWTValidator
from anyvlm.outbound.node_registry import NodeRegistry
from anyvlm.utils.exceptions import AuthError, AuthErrorReason


class UnknownNodeCache:
    """manage unknown client nodes who have attempted to make requests to our service"""

    _CACHE_MAX_SIZE = 1024

    def __init__(self) -> None:
        """Initializes a cache of unknown (non-VLM Network member) nodes that have attempted to make requests to our service"""
        self.nodes: OrderedDict[str, datetime] = OrderedDict[str, datetime]()

    def add_node(self, client_id: str, cooldown_start: datetime) -> None:
        """add a node to the cache"""
        self.nodes[client_id] = cooldown_start
        if len(self.nodes) >= self._CACHE_MAX_SIZE:
            self.nodes.popitem(last=False)


class RequestAuthenticator:
    """Handles authenticating inbound requests"""

    REFRESH_COOLDOWN_SECONDS = 30
    UNKNOWN_NODE_CACHE_MAX_SIZE = 1024

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
        self.unknown_node_cache: UnknownNodeCache = UnknownNodeCache()

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

        # If not in cached unknown node list, refresh the node registry and try again,
        # unless last refresh for this ID was w/in the cool-down period
        if (
            client_id not in self.unknown_node_cache.nodes
            or self.unknown_node_cache.nodes[client_id]
            <= datetime.now(tz=UTC) - timedelta(seconds=self.REFRESH_COOLDOWN_SECONDS)
        ):
            self.node_registry.refresh_nodes()
            if client_id not in self.node_registry.get_node_ids():
                # If client_id STILL isn't in the node registry,
                # check to see if it's on cooldown in our unknown node cache and add it if it's not
                # then raise an error
                if client_id not in self.unknown_node_cache.nodes:
                    self.unknown_node_cache.add_node(
                        client_id=client_id, cooldown_start=datetime.now(tz=UTC)
                    )

                raise AuthError(error_reason=AuthErrorReason.UNRECOGNIZED_NODE)

        raise AuthError(error_reason=AuthErrorReason.UNRECOGNIZED_NODE)
