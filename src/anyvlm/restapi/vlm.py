"""Define route(s) for the variant-level matching (VLM) protocol"""

import gzip
import logging
import tempfile
import uuid
from http import HTTPStatus
from pathlib import Path
from typing import Annotated, BinaryIO, Literal

from anyvar.mapping.liftover import ReferenceAssembly
from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from pydantic import BaseModel

from anyvlm.anyvar.base_client import AnyVarClientConnectionError, BaseAnyVarClient
from anyvlm.functions.build_vlm_response import build_vlm_response
from anyvlm.functions.get_caf import VariantNotRegisteredError, get_caf
from anyvlm.functions.ingest_vcf import VcfAfColumnsError
from anyvlm.functions.ingest_vcf import ingest_vcf as ingest_vcf_function
from anyvlm.schemas.vlm import VlmResponse
from anyvlm.storage.base_storage import Storage
from anyvlm.utils.types import (
    AnyVlmCohortAlleleFrequencyResult,
    ChromosomeName,
    EndpointTag,
    GrcAssemblyId,
    Nucleotide,
    UcscAssemblyBuild,
)

# Create alias for easier mocking in tests
ingest_vcf = ingest_vcf_function

_logger = logging.getLogger(__name__)

router = APIRouter()

# Constants
MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024  # 5GB
UPLOAD_CHUNK_SIZE = 1024 * 1024  # 1MB
REQUIRED_INFO_FIELDS = {"AC", "AN", "AC_Het", "AC_Hom", "AC_Hemi"}


# ====================
# Response Models
# ====================


class VcfIngestionResponse(BaseModel):
    """Response model for VCF ingestion endpoint."""

    status: Literal["success", "error"]
    message: str
    details: str | None = None


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


def validate_gzip_magic_bytes(file_obj: BinaryIO) -> None:
    """Validate that file has gzip magic bytes.

    :param file_obj: file-like object to validate
    :raise ValueError: if file is not gzipped
    """
    header = file_obj.read(2)
    file_obj.seek(0)  # Reset file pointer

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


# ====================
# Endpoints
# ====================


@router.post(
    "/ingest_vcf",
    summary="Upload and ingest VCF file",
    description=(
        "Upload a compressed VCF file (.vcf.gz) to register variants and store allele frequency data. "
        "**Requirements:** File must be gzip-compressed (.vcf.gz), contain required INFO fields "
        "(AC, AN, AC_Het, AC_Hom, AC_Hemi), and be under 5GB. "
        "Processing is synchronous with a 30-minute timeout."
    ),
    tags=[EndpointTag.SEARCH],
)
async def ingest_vcf_endpoint(
    request: Request,
    file: UploadFile,
    assembly: Annotated[
        ReferenceAssembly,
        Query(..., description="Reference genome assembly (GRCh37 or GRCh38)"),
    ],
) -> VcfIngestionResponse:
    """Upload and ingest a VCF file with allele frequency data.

    Requirements: .vcf.gz format, <5GB, INFO fields (AC, AN, AC_Het, AC_Hom, AC_Hemi).
    Synchronous processing with 30-minute timeout. Variants batched in groups of 1000.

    :param request: FastAPI request object
    :param file: uploaded VCF file
    :param assembly: reference assembly used in VCF
    :return: ingestion status response
    """
    temp_path: Path | None = None

    try:
        # Validate filename extension
        if not file.filename:
            raise HTTPException(400, "Filename is required")  # noqa: TRY301

        try:
            validate_filename_extension(file.filename)
        except ValueError as e:
            raise HTTPException(400, str(e)) from e

        # Validate content type (if provided)
        if file.content_type and file.content_type not in {
            "application/gzip",
            "application/x-gzip",
            "application/octet-stream",
        }:
            raise HTTPException(  # noqa: TRY301
                400,
                f"Invalid content type: {file.content_type}",
            )

        # Validate gzip magic bytes
        try:
            validate_gzip_magic_bytes(file.file)
        except ValueError as e:
            raise HTTPException(400, str(e)) from e

        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset

        try:
            validate_file_size(file_size)
        except ValueError as e:
            raise HTTPException(400, str(e)) from e

        # Save to temporary file
        _logger.info("Saving uploaded file %s (%d bytes)", file.filename, file_size)
        temp_path = await save_upload_file_temp(file)

        # Validate VCF format and required fields
        try:
            validate_vcf_header(temp_path)
        except ValueError as e:
            raise HTTPException(
                422,
                f"VCF validation failed: {e!s}",
            ) from e

        # Process VCF
        anyvar_client = request.app.state.anyvar_client
        anyvlm_storage = request.app.state.anyvlm_storage
        _logger.info("Starting VCF ingestion for %s", file.filename)

        try:
            ingest_vcf_function(temp_path, anyvar_client, anyvlm_storage, assembly)
        except VcfAfColumnsError as e:
            _logger.exception("VCF missing required INFO columns")
            raise HTTPException(422, f"VCF validation failed: {e}") from e
        except Exception as e:
            _logger.exception("VCF ingestion failed")
            raise HTTPException(500, f"Ingestion failed: {e}") from e

        _logger.info("Successfully ingested VCF: %s", file.filename)
        return VcfIngestionResponse(
            status="success",
            message=f"Successfully ingested {file.filename}",
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        _logger.exception("Unexpected error during VCF upload")
        raise HTTPException(500, f"Upload failed: {e}") from e
    finally:
        # Always cleanup temporary file
        if temp_path and temp_path.exists():
            _logger.debug("Cleaning up temporary file: %s", temp_path)
            temp_path.unlink()


_allele_counts_description = """Search for a SNP and receive allele counts by zygosity, in accordance with the Variant-Level Matching protocol.

* Unrecognized variants will return a `200 OK` response with a `resultsCount` of 0
"""


@router.get(
    "/variant_counts",
    summary="Get allele counts of a single sequence variant, broken down by zygosity",
    description=_allele_counts_description,
    tags=[EndpointTag.SEARCH],
)
# ruff: noqa: N803, D103
def variant_counts(
    request: Request,
    assemblyId: Annotated[
        GrcAssemblyId | UcscAssemblyBuild,
        Query(..., description="Genome reference assembly"),
    ],
    referenceName: Annotated[
        ChromosomeName, Query(..., description="Chromosome with optional 'chr' prefix")
    ],
    start: Annotated[int, Query(..., description="Variant position")],
    referenceBases: Annotated[
        Nucleotide, Query(..., description="Single genomic base (A/C/T/G)")
    ],
    alternateBases: Annotated[
        Nucleotide, Query(..., description="Single genomic base (A/C/T/G)")
    ],
) -> VlmResponse:
    anyvar_client: BaseAnyVarClient = request.app.state.anyvar_client
    anyvlm_storage: Storage = request.app.state.anyvlm_storage
    try:
        caf_data: list[AnyVlmCohortAlleleFrequencyResult] = get_caf(
            anyvar_client,
            anyvlm_storage,
            assemblyId,
            referenceName,
            start,
            referenceBases,
            alternateBases,
        )
    except VariantNotRegisteredError:
        caf_data = []
    except AnyVarClientConnectionError as e:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail="Unable to establish AnyVar connection",
        ) from e
    return build_vlm_response(caf_data)
