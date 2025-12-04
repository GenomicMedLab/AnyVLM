"""Define route(s) for the variant-level matching (VLM) protocol"""

from pathlib import Path


def ingest_vcf(vcf_path: Path) -> None:
    """Ingest variants and cohort allele frequency data from an input VCF

    :param vcf_path: VCF file location
    """
    raise NotImplementedError
