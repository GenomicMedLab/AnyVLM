"""Object mappers for converting between VA-Spec models and database entities"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from ga4gh.core.models import iriReference
from ga4gh.va_spec.base import CohortAlleleFrequencyStudyResult, StudyGroup

from anyvlm.storage import orm

V = TypeVar("V")  # VA-Spec entity type
D = TypeVar("D")  # DB entity type


class BaseMapper(Generic[V, D], ABC):
    """Base class for all object mappers"""

    @abstractmethod
    def from_db_entity(self, db_entity: D) -> V:
        """Convert DB entity to VA-Spec model."""

    @abstractmethod
    def to_db_entity(self, va_model: V) -> D:
        """Convert VA-Spec model to DB entity."""


class AlleleFrequencyMapper(
    BaseMapper[CohortAlleleFrequencyStudyResult, orm.AlleleFrequencyData]
):
    """Maps between Allele Frequency Entities"""

    def from_db_entity(
        self, db_entity: orm.AlleleFrequencyData
    ) -> CohortAlleleFrequencyStudyResult:
        """Convert DB Allele Frequency Data to VA-Spec Cohort Allele Frequency Study Result model

        :param db_entity: An ORM Allele Frequency Data instance
        :return: VA-Spec Cohort Allele Frequency Study Result instance. Will use
            iriReference for focusAllele
        """
        homozygotes = db_entity.ac_hom
        heterozygotes = db_entity.ac_het
        hemizygotes = db_entity.ac_hemi
        ac = sum((homozygotes, heterozygotes, hemizygotes))
        an = db_entity.an

        return CohortAlleleFrequencyStudyResult(
            focusAllele=iriReference(db_entity.vrs_id),
            focusAlleleCount=ac,
            locusAlleleCount=an,
            focusAlleleFrequency=round(ac / an, 9),
            qualityMeasures={"qcFilters": db_entity.filter},
            ancillaryResults={
                "homozygotes": homozygotes,
                "heterozygotes": heterozygotes,
                "hemizygotes": hemizygotes,
            },
            cohort=StudyGroup(name=db_entity.cohort),
        )

    def to_db_entity(
        self, va_model: CohortAlleleFrequencyStudyResult
    ) -> orm.AlleleFrequencyData:
        """Convert VA-Spec Cohort Allele Frequency Study Result model to DB Allele Frequency Data

        :param va_model: VA-Spec Cohort Allele Frequency Study Result instance
        :return: ORM Allele Frequency Data instance
        """
        ancillary_results = va_model.ancillaryResults
        focus_allele = va_model.focusAllele

        if isinstance(focus_allele, iriReference):
            vrs_id = focus_allele.root
        else:
            vrs_id = focus_allele.id

        return orm.AlleleFrequencyData(
            vrs_id=vrs_id,
            an=va_model.locusAlleleCount,
            ac_het=ancillary_results["heterozygotes"],
            ac_hom=ancillary_results["homozygotes"],
            ac_hemi=ancillary_results["hemizygotes"],
            filter=va_model.qualityMeasures["qcFilters"],
            cohort=va_model.cohort.name,
        )
