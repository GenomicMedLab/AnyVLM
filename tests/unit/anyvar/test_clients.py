"""Test HTTP-based and Python AnyVar clients

These tests use VCR-style recordings for HTTP calls. In practice, there's obviously no
'true' behavior for search results, since it depends on what the AnyVar instance does
or doesn't contain -- so for the search tests, it's probably easiest to assume that the
variants deposited by the `put_objects` test are all that's in there (i.e. use a clean
AnyVar DB to record new test cassettes)
"""

import pytest
from anyvar.anyvar import create_storage
from ga4gh.vrs import models

from anyvlm.anyvar.base_client import BaseAnyVarClient
from anyvlm.anyvar.http_client import HttpAnyVarClient


@pytest.fixture
def anyvar_http_client(anyvlm_postgres_uri: str) -> HttpAnyVarClient:
    """Create test fixture for AnyVar HTTP client"""
    storage = create_storage(anyvlm_postgres_uri)
    storage.wipe_db()
    return HttpAnyVarClient()


@pytest.fixture
def anyvar_populated_http_client(
    anyvar_http_client: HttpAnyVarClient, alleles: dict
) -> HttpAnyVarClient:
    """Create test fixture for populated AnyVar HTTP client"""
    for allele_fixture in alleles.values():
        if "vcf_expression" not in allele_fixture:
            continue
        anyvar_http_client.put_allele_expressions([allele_fixture["vcf_expression"]])
    return anyvar_http_client


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
    "anyvar_populated_http_client",
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
            anyvar_client.get_registered_allele(allele_fixture["vcf_expression"])
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
        assert anyvar_client.get_registered_allele(
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
