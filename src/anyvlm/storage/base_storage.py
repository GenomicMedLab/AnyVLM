"""Provide base storage implementation."""

from abc import ABC, abstractmethod

from ga4gh.va_spec.base import CohortAlleleFrequencyStudyResult


class StorageError(Exception):
    """Base AnyLM storage error."""


class Storage(ABC):
    """Abstract base class for interacting with storage backends."""

    @abstractmethod
    def __init__(self, *args, **kwargs) -> None:
        """Initialize the storage backend."""

    @abstractmethod
    def close(self) -> None:
        """Close the storage backend."""

    @abstractmethod
    def wipe_db(self) -> None:
        """Wipe all data from the storage backend."""

    @abstractmethod
    def add_allele_frequencies(self, caf: CohortAlleleFrequencyStudyResult) -> None:
        """Add allele frequency data to the database. Will skip conflicts.

        NOTE: For now, this will only insert a single caf record into the database.
        Single insertion is used to do a simple test of the storage backend.
        Issue-34 will support batch insertion of caf records.

        :param caf: Cohort allele frequency study result object to insert into the DB
        """

    @property
    @abstractmethod
    def sanitized_url(self) -> str:
        """Return a sanitized URL (password masked) of the database connection string."""
