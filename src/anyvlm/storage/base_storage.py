"""Provide base storage implementation."""

from abc import ABC, abstractmethod

from ga4gh.va_spec.base import CohortAlleleFrequencyStudyResult


class StorageError(Exception):
    """Base AnyLM storage error."""


class IncompleteVAObjectError(StorageError):
    """Raise if provided VA object is missing fully-materialized properties required for storage"""


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
    def add_allele_frequency(self, caf: CohortAlleleFrequencyStudyResult) -> None:
        """Add allele frequency data to the database. Will skip conflicts.

        :param caf: Cohort allele frequency study result object to insert into the DB
        """
