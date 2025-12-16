"""Provide helpful type definitions, references, and type-based operations."""

from pydantic import BaseModel


class AncillaryResults(BaseModel):
    """Define model for Ancillary Results"""

    homozygotes: int | None = None
    heterozygotes: int | None = None
    hemizygotes: int | None = None


class QualityMeasures(BaseModel):
    """Define model for Quality Measures"""

    qcFilters: list[str] | None = None  # noqa: N815
