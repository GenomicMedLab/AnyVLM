"""Tests postgres storage implementation methods directly."""

import pytest
from ga4gh.core.models import iriReference
from ga4gh.va_spec.base import CohortAlleleFrequencyStudyResult
from ga4gh.vrs.models import Allele, LiteralSequenceExpression
from tests.conftest import return_cafs

from anyvlm.storage import orm
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

    def verify_row(db_record: orm.AlleleFrequencyData, expected_consequence: str):
        """Verify row"""
        assert db_record.vrs_id == "ga4gh:VA.J3Hi64dkKFKdnKIwB2419Qz3STDB2sJq"
        assert db_record.af == 0.000162232
        assert db_record.ac == 1
        assert db_record.an == 6164
        assert db_record.ac_het == 1
        assert db_record.ac_hom == 0
        assert db_record.consequence == expected_consequence
        assert db_record.filter == ["LowQual", "NO_HQ_GENOTYPES"]

    def insert_and_verify_rows(
        caf_obj: CohortAlleleFrequencyStudyResult, expected_consequences: list[str]
    ):
        """Insert caf record and verify rows"""
        postgres_storage.add_allele_frequency(caf_obj)

        rows = return_cafs(postgres_storage)
        assert len(rows) == len(expected_consequences)

        for index, consequence in enumerate(expected_consequences):
            db_record = rows[index]
            verify_row(db_record, consequence)

    caf = request.getfixturevalue(caf_fixture_name)
    expected_consequences = ["intron_variant"]

    # first insert
    insert_and_verify_rows(caf, expected_consequences=expected_consequences)

    # second insert
    insert_and_verify_rows(caf, expected_consequences=expected_consequences)

    # test composite key
    new_caf = caf.model_copy(deep=True)
    new_consequence = "missense_variant"
    new_caf.ancillaryResults["consequence"] = new_consequence
    expected_consequences.append(new_consequence)
    insert_and_verify_rows(new_caf, expected_consequences=expected_consequences)
