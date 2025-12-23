"""Test HTTP-based and Python AnyVar clients

These tests use VCR-style recordings for HTTP calls. In practice, there's obviously no
'true' behavior for search results, since it depends on what the AnyVar instance does
or doesn't contain -- so for the search tests, it's probably easiest to assume that the
variants deposited by the `put_objects` test are all that's in there (i.e. use a clean
AnyVar DB to record new test cassettes)
"""

import os

import pytest
from anyvar.anyvar import create_storage, create_translator
from ga4gh.vrs import models

from anyvlm.anyvar.base_client import BaseAnyVarClient
from anyvlm.anyvar.http_client import HttpAnyVarClient
from anyvlm.anyvar.python_client import PythonAnyVarClient


@pytest.fixture(scope="session")
def anyvar_postgres_uri():
    """Create test fixure for AnyVar postgres storage URI"""
    uri = os.environ.get(
        "ANYVLM_ANYVAR_TEST_STORAGE_URI",
        "postgresql://postgres:postgres@localhost:5432/anyvlm_anyvar_test",
    )
    return uri


@pytest.fixture
def anyvar_python_client(anyvar_postgres_uri: str) -> PythonAnyVarClient:
    """Create test fixture for AnyVar Python Client"""
    storage = create_storage(anyvar_postgres_uri)
    storage.wipe_db()
    translator = create_translator()
    return PythonAnyVarClient(translator, storage)


@pytest.fixture
def anyvar_http_client() -> HttpAnyVarClient:
    """Create test fixture for AnyVar HTTP client"""
    return HttpAnyVarClient()


@pytest.fixture
def anyvar_populated_python_client(
    anyvar_python_client: PythonAnyVarClient, alleles: dict
):
    """Create test fixture for populated AnyVar Python client"""
    for allele_fixture in alleles.values():
        if "vcf_expression" not in allele_fixture:
            continue
        anyvar_python_client.put_allele_expressions([allele_fixture["vcf_expression"]])
    return anyvar_python_client


@pytest.fixture
def anyvar_client(request):
    """Create test fixture for AnyVar Python or HTTP client"""
    return request.getfixturevalue(request.param)


UNPOPULATED_CLIENTS = [
    "anyvar_python_client",
    "anyvar_http_client",
]

POPULATED_CLIENTS = [
    "anyvar_populated_python_client",
    "anyvar_http_client",
]


@pytest.mark.vcr
@pytest.mark.parametrize("anyvar_client", UNPOPULATED_CLIENTS, indirect=True)
def test_get_registered_allele_expressions_unpopulated(
    anyvar_client: BaseAnyVarClient, alleles: dict
):
    """Test `get_registered_allele_expressions` for an unpopulated client"""
    for allele_fixture in alleles.values():
        if "vcf_expression" not in allele_fixture:
            continue
        assert (
            anyvar_client.get_registered_allele_expression(
                allele_fixture["vcf_expression"]
            )
            is None
        )


@pytest.mark.vcr
@pytest.mark.parametrize("anyvar_client", POPULATED_CLIENTS, indirect=True)
def test_get_registered_allele_expressions_populated(
    anyvar_client: BaseAnyVarClient, alleles: dict
):
    """Test `get_registered_allele_expressions` for a populated client"""
    for allele_fixture in alleles.values():
        if "vcf_expression" not in allele_fixture:
            continue
        assert anyvar_client.get_registered_allele_expression(
            allele_fixture["vcf_expression"]
        ) == models.Allele(**allele_fixture["variation"])


@pytest.mark.vcr
@pytest.mark.parametrize("anyvar_client", UNPOPULATED_CLIENTS, indirect=True)
def test_put_allele_expressions(anyvar_client: BaseAnyVarClient, alleles: dict):
    """Test `put_objects` for a basic test suite of variants"""
    for allele_fixture in alleles.values():
        if "vcf_expression" not in allele_fixture:
            continue
        results = anyvar_client.put_allele_expressions(
            [allele_fixture["vcf_expression"]]
        )
        assert results == [allele_fixture["variation"]["id"]]


@pytest.mark.vcr
@pytest.mark.parametrize("anyvar_client", POPULATED_CLIENTS, indirect=True)
def test_put_allele_expressions_handle_invalid(
    anyvar_client: BaseAnyVarClient, alleles: dict
):
    results = anyvar_client.put_allele_expressions(["Y-2781761-A-C"])  # wrong REF
    assert results == [None]

    allele_fixture = alleles["ga4gh:VA.yi7A2l0uIUMaInQaJnHU_B2Cf_OuZRJg"]
    results = anyvar_client.put_allele_expressions(
        ["Y-2781761-A-C", allele_fixture["vcf_expression"]]
    )
    assert results == [None, allele_fixture["variation"]["id"]]


@pytest.mark.vcr
@pytest.mark.parametrize("anyvar_client", POPULATED_CLIENTS, indirect=True)
def test_search_by_interval(anyvar_client: BaseAnyVarClient, alleles: dict):
    """Test `search_by_interval` for a couple of basic cases"""
    results = anyvar_client.search_by_interval(
        "ga4gh:SQ.8_liLu1aycC0tPQPFmUaGXJLDs5SbPZ5", 2781760, 2781760
    )
    assert sorted(results, key=lambda r: r.id) == [
        models.Allele(
            **alleles["ga4gh:VA.9VDxL0stMBOZwcTKw3yb3UoWQkpaI9OD"]["variation"]
        ),
        models.Allele(
            **alleles["ga4gh:VA.R4kbmdsn5VldGrBiAaByO5N9zM3qCSFw"]["variation"]
        ),
    ]
    results = anyvar_client.search_by_interval(
        "ga4gh:SQ.8_liLu1aycC0tPQPFmUaGXJLDs5SbPZ5", 2781760, 2781768
    )
    assert sorted(results, key=lambda r: r.id) == [
        models.Allele(
            **alleles["ga4gh:VA.9VDxL0stMBOZwcTKw3yb3UoWQkpaI9OD"]["variation"]
        ),
        models.Allele(
            **alleles["ga4gh:VA.R4kbmdsn5VldGrBiAaByO5N9zM3qCSFw"]["variation"]
        ),
        models.Allele(
            **alleles["ga4gh:VA.yi7A2l0uIUMaInQaJnHU_B2Cf_OuZRJg"]["variation"]
        ),
    ]


@pytest.mark.vcr
@pytest.mark.parametrize("anyvar_client", POPULATED_CLIENTS, indirect=True)
def test_search_by_interval_with_alias(anyvar_client: BaseAnyVarClient, alleles: dict):
    """Test use of sequence alias"""
    results = anyvar_client.search_by_interval("GRCh38.p1:Y", 2781760, 2781760)
    assert sorted(results, key=lambda r: r.id) == [
        models.Allele(
            **alleles["ga4gh:VA.9VDxL0stMBOZwcTKw3yb3UoWQkpaI9OD"]["variation"]
        ),
        models.Allele(
            **alleles["ga4gh:VA.R4kbmdsn5VldGrBiAaByO5N9zM3qCSFw"]["variation"]
        ),
    ]


@pytest.mark.vcr
@pytest.mark.parametrize("anyvar_client", POPULATED_CLIENTS, indirect=True)
def test_search_by_interval_unknown_alias(anyvar_client: BaseAnyVarClient):
    """Test handling response when sequence alias isn't recognized."""
    assert anyvar_client.search_by_interval("GRCh45.p1:Y", 2781760, 2781760) == []


@pytest.mark.vcr
@pytest.mark.parametrize("anyvar_client", POPULATED_CLIENTS, indirect=True)
def test_search_by_interval_unknown_accession(anyvar_client: BaseAnyVarClient):
    """Test handling response when accession ID isn't recognized"""
    results = anyvar_client.search_by_interval(
        "ga4gh:SQ.ZZZZZu1aycC0tPQPFmUaGXJLDs5SbPZ5", 2781760, 2781768
    )
    assert results == []


@pytest.mark.vcr
@pytest.mark.parametrize("anyvar_client", POPULATED_CLIENTS, indirect=True)
def test_search_by_interval_not_found(anyvar_client: BaseAnyVarClient):
    """Test handling response when no matching variants are found"""
    results = anyvar_client.search_by_interval(
        "ga4gh:SQ.8_liLu1aycC0tPQPFmUaGXJLDs5SbPZ5", 1, 100
    )
    assert results == []
