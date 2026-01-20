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
    def add_allele_frequencies(
        self, cafs: list[AnyVlmCohortAlleleFrequencyResult]
    ) -> None:
        """Add allele frequency data to the database. Will skip conflicts.

        :param cafs: List of cohort allele frequency study result objects to insert
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
