"""Provide helpful type definitions, references, and type-based operations."""

from pydantic import BaseModel


class AncillaryResults(BaseModel):
    """Define model for Ancillary Results"""

    homozygotes: int
    heterozygotes: int
    hemizygotes: int


class QualityMeasures(BaseModel):
    """Define model for Quality Measures"""

    qcFilters: list[str]  # noqa: N815
