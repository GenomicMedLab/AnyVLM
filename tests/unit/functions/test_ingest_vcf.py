from pathlib import Path

import pytest

from anyvlm.anyvar.http_client import HttpAnyVarClient
from anyvlm.functions.ingest_vcf import ingest_vcf


@pytest.fixture(scope="session")
def input_vcf_path(test_data_dir: Path) -> Path:
    return test_data_dir / "vcf.vcf"


@pytest.fixture
def client() -> HttpAnyVarClient:
    return HttpAnyVarClient()


def test_ingest_vcf(input_vcf_path: Path, client: HttpAnyVarClient):
    ingest_vcf(input_vcf_path, client)
