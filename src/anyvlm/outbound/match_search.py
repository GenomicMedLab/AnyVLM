# ruff: noqa: D100, D103
from http import HTTPMethod

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
    query_url += f"/?assembly_id={assembly_id}&referenceName={reference_name}&start={start}&referenceBases={reference_bases}&alternateBases={alternate_bases}"
    vlm_client: VLMClient = VLMClient(token_provider=TokenProvider())
    return vlm_client.request(method_type=HTTPMethod.GET, url=query_url)


if __name__ == "__main__":
    vlm_client: VLMClient = VLMClient(token_provider=TokenProvider())
    node_registry: NodeRegistry = NodeRegistry(vlm_client)
    # for node in node_registry.get_nodes():
    #     print(f"{node.client_name}:")
    #     print(f"  client_id: {node.client_id}")
    #     print(f"  match_url: {node.match_url}")
