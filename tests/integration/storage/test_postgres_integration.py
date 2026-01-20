"""Test postgres storage integration methods"""

from sqlalchemy import select

from anyvlm.storage import orm
from anyvlm.storage.postgres import PostgresObjectStore
from anyvlm.utils.types import AnyVlmCohortAlleleFrequencyResult


def return_cafs(postgres_storage: PostgresObjectStore):
    """Integration-test helper: Get all CAF rows from the DB"""
    with postgres_storage.session_factory() as session:
        return session.execute(select(orm.AlleleFrequencyData)).scalars().all()


def test_db_lifecycle(
    anyvlm_postgres_uri: str, caf_iri: AnyVlmCohortAlleleFrequencyResult
):
    """Test that DB lifecycle works correctly"""
    # set up and populate DB
    storage = PostgresObjectStore(anyvlm_postgres_uri)
    caf_rows = return_cafs(storage)
    assert caf_rows == []

    storage.add_allele_frequencies([caf_iri])
    caf_rows = return_cafs(storage)
    assert len(caf_rows) == 1

    # wipe_db removes objects
    storage.wipe_db()
    caf_rows = return_cafs(storage)
    assert caf_rows == []
