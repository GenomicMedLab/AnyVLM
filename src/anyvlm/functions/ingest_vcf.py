"""Get a VCF, register its contained variants, and add cohort frequency data to storage"""

import logging
from collections import namedtuple
from collections.abc import Iterator
from pathlib import Path

import pysam
from anyvar.mapping.liftover import ReferenceAssembly
from ga4gh.core.models import iriReference
from ga4gh.va_spec.base import StudyGroup

from anyvlm.anyvar.base_client import BaseAnyVarClient
from anyvlm.storage.base_storage import Storage
from anyvlm.utils.types import (
    AncillaryResults,
    AnyVlmCohortAlleleFrequencyResult,
    QualityMeasures,
)

_logger = logging.getLogger(__name__)


AfData = namedtuple("AfData", ("ac", "an", "ac_het", "ac_hom", "ac_hemi", "filters"))


class VcfAfColumnsError(Exception):
    """Raise for missing VCF INFO columns that are required for AF ingestion"""


def _yield_expression_af_batches(
    vcf: pysam.VariantFile, batch_size: int = 1000
) -> Iterator[list[tuple[str, AfData]]]:
    """Generate batches of tuples of (variant expression, allele frequency data).

    Operates lazily so only one batch is in memory at a time. If a VCF record has
    multiple alternate alleles, each is returned as a separate item.

    :param vcf: VCF to pull variants from
    :param batch_size: size of return batches
    :return: iterator of lists of pairs of variant expressions and AF data instances
    """
    batch = []

    for record in vcf:
        for i, alt in enumerate(record.alts or []):
            if record.ref is None or "*" in record.ref or "*" in alt:
                _logger.info("Skipping missing allele at %s", record)
                continue
            expression = f"{record.chrom}-{record.pos}-{record.ref}-{alt}"
            try:
                af = AfData(
                    ac=record.info["AC"][i],
                    an=record.info["AN"],
                    ac_het=record.info["AC_Het"][i],
                    ac_hom=record.info["AC_Hom"][i],
                    ac_hemi=record.info["AC_Hemi"][i],
                    filters=record.filter.keys(),
                )
            except KeyError as e:
                info = record.info
                msg = f"One or more required INFO column is missing: {'AC' in info}, {'AN' in info}, {'AC_Het' in info}, {'AC_Hom' in info}, {'AC_Hemi' in info}"
                _logger.exception(msg)
                raise VcfAfColumnsError(msg) from e
            batch.append((expression, af))
            if len(batch) >= batch_size:
                _logger.debug("Yielding next batch")
                yield batch
                batch = []
    if batch:
        yield batch
    _logger.debug("Expression/AF generator exhausted")


def ingest_vcf(
    vcf_path: Path,
    av: BaseAnyVarClient,
    storage: Storage,
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
    :param storage: AnyVLM storage instance
    :param assembly: reference assembly used by VCF
    :raise VcfAfColumnsError: if VCF is missing required columns
    """
    pysam.set_verbosity(0)  # silences warning re: lack of an index for the vcf file
    vcf = pysam.VariantFile(filename=vcf_path.absolute().as_uri(), mode="r")

    for batch in _yield_expression_af_batches(vcf):
        expressions, afs = zip(*batch, strict=True)
        variant_ids = av.put_allele_expressions(expressions, assembly)

        cafs = []
        for variant_id, af in zip(variant_ids, afs, strict=True):
            if variant_id is None:
                continue
            caf = AnyVlmCohortAlleleFrequencyResult(
                focusAllele=iriReference(variant_id),
                focusAlleleCount=af.ac,
                locusAlleleCount=af.an,
                focusAlleleFrequency=af.ac / af.an,
                qualityMeasures=QualityMeasures(qcFilters=af.filters),
                ancillaryResults=AncillaryResults(
                    heterozygotes=af.ac_het,
                    homozygotes=af.ac_hom,
                    hemizygotes=af.ac_hemi,
                ),
                cohort=StudyGroup(name="rare disease"),
            )
            cafs.append(caf)

        storage.add_allele_frequencies(cafs)
