"""Object mappers for converting between VA-Spec models and database entities"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from ga4gh.core.models import iriReference
from ga4gh.va_spec.base import CohortAlleleFrequencyStudyResult, StudyGroup
from pydantic import ValidationError

from anyvlm.storage import orm
from anyvlm.utils.types import AncillaryResults, QualityMeasures

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
        ac = sum(x or 0 for x in (homozygotes, heterozygotes, hemizygotes))
        an = db_entity.an

        if filter_ := db_entity.filter:
            quality_measures = QualityMeasures(qcFilters=filter_).model_dump()
        else:
            quality_measures = None

        return CohortAlleleFrequencyStudyResult(
            focusAllele=iriReference(db_entity.vrs_id),
            focusAlleleCount=ac,
            locusAlleleCount=an,
            focusAlleleFrequency=round(ac / an, 9),
            qualityMeasures=quality_measures,
            ancillaryResults=AncillaryResults(
                homozygotes=homozygotes,
                heterozygotes=heterozygotes,
                hemizygotes=hemizygotes,
            ).model_dump(),
            cohort=StudyGroup(name=db_entity.cohort),  # type: ignore
        )

    def to_db_entity(
        self, va_model: CohortAlleleFrequencyStudyResult
    ) -> orm.AlleleFrequencyData:
        """Convert VA-Spec Cohort Allele Frequency Study Result model to DB Allele Frequency Data

        :param va_model: VA-Spec Cohort Allele Frequency Study Result instance
        :return: ORM Allele Frequency Data instance
        :raises ValueError: if ancillaryResults or qualityMeasures are invalid
        """
        try:
            ancillary_results = AncillaryResults(**va_model.ancillaryResults or {})
        except ValidationError as e:
            raise ValueError("Invalid ancillaryResults data") from e

        try:
            quality_measures = QualityMeasures(**va_model.qualityMeasures or {})
        except ValidationError as e:
            raise ValueError("Invalid qualityMeasures data") from e

        focus_allele = va_model.focusAllele

        if isinstance(focus_allele, iriReference):
            vrs_id = focus_allele.root
        else:
            vrs_id = focus_allele.id

        return orm.AlleleFrequencyData(
            vrs_id=vrs_id,
            an=va_model.locusAlleleCount,
            ac=va_model.focusAlleleCount,
            ac_het=ancillary_results.heterozygotes,
            ac_hom=ancillary_results.homozygotes,
            ac_hemi=ancillary_results.hemizygotes,
            filter=quality_measures.qcFilters,
            cohort=va_model.cohort.name,
        )
