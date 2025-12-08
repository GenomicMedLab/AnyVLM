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


def is_valid_chromosome_name(chromosome_name: str) -> bool:
    """Checks whether or not a provided chromosome name is valid.

    :param chromosome_name: The chromosome name to validate.
    :return: `True` if the chromosome name is a number between 1-22, or the values "X" or "Y"; else `False`.
    """
    min_chromosome_number = 1
    max_chromosome_number = 22
    try:
        return (
            chromosome_name in {"X", "Y"}
            or min_chromosome_number <= int(chromosome_name) <= max_chromosome_number
        )
    except ValueError:
        return False


def _normalize_chromosome_name(chromosome_name: str) -> str:
    """Normalize a chromosome name. Input must be a string consisting of either a number between 1-22,
    or 'X' or 'Y'; optionally prefixed with 'chr'.

    :param chromosome_name: The name of the chromosome to normalize, following the rules stated above.
    :return: The chromosome name, stripped of it's 'chr' prefix if it was added
    """
    # strip the 'chr' prefix if it was included
    chromosome_name = (
        chromosome_name[3:]
        if chromosome_name.lower().startswith("chr")
        else chromosome_name
    ).upper()

    if is_valid_chromosome_name(chromosome_name):
        return chromosome_name
    error_message = (
        "Invalid chromosome. Must be 1-22, 'X', or 'Y'; with optional 'chr' prefix."
    )
    raise ValueError(error_message)


ChromosomeName = Annotated[str, BeforeValidator(_normalize_chromosome_name)]
