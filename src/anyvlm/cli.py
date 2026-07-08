"""CLI for interacting with AnyVLM instance"""

import gzip
import logging
import tempfile
import uuid
from pathlib import Path
from timeit import default_timer as timer

import click
from anyvar.mapping.liftover import ReferenceAssembly
from fastapi import HTTPException, UploadFile

import anyvlm
from anyvlm.anyvar.base_client import BaseAnyVarClient
from anyvlm.config import Settings, get_config
from anyvlm.functions.ingest_vcf import VcfAfColumnsError
from anyvlm.functions.ingest_vcf import ingest_vcf as ingest_vcf_function
from anyvlm.main import create_anyvar_client, create_anyvlm_storage
from anyvlm.storage import Storage
from anyvlm.utils.exceptions import VcfIngestionError

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


# ====================
# Validation Helpers
# ====================


def validate_filename_extension(filename: str) -> None:
    """Validate that filename has .vcf.gz extension.

    :param filename: name of uploaded file
    :raise ValueError: if extension is not .vcf.gz
    """
    if not filename.endswith(".vcf.gz"):
        raise ValueError("Only .vcf.gz files are accepted")


def validate_gzip_magic_bytes(file_obj: Path) -> None:
    """Validate that file has gzip magic bytes.

    :param file_obj: path to file to validate
    :raise ValueError: if file is not gzipped
    """
    with file_obj.open("rb") as f:
        header = f.read(2)

    if header != b"\x1f\x8b":
        raise ValueError("File is not a valid gzip file")


def validate_file_size(size: int) -> None:
    """Validate that file size is within limits.

    :param size: file size in bytes
    :raise ValueError: if file exceeds maximum size
    """
    if size > MAX_FILE_SIZE:
        max_gb = MAX_FILE_SIZE / (1024**3)
        raise ValueError(f"File too large. Maximum size: {max_gb:.1f}GB")


def validate_vcf_header(file_path: Path) -> None:
    """Validate VCF file format and required INFO fields.

    :param file_path: path to VCF file
    :raise ValueError: if VCF is malformed or missing required fields
    """
    with gzip.open(file_path, "rt") as f:
        # Check first line is VCF format declaration
        first_line = f.readline().strip()
        if not first_line.startswith("##fileformat=VCF"):
            raise ValueError("Not a valid VCF file (missing format declaration)")

        # Scan headers for required INFO fields
        found_fields = set()

        for line in f:
            if line.startswith("##INFO=<ID="):
                # Extract field ID
                field_id = line.split("ID=")[1].split(",")[0]
                found_fields.add(field_id)
            elif line.startswith("#CHROM"):
                # End of headers
                break

        missing = REQUIRED_INFO_FIELDS - found_fields
        if missing:
            raise ValueError(
                f"VCF missing required INFO fields: {', '.join(sorted(missing))}"
            )


# ====================
# File Handling
# ====================


async def save_upload_file_temp(upload_file: UploadFile) -> Path:
    """Save uploaded file to temporary location using streaming.

    :param upload_file: FastAPI UploadFile object
    :return: path to saved temporary file
    :raise: Any exceptions during file operations (caller should handle cleanup)
    """
    temp_dir = Path(tempfile.gettempdir())
    temp_path = temp_dir / f"anyvlm_{uuid.uuid4()}.vcf.gz"

    try:
        # Stream upload to disk (memory efficient)
        # Using blocking I/O here is acceptable as we're writing to local disk
        with temp_path.open("wb") as f:
            while chunk := await upload_file.read(UPLOAD_CHUNK_SIZE):
                f.write(chunk)
    except Exception:
        # Cleanup on error
        if temp_path.exists():
            temp_path.unlink()
        raise
    else:
        return temp_path


@_cli.command()
@click.command(name="ingest-vcf")
@click.option(
    "--file",
    "vcf_file",
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
def ingest_vcf_cli(vcf_file: Path, assembly: ReferenceAssembly) -> None:
    """Deposit variants and allele frequencies from VCF into AnyVLM instance

    $ anyvlm ingest-vcf --file path/to/file.vcf.gz --assembly grch38
    """
    start: float = timer()

    _logger.info(
        "Starting VCF ingestion: file='%s', assembly='%s'",
        str(vcf_file),
        assembly.value,
    )

    config: Settings = get_config()

    anyvar_client: BaseAnyVarClient = create_anyvar_client(
        connection_string=config.anyvar_uri
    )
    anyvlm_storage: Storage = create_anyvlm_storage(uri=config.storage_uri)

    try:
        validate_filename_extension(filename=vcf_file.name)

        # Validate gzip magic bytes
        validate_gzip_magic_bytes(file_obj=vcf_file)

        # Check file size
        file_size = vcf_file.stat().st_size

        validate_file_size(file_size)

        _logger.info("Validated input file %s (%d bytes)", vcf_file.name, file_size)

        # Validate VCF format and required fields
        try:
            validate_vcf_header(vcf_file)
        except ValueError as e:
            raise HTTPException(
                422,
                f"VCF validation failed: {e!s}",
            ) from e

        _logger.info("Starting VCF ingestion for %s", vcf_file.name)
        try:
            ingest_vcf_function(vcf_file, anyvar_client, anyvlm_storage, assembly)
        except VcfAfColumnsError as e:
            _logger.exception("VCF missing required INFO columns")
            raise HTTPException(422, f"VCF validation failed: {e}") from e
        except Exception as e:
            _logger.exception("VCF ingestion failed")
            raise HTTPException(500, f"Ingestion failed: {e}") from e

        _logger.info("Successfully ingested VCF: %s", vcf_file.name)
    except Exception as e:
        _logger.exception("Unexpected error during VCF upload")
        raise VcfIngestionError(f"Upload failed: {e}") from e

    end: float = timer()
    duration: float = end - start
    _logger.info("Ingestion complete in %s", f"{duration:.3f} seconds")
