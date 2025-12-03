"""Get a VCF, register its contained variants, and add cohort frequency data"""

from pathlib import Path


def ingest_vcf(vcf_path: Path) -> None:
    """Extract variant and frequency information from a single gVCF

    For now, we assume they're available under consistently-named INFO fields. In the
    future, we could enable custom field names, incrementing on top of existing counts,
    etc.

    :param vcf_path: location of input file
    """
    raise NotImplementedError
