"""Get a VCF, register its contained variants, and add cohort frequency data to storage"""

import logging
import os
from collections.abc import Iterator
from pathlib import Path

import pysam
from anyvar.translate.vrs_python import AlleleTranslator
from anyvar.utils.types import VrsVariation
from ga4gh.vrs.dataproxy import create_dataproxy

from anyvlm.anyvar.base_client import BaseAnyVarClient
from anyvlm.schemas.domain import AlleleFrequencyAnnotation

_logger = logging.getLogger(__name__)


_Var_Af_Pair = tuple[VrsVariation, AlleleFrequencyAnnotation]


def _yield_var_af_batches(
    vcf: pysam.VariantFile,
    translator: AlleleTranslator,
    assembly: str,
    batch_size: int = 1000,
) -> Iterator[_Var_Af_Pair]:
    """Generate a variant-allele frequency data pairing, one at a time

    :param vcf: VCF to pull variants from
    :param translator: VRS-Python variant translator for converting VCF expressions to VRS
    :param assembly: name of reference assembly used by VCF
    :param batch_size: size of return batches
    """
    batch: list[_Var_Af_Pair] = []

    for record in vcf:
        for i, alt in enumerate(record.alts or []):
            if record.ref is None or "*" in record.ref or "*" in alt:
                _logger.warning("Skipping missing allele at %s", record)
                continue
            expression = f"{record.chrom}-{record.pos}-{record.ref}-{alt}"
            vrs_variation = translator.translate_from(
                expression, "gnomad", assembly_name=assembly
            )
            af = AlleleFrequencyAnnotation(
                ac=record.info["AC"][i],
                an=record.info["AN"],
                ac_het=record.info["AC_Het"][i],
                ac_hom=record.info["AC_Hom"][i],
                ac_hemi=record.info["AC_Hemi"][i],
            )
            batch.append((vrs_variation, af))
            if len(batch) >= batch_size:
                yield batch
                batch = []
    if batch:
        yield batch


def ingest_vcf(vcf_path: Path, av: BaseAnyVarClient, assembly: str = "GRCh38") -> None:
    """Extract variant and frequency information from a single VCF

    Current assumptions (subject to change):
    * It's a gVCF, annotations for cohort are provided in 1 file
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
    dataproxy = create_dataproxy(
        os.environ.get("SEQREPO_DATAPROXY_URI", "seqrepo+http://localhost:5000/seqrepo")
    )
    translator = AlleleTranslator(dataproxy)
    vcf = pysam.VariantFile(filename=vcf_path.absolute().as_uri(), mode="r")

    for batch in _yield_var_af_batches(vcf, translator, assembly):
        variants = [v for v, _ in batch]
        av.put_objects(variants)
        for variant, af in batch:  # noqa: B007
            pass  # make a call to a storage class to store frequency data
