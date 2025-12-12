"""Provide PostgreSQL-based storage implementation."""

from ga4gh.va_spec.base import CohortAlleleFrequencyStudyResult
from sqlalchemy import create_engine, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker

from anyvlm.storage import orm
from anyvlm.storage.base_storage import (
    Storage,
)
from anyvlm.storage.mapper_registry import mapper_registry
from anyvlm.storage.orm import create_tables


class PostgresObjectStore(Storage):
    """PostgreSQL storage backend using dedicated ORM tables."""

    MAX_ROWS = 100

    def __init__(self, db_url: str, *args, **kwargs) -> None:
        """Initialize PostgreSQL storage.

        :param db_url: Database connection URL (e.g., postgresql://user:pass@host:port/db)
        """
        self.db_url = db_url
        self.engine = create_engine(db_url)
        self.session_factory = sessionmaker(bind=self.engine)
        create_tables(self.db_url)

    def close(self) -> None:
        """Close the storage backend."""

    def wipe_db(self) -> None:
        """Wipe all data from the storage backend."""
        with self.session_factory() as session, session.begin():
            session.execute(delete(orm.AlleleFrequencyData))

    def add_allele_frequency(self, caf: CohortAlleleFrequencyStudyResult) -> None:
        """Add allele frequency data to the database. Will skip conflicts.

        :param caf: Cohort allele frequency study result object to insert into the DB
        """
        db_entity = mapper_registry.to_db_entity(caf)
        stmt = insert(orm.AlleleFrequencyData).on_conflict_do_nothing()

        with self.session_factory() as session, session.begin():
            session.execute(stmt, db_entity.to_dict())
