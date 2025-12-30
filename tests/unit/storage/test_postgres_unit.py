"""Tests postgres storage implementation methods directly."""

import pytest
from ga4gh.core.models import iriReference
from ga4gh.va_spec.base import StudyGroup
from ga4gh.vrs.models import Allele, LiteralSequenceExpression, sequenceString
from sqlalchemy.exc import IntegrityError

from anyvlm.storage.postgres import PostgresObjectStore
from anyvlm.utils.types import AnyVlmCohortAlleleFrequencyResult, QualityMeasures


@pytest.fixture
def caf_allele(caf_iri: AnyVlmCohortAlleleFrequencyResult):
    """Create test fixture for CAF object that uses Allele for focusAllele

    Note: Allele is a dummy allele
    """
    caf_allele = caf_iri.model_copy(deep=True)
    caf_allele.focusAllele = Allele(
        id=caf_iri.focusAllele.root,  # type: ignore
        location=iriReference("locations.json#/1"),
        state=LiteralSequenceExpression(sequence=sequenceString("A")),
    )
    return caf_allele


@pytest.fixture
def caf_empty_cohort(caf_iri: AnyVlmCohortAlleleFrequencyResult):
    """Create test fixture for CAF object that uses empty cohort"""
    caf = caf_iri.model_copy(deep=True)
    caf.cohort = StudyGroup()  # type: ignore
    return caf


@pytest.mark.parametrize(
    ("db_url", "sanitized_db_url"),
    [
        (
            "postgresql://postgres:postgres@localhost:5432/anyvlm_test",
            "postgresql://postgres:****@localhost:5432/anyvlm_test",
        ),
        (
            "postgresql://postgres@localhost:5432/anyvlm_test",
            "postgresql://postgres@localhost:5432/anyvlm_test",
        ),
    ],
)
def test_sanitized_url(monkeypatch, db_url: str, sanitized_db_url: str):
    """Test that sanitized_url method works correctly"""
    monkeypatch.setattr(PostgresObjectStore, "__init__", lambda *_: None)
    object_store = PostgresObjectStore("")
    monkeypatch.setattr(object_store, "db_url", db_url, raising=False)
    assert object_store.db_url == db_url
    assert object_store.sanitized_url == sanitized_db_url


@pytest.mark.parametrize("caf_fixture_name", ["caf_iri", "caf_allele"])
def test_add_allele_frequencies(
    request, caf_fixture_name: str, postgres_storage: PostgresObjectStore
):
    """Test that add_allele_frequencies method works correctly"""
    caf = request.getfixturevalue(caf_fixture_name)
    try:
        postgres_storage.add_allele_frequencies(caf)
    except Exception as e:  # noqa: BLE001
        pytest.fail(f"add_allele_frequencies raised an exception: {e}")

    caf = AnyVlmCohortAlleleFrequencyResult(
        focusAllele=iriReference("ga4gh:VA.J3Hi64dkKFKdnKIwB2419Qz3STDB2sJq"),
        focusAlleleCount=1,
        locusAlleleCount=6164,
        focusAlleleFrequency=0.000162232,
        qualityMeasures=QualityMeasures(qcFilters=["LowQual", "NO_HQ_GENOTYPES"]),
        cohort=StudyGroup(name="rare disease"),  # type: ignore
    )  # type: ignore

    postgres_storage.add_allele_frequencies(caf)


def test_add_allele_frequencies_failures(
    postgres_storage: PostgresObjectStore,
    caf_empty_cohort: AnyVlmCohortAlleleFrequencyResult,
):
    """Test that add_allele_frequencies method fails correctly on bad input"""
    with pytest.raises(IntegrityError, match='null value in column "cohort"'):
        postgres_storage.add_allele_frequencies(caf_empty_cohort)
