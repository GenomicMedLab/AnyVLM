"""Test VCF upload CLI wrapper functionality."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import click
import pytest
from anyvar.mapping.liftover import ReferenceAssembly
from click.testing import CliRunner

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

    def test_validate_gzip_magic_bytes_valid(self, valid_vcf_gz: Path):
        """Test gzip magic bytes validation with valid file."""
        from anyvlm.cli import validate_gzip_magic_bytes

        # Should not raise an error
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

        with pytest.raises(
            ValueError, match="VCF ingestion failed: missing required INFO field.*AN"
        ):
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
        from anyvlm.cli import _cli  # pyright: ignore[reportPrivateUsage]

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

    def test_not_a_vcf_file(self, runner: CliRunner, not_vcf_gz: Path):
        """Test ingestion fails for gzipped content that is not a VCF."""
        with runner.isolated_filesystem():
            renamed_not_vcf = Path("not_a_vcf.vcf.gz")
            renamed_not_vcf.write_bytes(not_vcf_gz.read_bytes())

            result = self._invoke_ingest_vcf(
                runner, ["--file", str(renamed_not_vcf), "--assembly", "GRCh38"]
            )

        assert result.exit_code == 1
        # assert isinstance(result.exception, VcfIngestionError)
        # assert "Not a valid VCF file" in str(result.exception)

    def test_vcf_missing_required_fields(
        self, runner: CliRunner, missing_fields_vcf_gz: Path
    ):
        """Test ingestion fails for VCF missing required INFO fields."""
        result = self._invoke_ingest_vcf(
            runner, ["--file", str(missing_fields_vcf_gz), "--assembly", "GRCh38"]
        )

        assert result.exit_code == 1
        # assert isinstance(result.exception, VcfIngestionError)
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

        assert isinstance(call_args.kwargs["vcf_path"], Path)
        assert call_args.kwargs["av"] is not None
        assert call_args.kwargs["storage"] is not None
        assert call_args.kwargs["assembly"] == ReferenceAssembly.GRCH38

        assert result.exit_code == 0
        assert "Ingestion complete" in result.output

    def test_assembly_grch37_parameter(self, runner: CliRunner, valid_vcf_gz: Path):
        """Test that GRCh37 assembly parameter is accepted and used."""
        with patch("anyvlm.cli.ingest_vcf_function") as mock_ingest:
            mock_ingest.return_value = None

            result = self._invoke_ingest_vcf(
                runner, ["--file", str(valid_vcf_gz), "--assembly", "GRCh37"]
            )

        assert result.exit_code == 0
        call_args = mock_ingest.call_args
        assert call_args.kwargs["assembly"] == ReferenceAssembly.GRCH37
