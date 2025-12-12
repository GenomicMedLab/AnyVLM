import json
from pathlib import Path

import pytest
from dotenv import load_dotenv
from ga4gh.vrs import models
from pydantic import BaseModel

from anyvlm.anyvar.http_client import HttpAnyVarClient


@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Load `.env` file.

    Must set `autouse=True` to run before other fixtures or test cases.
    """
    load_dotenv()


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Provide Path instance pointing to test data directory"""
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def alleles(test_data_dir: Path):
    class _AlleleFixture(BaseModel):
        """Validate data structure in variations.json"""

        variation: models.Allele
        comment: str | None = None

    with (test_data_dir / "variations.json").open() as f:
        data = json.load(f)
        alleles = data["alleles"]
        for allele in alleles.values():
            assert _AlleleFixture(**allele), f"Not a valid allele fixture: {allele}"
        return alleles


def remove_request_headers(request):
    """Remove all headers from VCR request before recording."""
    request.headers = {}
    return request


def remove_response_headers(response):
    """Remove all headers from VCR response before recording."""
    response["headers"] = {}
    return response


@pytest.fixture(scope="module")
def vcr_config():
    """Configure VCR to filter out headers from cassettes."""
    return {
        "before_record_request": remove_request_headers,
        "before_record_response": remove_response_headers,
        "decode_compressed_response": True,
    }


@pytest.fixture
def anyvar_client() -> HttpAnyVarClient:
    """Provide AnyVar client fixture for tests.

    Uses HTTP because that's auto-mockable with pytest-record
    """
    return HttpAnyVarClient()
