# ruff: noqa: D100, D103, T203, T201
import pprint
import sys
from http import HTTPMethod, HTTPStatus
from typing import Any

from dotenv import load_dotenv
from pydantic import ValidationError
from requests.models import Response

from anyvlm.auth.token_provider import TokenProvider
from anyvlm.outbound.node_registry import NodeRegistry, VLMNode
from anyvlm.outbound.vlm_client import VLMClient
from anyvlm.utils.types import (
    ChromosomeName,
    GrcAssemblyId,
    Nucleotide,
    nucleotide_adapter,
)

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


def _exit_early() -> None:
    print("🛑 exiting...")
    sys.exit()


def _validate_selected_number(
    selection: str, max_value: int, min_value: int = 0
) -> int | None:
    try:
        selection_number = int(selection)
    except ValueError:
        return None

    if selection_number <= min_value or selection_number > max_value:
        return None

    return selection_number


def _select_option_helper(
    options_list: list[Any],
    prompt: str,
    no_results_message: str,
    option_attribute: str | None = None,
) -> Any:  # noqa: ANN401
    print("\n" + prompt)

    num_options: int = len(options_list)
    if num_options == 0:
        print(no_results_message)
        _exit_early()

    for i, option in enumerate(options_list):
        selection_value = (
            getattr(option, option_attribute) if option_attribute else option
        )
        print(f" ({i + 1}) {selection_value}")

    while True:
        selection: str = input("> Enter your selection's number: ")
        selection_number: int | None = _validate_selected_number(
            selection=selection, max_value=num_options
        )
        if not selection_number:
            print(f"❌ Please enter a number between 1-{num_options}")
        else:
            return options_list[int(selection_number) - 1]


def _select_node(node_registry: NodeRegistry) -> VLMNode:
    return _select_option_helper(
        options_list=node_registry.get_nodes(),
        prompt="Select a node to query from the list below:",
        no_results_message="Sorry, no nodes are currently registered on the network",
        option_attribute="client_name",
    )


def _select_assembly() -> GrcAssemblyId:
    return _select_option_helper(
        options_list=list(GrcAssemblyId),
        prompt="Select the assembly for the variant you're matching on:",
        no_results_message="Whoops, there was an error retrieving assembly options",
    )


def _select_reference_name() -> ChromosomeName:
    options_list: list[str] = [f"chr{i}" for i in range(1, 22)] + ["X", "Y", "M"]
    return _select_option_helper(
        options_list=options_list,
        prompt="Select the chromosome for the variant you're matching on:",
        no_results_message="Whoops, there was an error retrieving chromosome selection options",
    )


def _select_start_position() -> int:
    print()
    max_start_position = 250000000  # heuristic cap; longest chromosome on either assembly is just under this length
    while True:
        start_position_string: str = input(
            "Enter the start position for the variant you're matching on: "
        )
        start_position_number: int | None = _validate_selected_number(
            selection=start_position_string, max_value=max_start_position
        )
        if not start_position_number:
            print(f"❌ Please enter a number between 1-{max_start_position}")
        else:
            return start_position_number


def _select_base(base_type: str) -> Nucleotide:
    print()
    while True:
        selected_nucleotide_str: str = input(
            f"Enter the {base_type} base for the variant you're matching on: "
        )
        try:
            selected_nucleotide: Nucleotide = nucleotide_adapter.validate_python(
                selected_nucleotide_str
            )
        except ValidationError:
            print(
                "❌ Please enter a valid nucleotide. (Note: only single bases are supported by the VLM Network at this time)"
            )
        else:
            return selected_nucleotide


if __name__ == "__main__":
    print("VARIANT MATCH QUERY")
    vlm_client: VLMClient = VLMClient(token_provider=TokenProvider())
    node_registry: NodeRegistry = NodeRegistry(vlm_client)
    selected_node: VLMNode = _select_node(node_registry)

    match_url = selected_node.match_url
    if not match_url:
        print("Sorry, your selected node does not support match queries at this time")
        _exit_early()

    print("\nTell us more about the variant you're matching against ⬇️")
    assembly: GrcAssemblyId = _select_assembly()
    reference_name: ChromosomeName = _select_reference_name()
    start_position: int = _select_start_position()
    reference_base: Nucleotide = _select_base(base_type="reference")
    alternate_base: Nucleotide = _select_base(base_type="alternate")

    print("\nRESULT:")
    response: Response = match_search(
        query_url=match_url,  # pyright: ignore[reportArgumentType]
        assembly_id=assembly,
        reference_name=reference_name,
        start=start_position,
        reference_bases="A",
        alternate_bases="T",
    )

    if response.status_code == HTTPStatus.OK:
        data = response.json()
        pprint.pprint(object=data)
    else:
        print(
            f"Sorry, there was an error querying this node. We received a response status code of :{response.status_code}"
        )
