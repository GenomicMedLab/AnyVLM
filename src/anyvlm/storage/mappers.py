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
        ac = sum((homozygotes or 0, heterozygotes or 0, hemizygotes or 0))
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
            cohort=StudyGroup(name=db_entity.cohort),  # type: ignore
        )

    def to_db_entity(
        self, va_model: CohortAlleleFrequencyStudyResult
    ) -> orm.AlleleFrequencyData:
        """Convert VA-Spec Cohort Allele Frequency Study Result model to DB Allele Frequency Data

        :param va_model: VA-Spec Cohort Allele Frequency Study Result instance
        :return: ORM Allele Frequency Data instance
        """
        ancillary_results = va_model.ancillaryResults or {}
        quality_filters = va_model.qualityMeasures or {}
        focus_allele = va_model.focusAllele

        if isinstance(focus_allele, iriReference):
            vrs_id = focus_allele.root
        else:
            vrs_id = focus_allele.id

        return orm.AlleleFrequencyData(
            vrs_id=vrs_id,
            an=va_model.locusAlleleCount,
            ac=va_model.focusAlleleCount,
            ac_het=ancillary_results.get("heterozygotes"),
            ac_hom=ancillary_results.get("homozygotes"),
            ac_hemi=ancillary_results.get("hemizygotes"),
            filter=quality_filters.get("qcFilters"),
            cohort=va_model.cohort.name,
        )
