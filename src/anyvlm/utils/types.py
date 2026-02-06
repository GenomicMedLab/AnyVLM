"""Provide helpful type definitions, references, and type-based operations."""

from enum import Enum, StrEnum
from types import MappingProxyType
from typing import Annotated

from anyvar.mapping.liftover import ReferenceAssembly
from ga4gh.va_spec.base import CohortAlleleFrequencyStudyResult
from pydantic import AfterValidator, BaseModel, BeforeValidator, StringConstraints


class AncillaryResults(BaseModel):
    """Define model for Ancillary Results"""

    homozygotes: int | None = None
    heterozygotes: int | None = None
    hemizygotes: int | None = None


class QualityMeasures(BaseModel):
    """Define model for Quality Measures"""

    qcFilters: list[str] | None = None  # noqa: N815


class AnyVlmCohortAlleleFrequencyResult(CohortAlleleFrequencyStudyResult):
    """Define model for AnyVLM Cohort Allele Frequency Result

    This is still VA-Spec compliant, but replaces dictionary fields with Pydantic models
    """

    ancillaryResults: AncillaryResults | None = None  # type: ignore # noqa: N815
    qualityMeasures: QualityMeasures | None = None  # type: ignore # noqa: N815


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


# Mapping of GRC and UCSC assembly identifiers to their corresponding ReferenceAssembly
ASSEMBLY_MAP: MappingProxyType[GrcAssemblyId | UcscAssemblyBuild, ReferenceAssembly] = (
    MappingProxyType(
        {
            GrcAssemblyId.GRCH38: ReferenceAssembly.GRCH38,
            UcscAssemblyBuild.HG38: ReferenceAssembly.GRCH38,
            GrcAssemblyId.GRCH37: ReferenceAssembly.GRCH37,
            UcscAssemblyBuild.HG19: ReferenceAssembly.GRCH37,
        }
    )
)


NucleotideSequence = Annotated[
    str,
    BeforeValidator(str.upper),
    StringConstraints(pattern=r"^[ACGTURYKMSWBDHVN.-]*$"),
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
        "Invalid chromosome name. Must be a string consisting of either a number between 1-22, "
        "or one of the values 'X', 'Y', or 'MT'; optionally prefixed with 'chr'."
    )


ChromosomeName = Annotated[str, AfterValidator(_normalize_chromosome_name)]


class Zygosity(StrEnum):
    """Allowable zygosity values as defined by the VLM protocol"""

    HOMOZYGOUS = "Homozygous"
    HETEROZYGOUS = "Heterozygous"
    HEMIZYGOUS = "Hemizygous"
    UNKNOWN = "Unknown Zygosity"
