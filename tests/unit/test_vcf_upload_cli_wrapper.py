"""Test VCF upload CLI wrapper functionality."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import click
import pytest
from anyvar.mapping.liftover import ReferenceAssembly
from click.testing import CliRunner

from anyvlm.functions.ingest_vcf import VcfAfColumnsError
from anyvlm.utils.exceptions import VcfIngestionError

# Constants for testing
MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024  # 5GB
UPLOAD_CHUNK_SIZE = 1024 * 1024  # 1MB


@pytest.fixture
def runner() -> CliRunner:
    """Create Click CLI runner."""
    return CliRunner()


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
        from anyvlm.cli import validate_filename_extension

        # Should not raise
        validate_filename_extension(filename="test.vcf.gz")
        validate_filename_extension(filename="path/to/file.vcf.gz")

    def test_validate_filename_extension_invalid(self):
        """Test that non-.vcf.gz extensions fail validation."""
        from anyvlm.cli import validate_filename_extension

        with pytest.raises(ValueError, match="Only .vcf.gz files"):
            validate_filename_extension(filename="test.vcf")

        with pytest.raises(ValueError, match="Only .vcf.gz files"):
            validate_filename_extension(filename="test.gz")

        with pytest.raises(ValueError, match="Only .vcf.gz files"):
            validate_filename_extension(filename="test.txt.gz")

    def test_validate_gzip_magic_bytes_valid(self, valid_vcf_gz: Path):
        """Test gzip magic bytes validation with valid file."""
        from anyvlm.cli import validate_gzip_magic_bytes

        validate_gzip_magic_bytes(vcf_file_path=valid_vcf_gz)

    def test_validate_gzip_magic_bytes_invalid(self):
        """Test gzip magic bytes validation with invalid file."""
        from anyvlm.cli import validate_gzip_magic_bytes

        runner = CliRunner()
        with runner.isolated_filesystem():
            invalid_gzip = Path("not_gzip.vcf.gz")
            invalid_gzip.write_bytes(b"Not a gzip file")

            with pytest.raises(ValueError, match="not a valid gzip file"):
                validate_gzip_magic_bytes(invalid_gzip)

    def test_validate_file_size_within_limit(self, valid_vcf_gz: Path):
        """Test file size validation for file within limit."""
        from anyvlm.cli import validate_file_size

        file_size: int = valid_vcf_gz.stat().st_size
        assert file_size < MAX_FILE_SIZE  # Sanity check

        # Should not raise
        validate_file_size(vcf_file_path=valid_vcf_gz)

    def test_file_size_check_with_mock_large_file(self):
        """Test that files exceeding size limit are rejected."""
        from anyvlm.cli import validate_file_size

        file_path = MagicMock(spec=Path)
        file_path.stat.return_value.st_size = MAX_FILE_SIZE + 1

        with pytest.raises(ValueError, match="File too large"):
            validate_file_size(file_path)

    def test_validate_vcf_header_valid(self, valid_vcf_gz: Path):
        """Test VCF header validation with valid file."""
        from anyvlm.cli import validate_vcf_header

        # Should not raise
        validate_vcf_header(vcf_file_path=valid_vcf_gz)

    def test_validate_vcf_header_missing_format_declaration(
        self, malformed_vcf_gz: Path
    ):
        """Test VCF header validation fails on missing fileformat."""
        from anyvlm.cli import validate_vcf_header

        with pytest.raises(ValueError, match="Not a valid VCF"):
            validate_vcf_header(vcf_file_path=malformed_vcf_gz)

    def test_validate_vcf_header_missing_required_fields(
        self, missing_fields_vcf_gz: Path
    ):
        """Test VCF header validation fails on missing INFO fields."""
        from anyvlm.cli import validate_vcf_header

        with pytest.raises(ValueError, match="VCF missing required INFO fields.*AN"):
            validate_vcf_header(vcf_file_path=missing_fields_vcf_gz)


# ====================
# CLI Wrapper Integration Tests
# ====================


class TestIngestVcfCliWrapper:
    """Test the `ingest_vcf_cli_wrapper` function"""

    @staticmethod
    def _invoke_ingest_vcf(
        runner: CliRunner, args: list[str], **patches: MagicMock
    ) -> click.testing.Result:
        from anyvlm.cli import _cli

        default_config = SimpleNamespace(
            anyvar_uri="http://example-anyvar",
            storage_uri="postgresql://example-storage",
        )
        with (
            patch(
                "anyvlm.cli.get_config",
                return_value=patches.get("config", default_config),
            ),
            patch(
                "anyvlm.cli.create_anyvar_client",
                return_value=patches.get("anyvar_client", MagicMock()),
            ),
            patch(
                "anyvlm.cli.create_anyvlm_storage",
                return_value=patches.get("anyvlm_storage", MagicMock()),
            ),
        ):
            return runner.invoke(_cli, ["ingest-vcf", *args])

    def test_missing_file_parameter(self, runner: CliRunner):
        """Test CLI invocation without file parameter."""
        result = self._invoke_ingest_vcf(runner, ["--assembly", "GRCh38"])

        assert result.exit_code == 2
        assert "Missing option '--file'" in result.output

    def test_missing_assembly_parameter(self, runner: CliRunner, valid_vcf_gz: Path):
        """Test CLI invocation without assembly parameter."""
        result = self._invoke_ingest_vcf(runner, ["--file", str(valid_vcf_gz)])

        assert result.exit_code == 2
        assert "Missing option '--assembly'" in result.output

    def test_invalid_assembly_value(self, runner: CliRunner, valid_vcf_gz: Path):
        """Test CLI invocation with invalid assembly value."""
        result = self._invoke_ingest_vcf(
            runner, ["--file", str(valid_vcf_gz), "--assembly", "GRCh99"]
        )

        assert result.exit_code == 2
        assert "Invalid value for '--assembly'" in result.output

    def test_invalid_file_extension(self, runner: CliRunner, valid_vcf_gz: Path):
        """Test ingestion fails for wrong file extension."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            wrong_extension = Path("test.vcf")
            wrong_extension.write_bytes(valid_vcf_gz.read_bytes())

            result = self._invoke_ingest_vcf(
                runner, ["--file", str(wrong_extension), "--assembly", "GRCh38"]
            )

        assert result.exit_code == 1
        assert isinstance(result.exception, VcfIngestionError)
        assert "VCF validation failed" in str(result.exception)
        assert ".vcf.gz" in str(result.exception)

    def test_not_gzipped_file(self, runner: CliRunner):
        """Test ingestion fails for non-gzipped content."""
        with runner.isolated_filesystem():
            plain_text_file = Path("test.vcf.gz")
            plain_text_file.write_bytes(b"This is not gzipped")

            result = self._invoke_ingest_vcf(
                runner, ["--file", str(plain_text_file), "--assembly", "GRCh38"]
            )

        assert result.exit_code == 1
        assert isinstance(result.exception, VcfIngestionError)
        assert "valid gzip file" in str(result.exception)

    def test_not_a_vcf_file(self, runner: CliRunner, not_vcf_gz: Path):
        """Test ingestion fails for gzipped content that is not a VCF."""
        with runner.isolated_filesystem():
            renamed_not_vcf = Path("not_a_vcf.vcf.gz")
            renamed_not_vcf.write_bytes(not_vcf_gz.read_bytes())

            result = self._invoke_ingest_vcf(
                runner, ["--file", str(renamed_not_vcf), "--assembly", "GRCh38"]
            )

        assert result.exit_code == 1
        assert isinstance(result.exception, VcfIngestionError)
        assert "Not a valid VCF file" in str(result.exception)

    def test_vcf_missing_required_fields(
        self, runner: CliRunner, missing_fields_vcf_gz: Path
    ):
        """Test ingestion fails for VCF missing required INFO fields."""
        result = self._invoke_ingest_vcf(
            runner, ["--file", str(missing_fields_vcf_gz), "--assembly", "GRCh38"]
        )

        assert result.exit_code == 1
        assert isinstance(result.exception, VcfIngestionError)
        assert "required INFO fields" in str(result.exception)

    @patch("anyvlm.cli.ingest_vcf_function")
    def test_successful_upload_and_ingestion(
        self, mock_ingest: MagicMock, runner: CliRunner, valid_vcf_gz: Path
    ):
        """Test successful VCF ingestion via the CLI wrapper."""
        mock_ingest.return_value = None

        result = self._invoke_ingest_vcf(
            runner, ["--file", str(valid_vcf_gz), "--assembly", "GRCh38"]
        )

        assert mock_ingest.called
        call_args = mock_ingest.call_args

        assert isinstance(call_args[0][0], Path)
        assert call_args[0][1] is not None
        assert call_args[0][2] is not None
        assert call_args[0][3] == ReferenceAssembly.GRCH38

        assert result.exit_code == 0
        assert "Ingestion complete" in result.output

    @patch("anyvlm.cli.ingest_vcf_function")
    def test_ingestion_failure_propagates(
        self, mock_ingest: MagicMock, runner: CliRunner, valid_vcf_gz: Path
    ):
        """Test ingestion errors are wrapped in `VcfIngestionError`."""
        mock_ingest.side_effect = VcfAfColumnsError("Missing AC_Het field")

        result = self._invoke_ingest_vcf(
            runner, ["--file", str(valid_vcf_gz), "--assembly", "GRCh38"]
        )

        assert result.exit_code == 1
        assert isinstance(result.exception, VcfIngestionError)
        assert "VCF missing required INFO columns" in str(result.exception)
        assert "AC_Het" in str(result.exception)

    def test_unexpected_ingestion_failure_propagates(
        self, runner: CliRunner, valid_vcf_gz: Path
    ):
        """Test unexpected ingestion errors are wrapped in `VcfIngestionError`."""
        with patch("anyvlm.cli.ingest_vcf_function") as mock_ingest:
            mock_ingest.side_effect = RuntimeError("Ingestion failed")
            result = self._invoke_ingest_vcf(
                runner, ["--file", str(valid_vcf_gz), "--assembly", "GRCh38"]
            )

        assert result.exit_code == 1
        assert isinstance(result.exception, VcfIngestionError)
        assert "Unexpected error during VCF upload" in str(result.exception)
        assert "Ingestion failed" in str(result.exception)

    def test_assembly_grch37_parameter(self, runner: CliRunner, valid_vcf_gz: Path):
        """Test that GRCh37 assembly parameter is accepted and used."""
        with patch("anyvlm.cli.ingest_vcf_function") as mock_ingest:
            mock_ingest.return_value = None

            result = self._invoke_ingest_vcf(
                runner, ["--file", str(valid_vcf_gz), "--assembly", "GRCh37"]
            )

        assert result.exit_code == 0
        call_args = mock_ingest.call_args
        assert call_args[0][3] == ReferenceAssembly.GRCH37
