from pathlib import Path

import pytest

from anyvlm.anyvar.http_client import HttpAnyVarClient
from anyvlm.functions.ingest_vcf import ingest_vcf


@pytest.fixture(scope="session")
def input_vcf_path(test_data_dir: Path) -> Path:
    return test_data_dir / "vcf.vcf"


@pytest.mark.vcr
def test_ingest_vcf(input_vcf_path: Path, anyvar_client: HttpAnyVarClient):
    ingest_vcf(input_vcf_path, anyvar_client)


# GRCh37 VCF
# nonexistent path
# once storage exists, think about how to validate that AFs are stored
# handle invalid ref
