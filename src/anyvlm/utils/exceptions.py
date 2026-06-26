"""Defines custom exceptions for AnyVLM"""


class IncompleteVariantError(Exception):
    """Raised when a variant is missing one or more properties required by AnyVLM"""


class LiftoverError(Exception):
    """Raised when an error occurs while attempting to lift over a variant"""


class UnexpectedVariantTypeError(Exception):
    """Raised when <vrs_variant>.type is not of the type expected by AnyVLM"""


class VariantLookupError(Exception):
    """Raised when a variant cannot be retrieved from AnyVar"""
