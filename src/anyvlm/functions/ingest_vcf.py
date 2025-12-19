"""Get a VCF, register its contained variants, and add cohort frequency data to storage"""

import logging
from collections import namedtuple
from collections.abc import Iterator
from pathlib import Path

import pysam
from anyvar.utils.liftover_utils import ReferenceAssembly
from ga4gh.va_spec.base import CohortAlleleFrequencyStudyResult

from anyvlm.anyvar.base_client import BaseAnyVarClient

_logger = logging.getLogger(__name__)


AfData = namedtuple("AfData", ("ac", "an", "ac_het", "ac_hom", "ac_hemi"))


def _yield_expression_af_batches(
    vcf: pysam.VariantFile, batch_size: int = 1000
) -> Iterator[list[tuple[str, CohortAlleleFrequencyStudyResult]]]:
    """Generate a variant expression-allele frequency data pairing, one at a time

    :param vcf: VCF to pull variants from
    :param translator: VRS-Python variant translator for converting VCF expressions to VRS
    :param assembly: name of reference assembly used by VCF
    :param batch_size: size of return batches
    :return: iterator of lists of pairs of variant expressions and AF data classes
    """
    batch = []

    for record in vcf:
        for i, alt in enumerate(record.alts or []):
            if record.ref is None or "*" in record.ref or "*" in alt:
                _logger.warning("Skipping missing allele at %s", record)
                continue
            expression = f"{record.chrom}-{record.pos}-{record.ref}-{alt}"
            af = AfData(
                ac=record.info["AC"][i],
                an=record.info["AN"],
                ac_het=record.info["AC_Het"][i],
                ac_hom=record.info["AC_Hom"][i],
                ac_hemi=record.info["AC_Hemi"][i],
            )
            batch.append((expression, af))
            if len(batch) >= batch_size:
                yield batch
                batch = []
    if batch:
        yield batch


def ingest_vcf(
    vcf_path: Path,
    av: BaseAnyVarClient,
    assembly: ReferenceAssembly = ReferenceAssembly.GRCH38,
) -> None:
    """Extract variant and frequency information from a single VCF

    Current assumptions (subject to change):
    * annotations for cohort are provided in 1 file
    * INFO fields are named in conformance with convention used here:
      * AC (type: A)
      * AN (type: 1)
      * AC_Het (type: A)
      * AC_Hom (type: A)
      * AC_Hemi (type: A)

    :param vcf_path: location of input file
    :param av: AnyVar client
    :param assembly: reference assembly used by VCF
    """
    vcf = pysam.VariantFile(filename=vcf_path.absolute().as_uri(), mode="r")

    for batch in _yield_expression_af_batches(vcf):
        expressions, afs = zip(*batch, strict=True)
        variant_ids = av.put_allele_expressions(expressions, assembly)
        for variant_id, af in zip(variant_ids, afs, strict=True):  # noqa: B007
            if variant_id is None:
                continue
            # make call to object store method for putting CAF here
