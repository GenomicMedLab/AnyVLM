"""Test that get_caf function works correctly"""

from dataclasses import dataclass

import pytest
from deepdiff import DeepDiff
from ga4gh.core.models import iriReference
from ga4gh.vrs.models import Allele

from anyvlm.anyvar.python_client import PythonAnyVarClient
from anyvlm.functions.get_caf import VariantNotRegisteredError, get_caf
from anyvlm.storage.postgres import PostgresObjectStore
from anyvlm.utils.types import AnyVlmCohortAlleleFrequencyResult, GrcAssemblyId


@dataclass(frozen=True, slots=True)
class TestVariant:
    """Dataclass for test variant"""

    assembly: GrcAssemblyId
    chromosome: str
    position: int
    ref: str
    alt: str


EXPECTED_VRS_ID = "ga4gh:VA.9VDxL0stMBOZwcTKw3yb3UoWQkpaI9OD"
TEST_VARIANT = TestVariant(
    assembly=GrcAssemblyId.GRCH38,
    chromosome="chrY",
    position=2781761,
    ref="C",
    alt="A",
)


def build_caf(
    base_caf: AnyVlmCohortAlleleFrequencyResult,
    allele_id: str | None = None,
    allele_obj: dict | None = None,
):
    """Build a caf object with the given allele_id or allele_obj"""
    caf = base_caf.model_copy(deep=True)
    if allele_id:
        caf.focusAllele = iriReference(root=allele_id)
    elif allele_obj:
        caf.focusAllele = Allele(**allele_obj)
    else:
        msg = "One of allele_id or allele_obj must be provided"
        raise ValueError(msg)

    return caf


@pytest.fixture
def anyvar_minimal_populated_python_client(
    anyvar_python_client: PythonAnyVarClient, alleles: dict
):
    """AnyVar client populated with allele alleles except the expected one"""
    vcf_expressions = [
        allele_fixture["vcf_expression"]
        for allele_fixture in alleles.values()
        if allele_fixture.get("vcf_expression")
        and allele_fixture["variation"]["id"] != EXPECTED_VRS_ID
    ]
    anyvar_python_client.put_allele_expressions(vcf_expressions)

    return anyvar_python_client


@pytest.fixture
def populated_postgres_storage(
    postgres_storage: PostgresObjectStore,
    alleles: dict,
    caf_iri: AnyVlmCohortAlleleFrequencyResult,
):
    """Populate the postgres storage with allele frequencies for testing"""
    for allele in alleles.values():
        caf = build_caf(caf_iri, allele_id=allele["variation"]["id"])
        postgres_storage.add_allele_frequencies(caf)
    return postgres_storage


@pytest.fixture
def expected_cafs(caf_iri: AnyVlmCohortAlleleFrequencyResult, alleles: dict):
    allele = alleles.get(EXPECTED_VRS_ID)
    if not allele:
        return []

    return [build_caf(caf_iri, allele_obj=allele["variation"])]


@pytest.mark.vcr
def test_get_caf_results_returned(
    anyvar_populated_python_client: PythonAnyVarClient,
    populated_postgres_storage: PostgresObjectStore,
    expected_cafs: list[AnyVlmCohortAlleleFrequencyResult],
):
    """Test get_caf when variants are registered and results are expected"""
    cafs = get_caf(
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
def test_get_caf_no_results_returned(
    anyvar_populated_python_client: PythonAnyVarClient,
    postgres_storage: PostgresObjectStore,
):
    """Test get_caf when variants are registered but no results are expected"""
    cafs = get_caf(
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
def test_get_caf_variant_not_registered(
    anyvar_minimal_populated_python_client: PythonAnyVarClient,
    populated_postgres_storage: PostgresObjectStore,
):
    """Test get_caf raises exception due to variant not being registered"""
    with pytest.raises(
        VariantNotRegisteredError,
        match="Variant GRCh38 chrY-2781761-C-A is not registered in AnyVar",
    ):
        get_caf(
            anyvar_minimal_populated_python_client,
            populated_postgres_storage,
            TEST_VARIANT.assembly,
            TEST_VARIANT.chromosome,
            TEST_VARIANT.position,
            TEST_VARIANT.ref,
            TEST_VARIANT.alt,
        )
