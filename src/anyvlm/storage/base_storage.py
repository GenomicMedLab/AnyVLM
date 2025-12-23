"""Provide base storage implementation."""

from abc import ABC, abstractmethod

from anyvlm.utils.types import AnyVlmCohortAlleleFrequencyResult


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
    def add_allele_frequencies(self, caf: AnyVlmCohortAlleleFrequencyResult) -> None:
        """Add allele frequency data to the database. Will skip conflicts.

        NOTE: For now, this will only insert a single caf record into the database.
        Single insertion is used to do a simple test of the storage backend.
        Issue-34 will support batch insertion of caf records.

        :param caf: Cohort allele frequency study result object to insert into the DB
        """

    @abstractmethod
    def get_caf_by_vrs_allele_id(
        self, vrs_allele_id: str
    ) -> list[AnyVlmCohortAlleleFrequencyResult]:
        """Retrieve cohort allele frequency study results by VRS Allele ID

        :param vrs_allele_id: VRS Allele ID to filter by
        :return: List of cohort allele frequency study results matching given VRS Allele
            ID. Will use iriReference for focusAllele
        """
