"""CLI for interacting with AnyVLM instance"""

import logging
from pathlib import Path
from timeit import default_timer as timer

import click
from anyvar.mapping.liftover import ReferenceAssembly

import anyvlm
from anyvlm.anyvar.base_client import BaseAnyVarClient
from anyvlm.config import Settings, get_config
from anyvlm.functions.ingest_vcf import ingest_vcf as ingest_vcf_function
from anyvlm.main import create_anyvar_client, create_anyvlm_storage
from anyvlm.storage import Storage

# Create alias for easier mocking in tests
ingest_vcf = ingest_vcf_function

_logger = logging.getLogger(__name__)

# Constants
MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024  # 5GB
UPLOAD_CHUNK_SIZE = 1024 * 1024  # 1MB
REQUIRED_INFO_FIELDS = {"AC", "AN", "AC_Het", "AC_Hom", "AC_Hemi"}


@click.version_option(anyvlm.__version__)
@click.group()
def _cli() -> None:
    """Manage AnyVLM data."""
    logging.basicConfig(filename="anyvlm.log", level=logging.INFO)


@_cli.command(name="ingest-vcf")
@click.option(
    "--file",
    "vcf_file_path",
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
def ingest_vcf_cli_wrapper(vcf_file_path: Path, assembly: ReferenceAssembly) -> None:
    """Deposit variants and allele frequencies from VCF into AnyVLM instance

    $ anyvlm ingest-vcf --file path/to/file.vcf.gz --assembly grch38
    """
    start: float = timer()
    _logger.info(
        "Starting VCF ingestion: file='%s', assembly='%s'",
        str(vcf_file_path),
        assembly.value,
    )

    config: Settings = get_config()
    anyvar_client: BaseAnyVarClient = create_anyvar_client(
        connection_string=config.anyvar_uri
    )
    anyvlm_storage: Storage = create_anyvlm_storage(uri=config.storage_uri)
    ingest_vcf_function(
        vcf_path=vcf_file_path,
        av=anyvar_client,
        storage=anyvlm_storage,
        assembly=assembly,
    )

    end: float = timer()
    duration: float = end - start
    _logger.info("Ingestion complete in %s", f"{duration:.3f} seconds")
    print("✅ Ingestion complete")  # noqa: T201
