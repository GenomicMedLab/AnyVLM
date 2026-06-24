"""Test that get_cafs function works correctly"""

import pytest
from deepdiff import DeepDiff
from helpers import EXPECTED_VRS_ID, TEST_VARIANT, build_caf

from anyvlm.anyvar.python_client import PythonAnyVarClient
from anyvlm.functions.get_cafs import VariantLookupError, get_cafs
from anyvlm.storage.postgres import PostgresObjectStore
from anyvlm.utils.types import AnyVlmCohortAlleleFrequencyResult


@pytest.fixture
def expected_cafs(caf_iri: AnyVlmCohortAlleleFrequencyResult, alleles: dict):
    allele = alleles.get(EXPECTED_VRS_ID)
    if not allele:
        return []

    return [build_caf(caf_iri, allele_obj=allele["variation"])]


@pytest.mark.vcr
def test_get_cafs_results_returned(
    anyvar_populated_python_client: PythonAnyVarClient,
    populated_postgres_storage: PostgresObjectStore,
    expected_cafs: list[AnyVlmCohortAlleleFrequencyResult],
):
    """Test get_cafs when variants are registered and results are expected"""
    cafs = get_cafs(
        anyvar_populated_python_client,
        populated_postgres_storage,
        TEST_VARIANT.assembly,
        TEST_VARIANT.chromosome,
        TEST_VARIANT.position,
        TEST_VARIANT.ref,
        TEST_VARIANT.alt,
    )
    diff = DeepDiff(
        [caf.model_dump(exclude_none=True) for caf in cafs],
        [caf.model_dump(exclude_none=True) for caf in expected_cafs],
        ignore_order=True,
    )
    assert diff == {}


@pytest.mark.vcr
def test_get_cafs_no_results_returned(
    anyvar_populated_python_client: PythonAnyVarClient,
    postgres_storage: PostgresObjectStore,
):
    """Test get_cafs when variants are registered but no results are expected"""
    cafs: list[AnyVlmCohortAlleleFrequencyResult] = get_cafs(
        anyvar_populated_python_client,
        postgres_storage,
        TEST_VARIANT.assembly,
        TEST_VARIANT.chromosome,
        TEST_VARIANT.position,
        TEST_VARIANT.ref,
        TEST_VARIANT.alt,
    )
    assert cafs == []


@pytest.mark.vcr
def test_get_cafs_variant_not_registered(
    anyvar_minimal_populated_python_client: PythonAnyVarClient,
    populated_postgres_storage: PostgresObjectStore,
):
    """Test get_cafs raises exception due to variant not being registered"""
    with pytest.raises(VariantLookupError):
        get_cafs(
            anyvar_client=anyvar_minimal_populated_python_client,
            anyvlm_storage=populated_postgres_storage,
            assembly_id=TEST_VARIANT.assembly,
            reference_name=TEST_VARIANT.chromosome,
            start=TEST_VARIANT.position,
            reference_base=TEST_VARIANT.ref,
            alternate_base=TEST_VARIANT.alt,
        )
