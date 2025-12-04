"""Provide helpful type definitions, references, and type-based operations."""

from enum import StrEnum


class GrcAssemblyId(StrEnum):
    """Supported GRC assembly identifiers"""

    GRCH37 = "GRCh37"
    GRCH38 = "GRCh38"
    

class UscsAssemblyBuild(StrEnum):
	"""Supported USCS assembly builds"""
    
	HG38 = "hg38"
	HG19 = "hg19"
