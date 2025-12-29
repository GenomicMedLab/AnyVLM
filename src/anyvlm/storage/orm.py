"""SQLAlchemy ORM models for AnyVLM database schema."""

from anyvar.utils.funcs import camel_case_to_snake_case
from sqlalchemy import (
    Integer,
    String,
    create_engine,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    sessionmaker,
)
from sqlalchemy.orm.decl_api import declared_attr


class Base(DeclarativeBase):
    """Base class for all AnyVLM ORM models."""

    @declared_attr.directive
    def __tablename__(cls) -> str:  # noqa: N805 (param name here should be 'cls', not 'self')
        # Default table name = class name, transformed from PascalCase into snake_case and pluralized.
        # Example: The table name created by the "AlleleFrequencyData" ORM class is `allele_frequency_data`
        # NOTE: Classes/tables that require a different pluralization scheme should override this function.
        return camel_case_to_snake_case(cls.__name__, False) + "s"

    def to_dict(self) -> dict:
        """Convert the model fields to a dictionary (non-recursive)."""
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }


class AlleleFrequencyData(Base):
    """AnyVLM ORM model for allele frequency data table."""

    @declared_attr.directive
    def __tablename__(self) -> str:
        return "allele_frequency_data"

    vrs_id: Mapped[str] = mapped_column(String, primary_key=True)
    cohort: Mapped[str] = mapped_column(String, index=True, nullable=False)
    an: Mapped[int] = mapped_column(Integer, nullable=False)
    ac: Mapped[int] = mapped_column(Integer, nullable=False)
    ac_het: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ac_hom: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ac_hemi: Mapped[int | None] = mapped_column(Integer, nullable=True)
    filter: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)


def create_tables(db_url: str) -> None:
    """Create all tables in the database.

    :param db_url: Database connection URL (e.g., postgresql://user:pass@host:port/db)
    """
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)


def session_factory(db_url: str) -> sessionmaker:
    """Create a SQLAlchemy session factory.

    Returns a sessionmaker factory that should be used to create sessions.
    Follows SQLAlchemy 2.0 recommended semantics where the session lifecycle
    is managed externally using context managers.

    Example usage:

    >>> sf = session_factory(db_url)
    >>> with sf() as session:
    >>>     with session.begin(): # Perform database operations
    >>>         session.add(some_object)
    >>>         session.execute(some_query)
    >>> # Transaction from session.begin() automatically commits if no exceptions occur
    >>> # Session automatically closes

    See: https://docs.sqlalchemy.org/en/20/orm/session_basics.html#using-a-sessionmaker

    :param db_url: Database connection URL (e.g., postgresql://user:pass@host:port/db)
    :return: SQLAlchemy sessionmaker factory
    """
    engine = create_engine(db_url)
    return sessionmaker(bind=engine)
