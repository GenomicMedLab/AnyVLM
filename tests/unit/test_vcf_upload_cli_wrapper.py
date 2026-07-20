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
