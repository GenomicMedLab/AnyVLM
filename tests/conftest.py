import json
from os import environ
from pathlib import Path

import pytest
from dotenv import load_dotenv
from ga4gh.core.models import iriReference
from ga4gh.va_spec.base import CohortAlleleFrequencyStudyResult, StudyGroup
from ga4gh.vrs import models
from pydantic import BaseModel

from anyvlm.storage.postgres import PostgresObjectStore


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


@pytest.fixture(scope="session")
def postgres_uri():
    return environ.get(
        "ANYVLM_TEST_STORAGE_URI",
        "postgresql://postgres:postgres@localhost:5432/anyvlm_test",
    )


@pytest.fixture
def postgres_storage(postgres_uri: str):
    """Reset storage state after each test case"""
    storage = PostgresObjectStore(postgres_uri)
    storage.wipe_db()  # Ensure clean state before test
    yield storage
    storage.wipe_db()  # Clean up after test


@pytest.fixture
def caf_iri():
    """Create test fixture for CAF object that uses iriReference for focusAllele

    This is a GREGoR example from issue #23 description
    """
    return CohortAlleleFrequencyStudyResult(
        focusAllele=iriReference("ga4gh:VA.J3Hi64dkKFKdnKIwB2419Qz3STDB2sJq"),
        focusAlleleCount=1,
        locusAlleleCount=6164,
        focusAlleleFrequency=0.000162232,
        qualityMeasures={"qcFilters": ["LowQual", "NO_HQ_GENOTYPES"]},
        ancillaryResults={
            "homozygotes": 0,
            "heterozygotes": 1,
            "hemizygotes": 0,
        },
        cohort=StudyGroup(name="rare disease"),  # type: ignore
    )  # type: ignore
