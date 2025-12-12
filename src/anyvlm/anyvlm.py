"""Client for cohort allele frequency (CAF) retrieval"""

from anyvar.utils.types import VrsVariation
from ga4gh.va_spec.base import CohortAlleleFrequencyStudyResult

from anyvlm.storage.base_storage import Storage


class AnyVLM:
    """Client for cohort allele frequency (CAF) operations"""

    def __init__(self, storage: Storage) -> None:
        """Initialize AnyVLM client

        :param storage: AnyVLM storage
        """
        self.storage = storage

    def get_caf_for_variations(
        self, vrs_variations: list[VrsVariation]
    ) -> list[CohortAlleleFrequencyStudyResult]:
        """Retrieve Cohort Allele Frequency data for given VRS Variations

        :param vrs_variations: List of VRS Variations to get CAF data for
        :return: list of CAFs for VRS Variations. Will use VRS Variation for focusAllele
        """
        vrs_variations_map: dict[str, VrsVariation] = {
            vrs_variation.id: vrs_variation for vrs_variation in vrs_variations
        }

        cafs: list[CohortAlleleFrequencyStudyResult] = self.storage.get_caf_by_vrs_ids(
            list(vrs_variations_map)
        )

        for caf in cafs:
            caf.focusAllele = vrs_variations_map[caf.focusAllele.root]

        return cafs
