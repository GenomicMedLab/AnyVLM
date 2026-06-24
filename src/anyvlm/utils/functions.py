"""Defines utility functions for use throughout AnyVLM"""

from typing import cast

from anyvar.core.objects import SupportedVrsObject
from ga4gh.vrs.models import Allele

from anyvlm.utils.exceptions import (
    IncompleteVariantError,
    UnexpectedVariantTypeError,
    VariantLookupError,
)


def validate_allele(allele: SupportedVrsObject | None) -> Allele:
    """Validates that the provided object is indeed a VRS Allele, with all the properties AnyVLM requires

    :param allele: The allele we're validating
    :return: A VRS Allele object
    """
    if not allele:
        raise VariantLookupError

    if not allele.id:
        raise IncompleteVariantError

    try:
        validated_allele: Allele = cast(Allele, allele)
    except (ValueError, TypeError) as e:
        raise UnexpectedVariantTypeError from e

    return validated_allele
