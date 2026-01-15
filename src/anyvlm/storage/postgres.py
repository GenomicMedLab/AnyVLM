"""Provide PostgreSQL-based storage implementation."""

from urllib.parse import urlparse

from sqlalchemy import create_engine, delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker

from anyvlm.storage import orm
from anyvlm.storage.base_storage import (
    Storage,
)
from anyvlm.storage.mapper_registry import mapper_registry
from anyvlm.storage.orm import create_tables
from anyvlm.utils.types import AnyVlmCohortAlleleFrequencyResult


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

    @property
    def sanitized_url(self) -> str:
        """Return a sanitized URL (password masked) of the database connection string."""
        parsed = urlparse(self.db_url)
        netloc = ""
        if parsed.username:
            netloc += parsed.username
            if parsed.password:
                netloc += ":****"
            netloc += "@"
        if parsed.hostname:
            netloc += f"{parsed.hostname}"
        if parsed.port:
            netloc += f":{parsed.port}"
        return f"{parsed.scheme}://{netloc}{parsed.path}"

    def add_allele_frequencies(
        self, cafs: list[AnyVlmCohortAlleleFrequencyResult]
    ) -> None:
        """Add allele frequency data to the database. Will skip conflicts.

        :param cafs: List of cohort allele frequency study result objects to insert
        """
        if not cafs:
            return

        db_entities = [mapper_registry.to_db_entity(caf) for caf in cafs]
        stmt = insert(orm.AlleleFrequencyData).on_conflict_do_nothing()

        with self.session_factory() as session, session.begin():
            session.execute(stmt, [entity.to_dict() for entity in db_entities])

    def get_caf_by_vrs_allele_id(
        self, vrs_allele_id: str
    ) -> list[AnyVlmCohortAlleleFrequencyResult]:
        """Retrieve cohort allele frequency study results by VRS Allele ID

        :param vrs_allele_id: VRS Allele ID to filter by
        :return: List of cohort allele frequency study results matching given VRS Allele
            ID. Will use iriReference for focusAllele
        """
        cafs: list[AnyVlmCohortAlleleFrequencyResult] = []
        with self.session_factory() as session:
            stmt = (
                select(orm.AlleleFrequencyData)
                .where(orm.AlleleFrequencyData.vrs_id == vrs_allele_id)
                .limit(self.MAX_ROWS)
            )
            db_objects = session.scalars(stmt).all()

            for db_object in db_objects:
                caf = mapper_registry.from_db_entity(db_object)
                cafs.append(caf)
        return cafs
