"""Helper utilities and test examples"""

from dataclasses import dataclass

from ga4gh.core.models import iriReference
from ga4gh.vrs import models

from anyvlm.utils.types import (
    AnyVlmCohortAlleleFrequencyResult,
    GrcAssemblyId,
)

EXPECTED_VRS_ID = "ga4gh:VA.9VDxL0stMBOZwcTKw3yb3UoWQkpaI9OD"


@dataclass(frozen=True, slots=True)
class TestVariant:
    """Dataclass for test variant"""

    assembly: GrcAssemblyId
    chromosome: str
    position: int
    ref: str
    alt: str


TEST_VARIANT = TestVariant(
    assembly=GrcAssemblyId.GRCH38,
    chromosome="chrY",
    position=2781761,
    ref="C",
    alt="A",
)


def build_caf(
    base_caf: AnyVlmCohortAlleleFrequencyResult,
    allele_id: str | None = None,
    allele_obj: dict | None = None,
):
    """Build a caf object with the given allele_id or allele_obj"""
    caf = base_caf.model_copy(deep=True)
    if allele_id:
        caf.focusAllele = iriReference(root=allele_id)
    elif allele_obj:
        caf.focusAllele = models.Allele(**allele_obj)
    else:
        msg = "One of allele_id or allele_obj must be provided"
        raise ValueError(msg)

    return caf
