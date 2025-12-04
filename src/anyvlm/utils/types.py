"""Provide helpful type definitions, references, and type-based operations."""

from enum import Enum, StrEnum
from typing import Annotated

from pydantic import BeforeValidator, StringConstraints


class EndpointTag(str, Enum):
    """Define tag names for endpoints."""

    META = "Meta"
    SEARCH = "Search"


class GrcAssemblyId(StrEnum):
    """Supported GRC assembly identifiers"""

    GRCH37 = "GRCh37"
    GRCH38 = "GRCh38"


class UscsAssemblyBuild(StrEnum):
    """Supported USCS assembly builds"""

    HG38 = "hg38"
    HG19 = "hg19"


GenomicSequence = Annotated[
    str,
    BeforeValidator(str.upper),
    StringConstraints(pattern=r"^[AGCT]*$"),
]


def _normalize_chromosome_name(chromosome_name: str) -> str:
    """Normalize a chromosome name. Input must be a string consisting of either a number between 1-22, or 'X' or 'Y';
    optionally prefixed with 'chr'.

    :param chromosome_name: The name of the chromosome to normalize, following the rules stated above.
    :return: The chromosome name, stripped of it's 'chr' prefix if it was added
    """
    error_message = (
        "Invalid chromosome. Must be 1-22, 'X,' or 'Y,' with optional 'chr' prefix."
    )

    # strip the 'chr' prefix if it was included
    chromosome_name = (
        chromosome_name[3:].upper()
        if chromosome_name.lower().startswith("chr")
        else chromosome_name.upper()
    )

    # chromosome name must be either an int, or "X" or "Y"
    try:
        int(chromosome_name)
    except ValueError:
        if chromosome_name not in ["X", "Y"]:
            raise ValueError(error_message) from None

    # if chromosome name is an int, it must be between 1-22
    if chromosome_name not in range(1, 23):  # stop is exclusive so we need to add 1
        raise ValueError(error_message)

    return chromosome_name


ChromosomeName = Annotated[str, BeforeValidator(_normalize_chromosome_name)]
