"""Test postgres storage integration methods"""

from ga4gh.va_spec.base import CohortAlleleFrequencyStudyResult
from tests.conftest import return_cafs

from anyvlm.storage.postgres import PostgresObjectStore


def test_db_lifecycle(postgres_uri: str, caf_iri: CohortAlleleFrequencyStudyResult):
    """Test that DB lifecycle works correctly"""
    # set up and populate DB
    storage = PostgresObjectStore(postgres_uri)
    caf_rows = return_cafs(storage)
    assert caf_rows == []

    storage.add_allele_frequency(caf_iri)
    caf_rows = return_cafs(storage)
    assert len(caf_rows) == 1

    # wipe_db removes objects
    storage.wipe_db()
    caf_rows = return_cafs(storage)
    assert caf_rows == []
