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

    @property
    @abstractmethod
    def sanitized_url(self) -> str:
        """Return a sanitized URL (password masked) of the database connection string."""

    @abstractmethod
    def add_allele_frequencies(self, caf: CohortAlleleFrequencyStudyResult) -> None:
        """Add allele frequency data to the database. Will skip conflicts.

        NOTE: For now, this will only insert a single caf record into the database.
        Single insertion is used to do a simple test of the storage backend.
        Issue-34 will support batch insertion of caf records.

        :param caf: Cohort allele frequency study result object to insert into the DB
        """

    @abstractmethod
    def get_caf_by_vrs_allele_ids(
        self, vrs_allele_ids: list[str]
    ) -> list[CohortAlleleFrequencyStudyResult]:
        """Retrieve cohort allele frequency study results by VRS Allele IDs

        :param vrs_allele_ids: List of VRS Allele IDs
        :return: List of cohort allele frequency study results matching given VRS
            Allele IDs. Will use iriReference for focusAllele
        """
