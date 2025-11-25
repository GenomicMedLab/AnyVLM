"""Provide structures for exchanging data in domain logic layer"""

from pydantic import BaseModel


class AlleleFrequencyAnnotation(BaseModel):
    """Provide components of allele frequency as annotated upon variations"""

    ac: int
    an: int
    ac_het: int
    ac_hom: int
    ac_hemi: int
