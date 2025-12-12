"""Tests postgres storage implementation methods directly."""

import pytest
from ga4gh.core.models import iriReference
from ga4gh.va_spec.base import CohortAlleleFrequencyStudyResult
from ga4gh.vrs.models import Allele, LiteralSequenceExpression
from tests.conftest import return_cafs

from anyvlm.storage.postgres import PostgresObjectStore


@pytest.fixture
def caf_allele(caf_iri: CohortAlleleFrequencyStudyResult):
    """Create test fixture for CAF object that uses Allele for focusAllele

    Note: Allele is a dummy allele
    """
    caf_allele = caf_iri.model_copy(deep=True)
    caf_allele.focusAllele = Allele(
        id=caf_iri.focusAllele.root,
        location=iriReference("locations.json#/1"),
        state=LiteralSequenceExpression(sequence="A"),
    )
    return caf_allele


@pytest.mark.parametrize("caf_fixture_name", ["caf_iri", "caf_allele"])
def test_add_allele_frequency(
    request, caf_fixture_name: str, postgres_storage: PostgresObjectStore
):
    """Test that add_allele_frequency method works correctly"""
    caf = request.getfixturevalue(caf_fixture_name)

    def insert_and_verify_one_row():
        postgres_storage.add_allele_frequency(caf)

        rows = return_cafs(postgres_storage)
        assert len(rows) == 1

        db_record = rows[0]

        assert db_record.vrs_id == "ga4gh:VA.J3Hi64dkKFKdnKIwB2419Qz3STDB2sJq"
        assert db_record.cohort == "rare disease"
        assert db_record.an == 6164
        assert db_record.ac_het == 1
        assert db_record.ac_hom == 0
        assert db_record.filter == ["LowQual", "NO_HQ_GENOTYPES"]

    # first insert
    insert_and_verify_one_row()

    # second insert
    insert_and_verify_one_row()
