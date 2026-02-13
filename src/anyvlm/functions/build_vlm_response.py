"""Craft a VlmResponse object from a list of CohortAlleleFrequencyStudyResults"""

import logging
import os

from anyvlm.schemas.vlm import (
    BeaconHandover,
    HandoverType,
    ResponseField,
    ResponseSummary,
    ResultSet,
    VlmResponse,
)
from anyvlm.utils.types import (
    AnyVlmCohortAlleleFrequencyResult,
    Zygosity,
)

_logger = logging.getLogger(__name__)


class MissingEnvironmentVariableError(Exception):
    """Raised when a required environment variable is not set."""


def _get_environment_var(key: str) -> str:
    """Retrieves an environment variable, raising an error if it is not set.

    :param key: The key for the environment variable
    :returns: The value for the environment variable of the provided `key`
    :raises: MissingEnvironmentVariableError if environment variable is not found.
    """
    value: str | None = os.environ.get(key)
    if not value:
        message = f"Missing required environment variable: {key}"
        raise MissingEnvironmentVariableError(message)
    return value


def build_nonexistent_vlm_resultsets(node_id: str) -> list[ResultSet]:
    """Build ResultSets for cases where allele is unrecognized or CAF data isn't stored

    :param node_id: Beacon node ID
    :return: list of ResultSets where each entry has a count of 0 and ``exists=False``
    """
    return [
        ResultSet(
            exists=False,
            id=f"{node_id} {zygosity.value}",
            resultsCount=0,
        )
        for zygosity in Zygosity
    ]


def build_vlm_resultsets(
    caf: AnyVlmCohortAlleleFrequencyResult, node_id: str
) -> list[ResultSet]:
    """Construct ResultSets from a given AnyVLM CAF

    If an individual count is ``None``, we assume that means it doesn't exist

    :param caf: cohort allele freq object stored by AnyVLM
    :param node_id: beacon node ID associated with the CAF
    :return: ResultSets for each kind of zygosity
    """
    ancillary_results = caf.ancillaryResults
    if ancillary_results is None:
        return build_nonexistent_vlm_resultsets(node_id)

    return [
        ResultSet(
            id=f"{node_id} {Zygosity.HOMOZYGOUS.value}",
            resultsCount=ancillary_results.homozygotes or 0,
            exists=ancillary_results.homozygotes is not None,
        ),
        ResultSet(
            id=f"{node_id} {Zygosity.HETEROZYGOUS.value}",
            resultsCount=ancillary_results.heterozygotes or 0,
            exists=ancillary_results.heterozygotes is not None,
        ),
        ResultSet(
            id=f"{node_id} {Zygosity.HEMIZYGOUS.value}",
            resultsCount=ancillary_results.hemizygotes or 0,
            exists=ancillary_results.hemizygotes is not None,
        ),
        ResultSet(
            id=f"{node_id} {Zygosity.UNKNOWN.value}", resultsCount=0, exists=False
        ),
    ]


def _build_response_summary(result_sets: list[ResultSet]) -> ResponseSummary:
    """Construct the VLM response summary from individual results

    :param result_sets: list of all results sets, of all kinds of zygosity from all sources
    :return: total count and whether variant exists in any source
    """
    count = 0
    exists = False
    for result_set in result_sets:
        count += result_set.resultsCount
        exists |= result_set.exists
    return ResponseSummary(exists=exists, numTotalResults=count)


def build_vlm_response(
    caf_data: list[AnyVlmCohortAlleleFrequencyResult],
) -> VlmResponse:
    """Craft a VlmResponse object from a list of CohortAlleleFrequencyStudyResults.

    Heavily assumptive of a single data source and single allele. Will need to be modified
    to indicate presence vs absence of requested allele(s) from one or more data sources.

    :param caf_data: A list of `AnyVlmCohortAlleleFrequencyResult` objects that will
        be used to build the VlmResponse. If empty, assumes non-existence.
    :return: A `VlmResponse` object.
    """
    # TODO - create `handover_type` and `beacon_handovers` dynamically,
    # instead of pulling from environment variables. See Issue #37.
    handover_type = HandoverType(
        id=_get_environment_var("HANDOVER_TYPE_ID"),
        label=_get_environment_var("HANDOVER_TYPE_LABEL"),
    )

    beacon_handovers: list[BeaconHandover] = [
        BeaconHandover(
            handoverType=handover_type, url=_get_environment_var("BEACON_HANDOVER_URL")
        )
    ]

    if len(caf_data) > 1:
        _logger.warning("Received more than 1 CAF data instance: %s", caf_data)
        msg = "Only single allele/data source responses are currently supported"
        raise NotImplementedError(msg)
    if len(caf_data) == 0:
        result_sets = build_nonexistent_vlm_resultsets(handover_type.id)
    else:
        result_sets = build_vlm_resultsets(caf_data[0], handover_type.id)

    summary = _build_response_summary(result_sets)

    return VlmResponse(
        beaconHandovers=beacon_handovers,
        responseSummary=summary,
        response=ResponseField(resultSets=result_sets),
    )
