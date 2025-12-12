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


class UcscAssemblyBuild(StrEnum):
    """Supported UCSC assembly builds"""

    HG38 = "hg38"
    HG19 = "hg19"


GenomicSequence = Annotated[
    str,
    BeforeValidator(str.upper),
    StringConstraints(pattern=r"^[ACGTURYKMSWBDHVN]*$"),
]


def _normalize_chromosome_name(chromosome_name: str) -> str:
    """Normalize a chromosome name. Input must be a string consisting of either a number between 1-22,
    or one of the values 'X', 'Y', or 'MT'; optionally prefixed with 'chr'.

    :param chromosome_name: The name of the chromosome to normalize, following the rules stated above.
    :return: The chromosome name, stripped of it's 'chr' prefix if it was added
    """
    chromosome_name = chromosome_name.upper().removeprefix("CHR")

    min_chromosome_number = 1
    max_chromosome_number = 22

    if chromosome_name in {"X", "Y", "MT"} or (
        chromosome_name.isdigit()
        and min_chromosome_number <= int(chromosome_name) <= max_chromosome_number
    ):
        return chromosome_name

    raise ValueError(
        "Invalid chromosome. Must be either a number between 1-22, or "
        "'one of the values 'X', 'Y', or 'MT'; optionally prefixed with 'chr'."
    )


ChromosomeName = Annotated[str, BeforeValidator(_normalize_chromosome_name)]
