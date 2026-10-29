# ruff: noqa: D100, D103, T203, T201
import pprint
import sys
from http import HTTPMethod, HTTPStatus

from dotenv import load_dotenv
from requests.models import Response

from anyvlm.auth.token_provider import TokenProvider
from anyvlm.outbound.node_registry import NodeRegistry, VLMNode
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


def _select_node(node_registry: NodeRegistry) -> VLMNode | None:
    print("Select a node to query from the list below:")
    nodes: list[VLMNode] = node_registry.get_nodes()
    for i, node in enumerate[VLMNode](nodes):
        print(f" ({i + 1}) {node.client_name}")
    print()

    num_nodes: int = len(nodes)
    if num_nodes == 0:
        print("Sorry, no nodes are currently registered on the network")
        return None

    repeat_question = True
    error_message: str = f"❌ Please enter a number between 1-{num_nodes}"
    while repeat_question:
        selection: str = input("> Enter the number for your node of choice: ")

        try:
            selection_number = int(selection)
        except ValueError:
            print(error_message)

        if selection_number <= 0 or selection_number > num_nodes:
            print(error_message)
        else:
            repeat_question = False

    return nodes[selection_number - 1]


if __name__ == "__main__":
    vlm_client: VLMClient = VLMClient(token_provider=TokenProvider())
    node_registry: NodeRegistry = NodeRegistry(vlm_client)
    selected_node: VLMNode | None = _select_node(node_registry)
    if not selected_node:
        print("No node selected for querying - exiting")
        sys.exit()

    match_url = selected_node.match_url
    if not match_url:
        print("Sorry, your selected node does not support match queries at this time")
        sys.exit()

    response: Response = match_search(
        match_url, GrcAssemblyId.GRCH38, "chr12", 10000, "A", "T"
    )

    if response.status_code == HTTPStatus.OK:
        data = response.json()
        pprint.pprint(object=data)
    else:
        print(
            f"Sorry, there was an error querying this node. We received a response status code of :{response.status_code}"
        )
