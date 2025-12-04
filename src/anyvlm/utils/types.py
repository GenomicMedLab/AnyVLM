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


class GenomicBase(StrEnum):
	"""Genomic bases for DNA sequences"""
	
	A = "A"
	G = "G"
	C = "C"
	T = "T"

ALLOWED_GENOMIC_BASES = {base.value for base in GenomicBase}

def is_valid_dna_sequence(sequence: str) -> bool:
	return set(sequence.upper()) <= ALLOWED_GENOMIC_BASES