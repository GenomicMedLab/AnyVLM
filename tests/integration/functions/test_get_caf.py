"""Test that get_caf function works correctly"""

import pytest
from deepdiff import DeepDiff
from ga4gh.core.models import iriReference
from ga4gh.va_spec.base import CohortAlleleFrequencyStudyResult

from anyvlm.anyvar.python_client import PythonAnyVarClient
from anyvlm.anyvlm import AnyVLM
from anyvlm.functions.get_caf import get_caf
from anyvlm.storage.postgres import PostgresObjectStore

POS = 2781760
REFGET_AC = "SQ.8_liLu1aycC0tPQPFmUaGXJLDs5SbPZ5"
GA4GH_SEQ_ID = f"ga4gh:{REFGET_AC}"


@pytest.fixture
def alleles_to_add(alleles: dict):
    """Create test fixture for alleles whose sequence reference matches REFGET_AC"""
    return [
        value["variation"]
        for value in alleles.values()
        if value["variation"]["location"]["sequenceReference"]["refgetAccession"]
        == REFGET_AC
    ]


@pytest.fixture
def alleles_in_range(alleles_to_add):
    """Create test fixture for alleles overlapping POS"""
    return [
        variation
        for variation in alleles_to_add
        if variation["location"]["start"] <= POS and variation["location"]["end"] >= POS
    ]


@pytest.fixture
def populated_postgres_storage(
    postgres_storage: PostgresObjectStore,
    alleles_to_add: list[dict],
    caf_iri: CohortAlleleFrequencyStudyResult,
):
    for variation in alleles_to_add:
        caf_copy = caf_iri.model_copy(deep=True)
        caf_copy.focusAllele = iriReference(root=variation["id"])
        postgres_storage.add_allele_frequency(caf_copy)
    return postgres_storage


@pytest.fixture
def anyvlm_populated_client(populated_postgres_storage):
    """Define test fixture for anyvlm"""
    return AnyVLM(populated_postgres_storage)


@pytest.fixture
def expected_cafs(caf_iri, alleles_in_range):
    cafs = []
    for variation in alleles_in_range:
        new_caf = caf_iri.model_copy(deep=True)
        new_caf.focusAllele = variation
        cafs.append(new_caf)
    return cafs


@pytest.mark.vcr
def test_get_caf_results_returned(
    anyvar_populated_python_client: PythonAnyVarClient,
    anyvlm_populated_client: AnyVLM,
    expected_cafs: list[CohortAlleleFrequencyStudyResult],
):
    """Test get_caf when results are expected"""
    cafs = get_caf(
        anyvar_populated_python_client,
        anyvlm_populated_client,
        GA4GH_SEQ_ID,
        POS,
        POS,
    )
    diff = DeepDiff(
        [caf.model_dump(exclude_none=True) for caf in cafs],
        [caf.model_dump(exclude_none=True) for caf in expected_cafs],
        ignore_order=True,
    )
    assert diff == {}


@pytest.mark.vcr
def test_get_caf_no_results(
    anyvar_populated_python_client: PythonAnyVarClient,
    anyvlm_populated_client: AnyVLM,
):
    """Test get_caf when no results are expected"""
    cafs = get_caf(
        anyvar_populated_python_client,
        anyvlm_populated_client,
        "GRCh45.p1:Y",
        POS,
        POS,
    )
    assert cafs == []
