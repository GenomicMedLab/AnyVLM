from pathlib import Path

import pytest

from anyvlm.anyvar.http_client import HttpAnyVarClient
from anyvlm.functions.ingest_vcf import ingest_vcf


@pytest.fixture(scope="session")
def input_grch38_vcf_path(test_data_dir: Path) -> Path:
    return test_data_dir / "vcf" / "grch38_vcf.vcf"


@pytest.fixture(scope="session")
def input_grch37_vcf_path(test_data_dir: Path) -> Path:
    return test_data_dir / "vcf" / "grch37_vcf.vcf"


@pytest.mark.vcr
def test_ingest_vcf_grch38(
    input_grch38_vcf_path: Path, anyvar_client: HttpAnyVarClient
):
    ingest_vcf(input_grch38_vcf_path, anyvar_client)


@pytest.mark.vcr
def test_ingest_vcf_grch37(
    input_grch37_vcf_path: Path, anyvar_client: HttpAnyVarClient
):
    ingest_vcf(input_grch37_vcf_path, anyvar_client)


def test_ingest_vcf_notfound(anyvar_client: HttpAnyVarClient):
    with pytest.raises(FileNotFoundError):
        ingest_vcf(Path("file_that_doesnt_exist.vcf"), anyvar_client)
