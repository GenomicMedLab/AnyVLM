"""Test VCF upload endpoint functionality."""

import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from anyvar.utils.liftover_utils import ReferenceAssembly
from fastapi.testclient import TestClient

from anyvlm.functions.ingest_vcf import VcfAfColumnsError
from anyvlm.main import app

# Constants for testing
MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024  # 5GB
UPLOAD_CHUNK_SIZE = 1024 * 1024  # 1MB


@pytest.fixture(scope="module")
def client():
    """Create FastAPI test client with mock anyvar_client."""
    # Set up mock anyvar client on app state
    mock_anyvar_client = MagicMock()
    mock_anyvlm_storage = MagicMock()
    app.state.anyvar_client = mock_anyvar_client
    app.state.anyvlm_storage = mock_anyvlm_storage
    return TestClient(app=app)


@pytest.fixture(scope="module")
def test_vcf_dir(test_data_dir: Path) -> Path:
    """Path to VCF test data directory."""
    return test_data_dir / "vcf"


@pytest.fixture(scope="module")
def valid_vcf_gz(test_vcf_dir: Path) -> Path:
    """Path to valid compressed VCF."""
    return test_vcf_dir / "valid_small.vcf.gz"


@pytest.fixture(scope="module")
def missing_fields_vcf_gz(test_vcf_dir: Path) -> Path:
    """Path to VCF missing required INFO fields."""
    return test_vcf_dir / "missing_info_fields.vcf.gz"


@pytest.fixture(scope="module")
def malformed_vcf_gz(test_vcf_dir: Path) -> Path:
    """Path to VCF with malformed header."""
    return test_vcf_dir / "malformed_header.vcf.gz"


@pytest.fixture(scope="module")
def not_vcf_gz(test_vcf_dir: Path) -> Path:
    """Path to gzipped text file (not a VCF)."""
    return test_vcf_dir / "not_a_vcf.txt.gz"


# ====================
# Validation Helper Tests
# ====================


class TestFileValidation:
    """Test file validation functions."""

    def test_validate_filename_extension_valid(self):
        """Test that .vcf.gz extension passes validation."""
        from anyvlm.restapi.vlm import validate_filename_extension

        # Should not raise
        validate_filename_extension("test.vcf.gz")
        validate_filename_extension("path/to/file.vcf.gz")

    def test_validate_filename_extension_invalid(self):
        """Test that non-.vcf.gz extensions fail validation."""
        from anyvlm.restapi.vlm import validate_filename_extension

        with pytest.raises(ValueError, match="Only .vcf.gz files"):
            validate_filename_extension("test.vcf")

        with pytest.raises(ValueError, match="Only .vcf.gz files"):
            validate_filename_extension("test.gz")

        with pytest.raises(ValueError, match="Only .vcf.gz files"):
            validate_filename_extension("test.txt.gz")

    def test_validate_gzip_magic_bytes_valid(self, valid_vcf_gz: Path):
        """Test gzip magic bytes validation with valid file."""
        from anyvlm.restapi.vlm import validate_gzip_magic_bytes

        with valid_vcf_gz.open("rb") as f:
            content = f.read()
            file_obj = io.BytesIO(content)
            validate_gzip_magic_bytes(file_obj)
            # Verify file pointer was reset
            assert file_obj.tell() == 0

    def test_validate_gzip_magic_bytes_invalid(self):
        """Test gzip magic bytes validation with invalid file."""
        from anyvlm.restapi.vlm import validate_gzip_magic_bytes

        # Non-gzip content
        file_obj = io.BytesIO(b"Not a gzip file")
        with pytest.raises(ValueError, match="not a valid gzip file"):
            validate_gzip_magic_bytes(file_obj)

    def test_validate_file_size_within_limit(self, valid_vcf_gz: Path):
        """Test file size validation for file within limit."""
        from anyvlm.restapi.vlm import validate_file_size

        file_size = valid_vcf_gz.stat().st_size
        assert file_size < MAX_FILE_SIZE  # Sanity check

        # Should not raise
        validate_file_size(file_size)

    def test_validate_file_size_exceeds_limit(self):
        """Test file size validation for file exceeding limit."""
        from anyvlm.restapi.vlm import validate_file_size

        too_large = MAX_FILE_SIZE + 1
        with pytest.raises(ValueError, match="File too large"):
            validate_file_size(too_large)

    def test_validate_vcf_header_valid(self, valid_vcf_gz: Path):
        """Test VCF header validation with valid file."""
        from anyvlm.restapi.vlm import validate_vcf_header

        # Should not raise
        validate_vcf_header(valid_vcf_gz)

    def test_validate_vcf_header_missing_format_declaration(
        self, malformed_vcf_gz: Path
    ):
        """Test VCF header validation fails on missing fileformat."""
        from anyvlm.restapi.vlm import validate_vcf_header

        with pytest.raises(ValueError, match="Not a valid VCF"):
            validate_vcf_header(malformed_vcf_gz)

    def test_validate_vcf_header_missing_required_fields(
        self, missing_fields_vcf_gz: Path
    ):
        """Test VCF header validation fails on missing INFO fields."""
        from anyvlm.restapi.vlm import validate_vcf_header

        with pytest.raises(ValueError, match="VCF missing required INFO fields.*AN"):
            validate_vcf_header(missing_fields_vcf_gz)


# ====================
# Endpoint Integration Tests
# ====================


class TestIngestVcfEndpoint:
    """Test the /ingest_vcf HTTP endpoint."""

    def test_endpoint_exists(self, client: TestClient):
        """Test that the endpoint exists and accepts POST."""
        response = client.post("/ingest_vcf")
        # Should not be 404
        assert response.status_code != 404

    def test_missing_file_parameter(self, client: TestClient):
        """Test request without file parameter."""
        response = client.post(
            "/ingest_vcf",
            params={"assembly": "GRCh38"},
        )
        assert response.status_code == 422  # Unprocessable Entity
        assert "file" in response.text.lower() or "required" in response.text.lower()

    def test_missing_assembly_parameter(self, client: TestClient, valid_vcf_gz: Path):
        """Test request without assembly parameter."""
        with valid_vcf_gz.open("rb") as f:
            files = {"file": ("test.vcf.gz", f, "application/gzip")}
            response = client.post("/ingest_vcf", files=files)

        assert response.status_code == 422
        assert (
            "assembly" in response.text.lower() or "required" in response.text.lower()
        )

    def test_invalid_assembly_value(self, client: TestClient, valid_vcf_gz: Path):
        """Test request with invalid assembly value."""
        with valid_vcf_gz.open("rb") as f:
            files = {"file": ("test.vcf.gz", f, "application/gzip")}
            response = client.post(
                "/ingest_vcf",
                params={"assembly": "GRCh99"},  # Invalid
                files=files,
            )

        assert response.status_code == 422

    def test_invalid_file_extension(self, client: TestClient, valid_vcf_gz: Path):
        """Test upload with wrong file extension."""
        with valid_vcf_gz.open("rb") as f:
            # Use .vcf extension (should be .vcf.gz)
            files = {"file": ("test.vcf", f, "application/gzip")}
            response = client.post(
                "/ingest_vcf",
                params={"assembly": "GRCh38"},
                files=files,
            )

        assert response.status_code == 400
        json_response = response.json()
        assert "detail" in json_response
        assert ".vcf.gz" in json_response["detail"]

    def test_not_gzipped_file(self, client: TestClient):
        """Test upload of non-gzipped content."""
        # Plain text, not gzipped
        content = b"This is not gzipped"
        files = {"file": ("test.vcf.gz", io.BytesIO(content), "application/gzip")}

        response = client.post(
            "/ingest_vcf",
            params={"assembly": "GRCh38"},
            files=files,
        )

        assert response.status_code == 400
        json_response = response.json()
        assert "detail" in json_response
        assert "gzip" in json_response["detail"].lower()

    def test_not_a_vcf_file(self, client: TestClient, not_vcf_gz: Path):
        """Test upload of gzipped file that's not a VCF."""
        with not_vcf_gz.open("rb") as f:
            files = {"file": ("test.vcf.gz", f, "application/gzip")}
            response = client.post(
                "/ingest_vcf",
                params={"assembly": "GRCh38"},
                files=files,
            )

        assert response.status_code == 422
        json_response = response.json()
        assert "detail" in json_response
        assert "vcf" in json_response["detail"].lower()

    def test_vcf_missing_required_fields(
        self, client: TestClient, missing_fields_vcf_gz: Path
    ):
        """Test upload of VCF missing required INFO fields."""
        with missing_fields_vcf_gz.open("rb") as f:
            files = {"file": ("test.vcf.gz", f, "application/gzip")}
            response = client.post(
                "/ingest_vcf",
                params={"assembly": "GRCh38"},
                files=files,
            )

        assert response.status_code == 422
        json_response = response.json()
        assert "detail" in json_response
        assert (
            "info" in json_response["detail"].lower()
            or "field" in json_response["detail"].lower()
        )

    @patch("anyvlm.restapi.vlm.ingest_vcf_function")
    def test_successful_upload_and_ingestion(
        self, mock_ingest: MagicMock, client: TestClient, valid_vcf_gz: Path
    ):
        """Test successful VCF upload and ingestion."""
        # Mock the ingest_vcf function to avoid needing real AnyVar
        mock_ingest.return_value = None

        with valid_vcf_gz.open("rb") as f:
            files = {"file": ("test.vcf.gz", f, "application/gzip")}
            response = client.post(
                "/ingest_vcf",
                params={"assembly": "GRCh38"},
                files=files,
            )

        assert response.status_code == 200
        json_response = response.json()
        assert json_response["status"] == "success"
        assert "message" in json_response

        # Verify ingest_vcf was called
        assert mock_ingest.called
        call_args = mock_ingest.call_args

        # Check Path argument
        assert isinstance(call_args[0][0], Path)

        # Check AnyVar client was passed
        assert call_args[0][1] is not None

        # Check AnyVLM storage was passed
        assert call_args[0][2] is not None

        # Check assembly (4th positional argument)
        assert call_args[0][3] == ReferenceAssembly.GRCH38

    @patch("anyvlm.restapi.vlm.ingest_vcf_function")
    def test_ingestion_failure_propagates(
        self, mock_ingest: MagicMock, client: TestClient, valid_vcf_gz: Path
    ):
        """Test that ingestion errors are properly handled and reported."""
        # Mock ingest_vcf to raise an error
        mock_ingest.side_effect = VcfAfColumnsError("Missing AC_Het field")

        with valid_vcf_gz.open("rb") as f:
            files = {"file": ("test.vcf.gz", f, "application/gzip")}
            response = client.post(
                "/ingest_vcf",
                params={"assembly": "GRCh38"},
                files=files,
            )

        assert response.status_code == 422
        json_response = response.json()
        assert "detail" in json_response
        assert "AC_Het" in json_response["detail"]

    def test_temp_file_cleanup_on_success(self, client: TestClient, valid_vcf_gz: Path):
        """Test that temporary files are cleaned up after successful ingestion."""
        with patch("anyvlm.restapi.vlm.ingest_vcf_function") as mock_ingest:
            mock_ingest.return_value = None

            with valid_vcf_gz.open("rb") as f:
                files = {"file": ("test.vcf.gz", f, "application/gzip")}
                response = client.post(
                    "/ingest_vcf",
                    params={"assembly": "GRCh38"},
                    files=files,
                )

            assert response.status_code == 200

            # Verify the temp file path that was passed to ingest_vcf no longer exists
            if mock_ingest.called:
                temp_path = mock_ingest.call_args[0][0]
                assert not temp_path.exists(), "Temporary file should be cleaned up"

    def test_temp_file_cleanup_on_error(self, client: TestClient, valid_vcf_gz: Path):
        """Test that temporary files are cleaned up even when ingestion fails."""
        with patch("anyvlm.restapi.vlm.ingest_vcf_function") as mock_ingest:
            mock_ingest.side_effect = Exception("Ingestion failed")

            with valid_vcf_gz.open("rb") as f:
                files = {"file": ("test.vcf.gz", f, "application/gzip")}
                response = client.post(
                    "/ingest_vcf",
                    params={"assembly": "GRCh38"},
                    files=files,
                )

            assert response.status_code == 500

            # Verify cleanup happened
            if mock_ingest.called:
                temp_path = mock_ingest.call_args[0][0]
                assert not temp_path.exists(), (
                    "Temporary file should be cleaned up even on error"
                )

    def test_assembly_grch37_parameter(self, client: TestClient, valid_vcf_gz: Path):
        """Test that GRCh37 assembly parameter is accepted and used."""
        with patch("anyvlm.restapi.vlm.ingest_vcf_function") as mock_ingest:
            mock_ingest.return_value = None

            with valid_vcf_gz.open("rb") as f:
                files = {"file": ("test.vcf.gz", f, "application/gzip")}
                response = client.post(
                    "/ingest_vcf",
                    params={"assembly": "GRCh37"},
                    files=files,
                )

            assert response.status_code == 200

            # Verify GRCh37 was passed (4th positional argument)
            call_args = mock_ingest.call_args
            assert call_args[0][3] == ReferenceAssembly.GRCH37


# ====================
# File Size Limit Tests
# ====================


class TestFileSizeLimits:
    """Test file size limit enforcement."""

    def test_file_size_check_with_mock_large_file(self):
        """Test that files exceeding size limit are rejected."""
        # Create a mock file that reports large size
        mock_large_file = MagicMock()
        mock_large_file.filename = "huge.vcf.gz"

        # We'll need to test this at the validation function level
        # since mocking the actual upload size is complex
        from anyvlm.restapi.vlm import validate_file_size

        with pytest.raises(ValueError, match="File too large"):
            validate_file_size(MAX_FILE_SIZE + 1)
