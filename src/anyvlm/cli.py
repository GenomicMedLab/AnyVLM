"""CLI for interacting with AnyVLM instance"""

import logging
from pathlib import Path
from timeit import default_timer as timer

import click
from anyvar.mapping.liftover import ReferenceAssembly

import anyvlm
from anyvlm.anyvar.base_client import BaseAnyVarClient
from anyvlm.config import Settings, get_config
from anyvlm.functions.ingest_vcf import ingest_vcf
from anyvlm.main import create_anyvar_client, create_anyvlm_storage
from anyvlm.storage import Storage

_logger = logging.getLogger(__name__)


@click.version_option(anyvlm.__version__)
@click.group()
def _cli() -> None:
    """Manage AnyVLM data."""
    logging.basicConfig(filename="anyvlm.log", level=logging.INFO)


@_cli.command()
@click.command(name="ingest-vcf")
@click.option(
    "--file",
    "vcf_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="Path to a gzip-compressed VCF file (.vcf.gz)",
)
@click.option(
    "--assembly",
    type=click.Choice(
        [assembly.value for assembly in ReferenceAssembly], case_sensitive=False
    ),
    required=True,
    callback=lambda _, __, value: ReferenceAssembly(value),
    help="Reference genome assembly",
)
def ingest_vcf_cli(vcf_path: Path, assembly: ReferenceAssembly) -> None:
    """Deposit variants and allele frequencies from VCF into AnyVLM instance

    $ anyvlm ingest-vcf --file path/to/file.vcf.gz --assembly grch38
    """
    start: float = timer()

    _logger.info(
        "Starting VCF ingestion: file='%s', assembly='%s'",
        str(vcf_path),
        assembly.value,
    )

    config: Settings = get_config()

    anyvar_client: BaseAnyVarClient = create_anyvar_client(
        connection_string=config.anyvar_uri
    )
    anyvlm_storage: Storage = create_anyvlm_storage(uri=config.storage_uri)

    ingest_vcf(vcf_path, anyvar_client, anyvlm_storage, assembly)

    # params = {"assembly": assembly.value}

    # with vcf_path.open("rb") as fh:
    #     files = {"file": (vcf_path.name, fh, "application/gzip")}

    #     try:
    #         response: requests.Response = requests.post(
    #             endpoint,
    #             files=files,
    #             params=params,
    #             timeout=3600,  # 1 hour
    #         )
    #     except requests.RequestException as e:
    #         _logger.exception("HTTP POST request to AnyVLM '/ingest_vcf' failed")
    #         raise click.ClickException(str(e)) from e

    # if response.status_code != HTTPStatus.OK:
    #     _logger.error("Request failed with status code %s", response.status_code)
    #     raise click.ClickException(
    #         f"Request failed with status code: {response.status_code}"
    #     )

    end: float = timer()
    duration: float = end - start
    _logger.info("Ingestion complete in %s", f"{duration:.3f} seconds")
