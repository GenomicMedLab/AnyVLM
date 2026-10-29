# ruff: noqa: D100, D103, T203
import pprint
from http import HTTPMethod, HTTPStatus

from dotenv import load_dotenv
from requests.models import Response

from anyvlm.auth.token_provider import TokenProvider
from anyvlm.outbound.node_registry import NodeRegistry
from anyvlm.outbound.vlm_client import VLMClient
from anyvlm.utils.types import ChromosomeName, GrcAssemblyId, Nucleotide

load_dotenv()


def match_search(
    query_url: str,
    assembly_id: GrcAssemblyId,
    reference_name: ChromosomeName,
    start: int,
    reference_bases: Nucleotide,
    alternate_bases: Nucleotide,
) -> Response:
    query_url += f"?assemblyId={assembly_id}&referenceName={reference_name}&start={start}&referenceBases={reference_bases}&alternateBases={alternate_bases}"
    vlm_client: VLMClient = VLMClient(token_provider=TokenProvider())
    return vlm_client.request(method_type=HTTPMethod.GET, url=query_url)


if __name__ == "__main__":
    vlm_client: VLMClient = VLMClient(token_provider=TokenProvider())
    node_registry: NodeRegistry = NodeRegistry(vlm_client)
    match_url = ""
    for node in node_registry.get_nodes():
        if node.client_id == "F7rjcLm2oWuihue1wDFOC6RwwJw6vqYY":  # seqr
            match_url: str = node.match_url if node.match_url else ""

    response = match_search(match_url, GrcAssemblyId.GRCH38, "chr12", 10000, "A", "T")

    if response.status_code == HTTPStatus.OK:
        data = response.json()
        pprint.pprint(object=data)
