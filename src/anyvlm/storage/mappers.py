"""Object mappers for converting between VA-Spec models and database entities"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from ga4gh.core.models import iriReference
from ga4gh.va_spec.base import StudyGroup

from anyvlm.storage import orm
from anyvlm.utils.types import (
    AncillaryResults,
    AnyVlmCohortAlleleFrequencyResult,
    QualityMeasures,
)

V = TypeVar("V")  # VA-Spec compliant entity type
D = TypeVar("D")  # DB entity type


class BaseMapper(Generic[V, D], ABC):
    """Base class for all object mappers"""

    @abstractmethod
    def from_db_entity(self, db_entity: D) -> V:
        """Convert DB entity to VA-Spec compliant model."""

    @abstractmethod
    def to_db_entity(self, va_model: V) -> D:
        """Convert VA-Spec compliant model to DB entity."""


class AlleleFrequencyMapper(
    BaseMapper[AnyVlmCohortAlleleFrequencyResult, orm.AlleleFrequencyData]
):
    """Maps between Allele Frequency Entities"""

    def from_db_entity(
        self, db_entity: orm.AlleleFrequencyData
    ) -> AnyVlmCohortAlleleFrequencyResult:
        """Convert DB Allele Frequency Data to VA-Spec Cohort Allele Frequency Study Result model

        :param db_entity: An ORM Allele Frequency Data instance
        :return: VA-Spec compliant Cohort Allele Frequency Study Result instance. Will
            use iriReference for focusAllele
        """
        homozygotes = db_entity.ac_hom
        heterozygotes = db_entity.ac_het
        hemizygotes = db_entity.ac_hemi

        if any(x is not None for x in (homozygotes, heterozygotes, hemizygotes)):
            ancillary_results = AncillaryResults(
                homozygotes=homozygotes,
                heterozygotes=heterozygotes,
                hemizygotes=hemizygotes,
            )
        else:
            ancillary_results = None

        ac = sum(x or 0 for x in (homozygotes, heterozygotes, hemizygotes))
        an = db_entity.an

        return AnyVlmCohortAlleleFrequencyResult(
            focusAllele=iriReference(db_entity.vrs_id),
            focusAlleleCount=ac,
            locusAlleleCount=an,
            focusAlleleFrequency=round(ac / an, 9),
            qualityMeasures=QualityMeasures(qcFilters=db_entity.filter)
            if db_entity.filter
            else None,
            ancillaryResults=ancillary_results,
            cohort=StudyGroup(name=db_entity.cohort),  # type: ignore
        )

    def to_db_entity(
        self, va_model: AnyVlmCohortAlleleFrequencyResult
    ) -> orm.AlleleFrequencyData:
        """Convert VA-Spec compliant Cohort Allele Frequency Study Result model to DB
        Allele Frequency Data

        :param va_model: VA-Spec compliant Cohort Allele Frequency Study Result instance
        :return: ORM Allele Frequency Data instance
        """
        ancillary_results = va_model.ancillaryResults
        if ancillary_results:
            ac_het = ancillary_results.heterozygotes
            ac_hom = ancillary_results.homozygotes
            ac_hemi = ancillary_results.hemizygotes
        else:
            ac_het = None
            ac_hom = None
            ac_hemi = None

        quality_measures = va_model.qualityMeasures

        focus_allele = va_model.focusAllele
        if isinstance(focus_allele, iriReference):
            vrs_id = focus_allele.root
        else:
            vrs_id = focus_allele.id

        return orm.AlleleFrequencyData(
            vrs_id=vrs_id,
            an=va_model.locusAlleleCount,
            ac=va_model.focusAlleleCount,
            ac_het=ac_het,
            ac_hom=ac_hom,
            ac_hemi=ac_hemi,
            filter=quality_measures.qcFilters if quality_measures else None,
            cohort=va_model.cohort.name,
        )
