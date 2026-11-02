"""Search for a matching variant in other VLM Nodes, and retrieve their CAF data for this variant"""

from http import HTTPMethod

from requests.models import Response

from anyvlm.auth.token_provider import TokenProvider
from anyvlm.outbound.vlm_client import VLMClient
from anyvlm.utils.types import (
    ChromosomeName,
    GrcAssemblyId,
    Nucleotide,
)


def variant_match_search(
    query_url: str,
    assembly_id: GrcAssemblyId,
    reference_name: ChromosomeName,
    start: int,
    reference_bases: Nucleotide,
    alternate_bases: Nucleotide,
) -> Response:
    """Search for a matching variant in other VLM Nodes, and retrieve their CAF data for this variant.

    :param query_url: The URL for the node you are querying
    :assembly_id: The assembly for variant you're matching
    :reference_name: The name of the chromosome the variant you're matching is on
    :start: The start position of the variant you're matching
    :reference_bases: The reference base for the variant you're matching
    :alternate_bases: The alternate base for hte variant you're matching
    :return: The Response object from the node you're querying. Will match
    """
    query_url += f"?assemblyId={assembly_id}&referenceName={reference_name}&start={start}&referenceBases={reference_bases}&alternateBases={alternate_bases}"
    vlm_client: VLMClient = VLMClient(token_provider=TokenProvider())
    return vlm_client.request(method_type=HTTPMethod.GET, url=query_url)
