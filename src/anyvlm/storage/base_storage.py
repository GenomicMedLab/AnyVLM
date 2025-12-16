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

        :param caf: Cohort allele frequency study result object to insert into the DB
        """

    @abstractmethod
    def get_caf_by_vrs_ids(
        self, vrs_ids: list[str]
    ) -> list[CohortAlleleFrequencyStudyResult]:
        """Retrieve cohort allele frequency study results by VRS IDs

        :param vrs_ids: List of VRS variation IDs
        :return: List of cohort allele frequency study results matching given VRS
            variation IDs. Will use iriReference for focusAllele
        """
