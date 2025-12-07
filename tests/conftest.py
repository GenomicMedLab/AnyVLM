import json
from pathlib import Path

import pytest
from dotenv import load_dotenv
from ga4gh.vrs import models
from pydantic import BaseModel


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
