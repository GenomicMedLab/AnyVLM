"""Defines custom exceptions for AnyVLM"""

from enum import StrEnum
from http import HTTPStatus
from typing import ClassVar


class IncompleteVariantError(Exception):
    """Raised when a variant is missing one or more properties required by AnyVLM"""


class LiftoverError(Exception):
    """Raised when an error occurs while attempting to lift over a variant"""


class UnexpectedVariantTypeError(Exception):
    """Raised when <vrs_variant>.type is not of the type expected by AnyVLM"""


class VcfIngestionError(Exception):
    """Raised VCF ingestion is unsuccessful"""


class VariantLookupError(Exception):
    """Raised when a variant cannot be retrieved from AnyVar"""


class TokenRetrievalError(Exception):
    """Raised when a token cannot be retrieved"""


class NodeRetrievalError(Exception):
    """Raised when the list of nodes on the VLM network cannot be retrieved"""


class AuthErrorReason(StrEnum):
    """Defines the error messages"""

    INVALID_HEADER = "Invalid request header"
    INVALID_SCHEMA = "Invalid token schema"
    INVALID_TOKEN = "Invalid access token"
    MISSING_TOKEN = "Missing bearer token"
    EXPIRED_TOKEN = "Access token has expired"
    MISSING_CLIENT_ID = "Missing client identity"
    UNRECOGNIZED_NODE = "Client is not authorized for access"


class AuthError(Exception):
    """Raised when an error occurs during Authentication"""

    reason_to_code_mapping: ClassVar[dict[AuthErrorReason, HTTPStatus]] = {
        AuthErrorReason.INVALID_HEADER: HTTPStatus.BAD_REQUEST,
        AuthErrorReason.INVALID_SCHEMA: HTTPStatus.UNAUTHORIZED,
        AuthErrorReason.INVALID_TOKEN: HTTPStatus.UNAUTHORIZED,
        AuthErrorReason.MISSING_TOKEN: HTTPStatus.UNAUTHORIZED,
        AuthErrorReason.EXPIRED_TOKEN: HTTPStatus.UNAUTHORIZED,
        AuthErrorReason.MISSING_CLIENT_ID: HTTPStatus.UNAUTHORIZED,
        AuthErrorReason.UNRECOGNIZED_NODE: HTTPStatus.FORBIDDEN,
    }

    reason_to_header_mapping: ClassVar[dict[AuthErrorReason, dict[str, str]]] = {
        AuthErrorReason.MISSING_TOKEN: {
            "WWW-Authenticate": 'Bearer realm="AnyVLM"',
        },
        AuthErrorReason.INVALID_TOKEN: {
            "WWW-Authenticate": 'Bearer error="invalid_token"',
        },
        AuthErrorReason.EXPIRED_TOKEN: {
            "WWW-Authenticate": (
                'Bearer error="invalid_token", '
                'error_description="The access token expired"'
            ),
        },
        AuthErrorReason.MISSING_CLIENT_ID: {
            "WWW-Authenticate": 'Bearer error="invalid_token"',
        },
        AuthErrorReason.INVALID_HEADER: {
            "WWW-Authenticate": 'Bearer realm="AnyVLM"',
        },
        AuthErrorReason.INVALID_SCHEMA: {
            "WWW-Authenticate": 'Bearer realm="AnyVLM"',
        },
    }

    def __init__(self, error_reason: AuthErrorReason) -> None:  # noqa: D107
        self.error_reason: AuthErrorReason = error_reason
        self.code: HTTPStatus = self.reason_to_code_mapping[error_reason]
        self.header: dict[str, str] | None = self.reason_to_header_mapping.get(
            error_reason
        )
        super().__init__(error_reason)
