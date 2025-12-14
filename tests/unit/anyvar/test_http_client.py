"""Test HTTP-based AnyVar client

These tests use VCR-style recordings for HTTP calls. In practice, there's obviously no
'true' behavior for search results, since it depends on what the AnyVar instance does
or doesn't contain -- so for the search tests, it's probably easiest to assume that the
variants deposited by the `put_objects` test are all that's in there (i.e. use a clean
AnyVar DB to record new test cassettes)
"""

import pytest
from ga4gh.vrs import models

from anyvlm.anyvar.base_client import AnyVarClientError
from anyvlm.anyvar.http_client import HttpAnyVarClient


@pytest.fixture
def client() -> HttpAnyVarClient:
    return HttpAnyVarClient()


@pytest.mark.vcr
def test_put_allele_expressions(client: HttpAnyVarClient, alleles: dict):
    """Test `put_allele_expressions` for a basic test suite of variants"""
    for allele_fixture in alleles.values():
        if "vcf_expression" not in allele_fixture:
            continue
        results = client.put_allele_expressions([allele_fixture["vcf_expression"]])
        assert results == [allele_fixture["variation"]["id"]]


# TODO this fails for now until anyvar #355
# @pytest.mark.vcf
# def test_put_allele_expressions_handle_invalid(client: HttpAnyVarClient, alleles: dict):
#     results = client.put_allele_expressions(["Y-2781761-A-C"])  # wrong REF
#     assert results == [None]
#
#     allele_fixture = alleles["ga4gh:VA.yi7A2l0uIUMaInQaJnHU_B2Cf_OuZRJg"]
#     results = client.put_allele_expressions(
#         ["Y-2781761-A-C", allele_fixture["vcf_expression"]]
#     )
#     assert results == [None, allele_fixture["variation"]["id"]]


def test_put_allele_expressions_catch_httperror():
    """Test handling HTTP failure

    DO NOT wrap this with pyVCR -- as far as I can tell, it won't write a cassette for the
    HTTP timeout, but will still call a failure in `--record-mode=None`
    """
    client = HttpAnyVarClient("http://localhost:4321")  # use a currently-inactive port
    with pytest.raises(AnyVarClientError):
        client.put_allele_expressions(["1-1000000-A-T"])


@pytest.mark.vcr
def test_search_by_interval(client: HttpAnyVarClient, alleles: dict):
    """Test `search_by_interval` for a couple of basic cases"""
    results = client.search_by_interval(
        "ga4gh:SQ.8_liLu1aycC0tPQPFmUaGXJLDs5SbPZ5", 2781760, 2781760
    )
    assert sorted(results, key=lambda r: r.id) == [
        models.Allele(
            **alleles["ga4gh:VA.9VDxL0stMBOZwcTKw3yb3UoWQkpaI9OD"]["variation"]
        ),
        models.Allele(
            **alleles["ga4gh:VA.IM4QyU9D2kTJzeftUBBD4Vcd1peq0dn1"]["variation"]
        ),
    ]
    results = client.search_by_interval(
        "ga4gh:SQ.8_liLu1aycC0tPQPFmUaGXJLDs5SbPZ5", 2781760, 2781768
    )
    assert sorted(results, key=lambda r: r.id) == [
        models.Allele(
            **alleles["ga4gh:VA.9VDxL0stMBOZwcTKw3yb3UoWQkpaI9OD"]["variation"]
        ),
        models.Allele(
            **alleles["ga4gh:VA.IM4QyU9D2kTJzeftUBBD4Vcd1peq0dn1"]["variation"]
        ),
        models.Allele(
            **alleles["ga4gh:VA.yi7A2l0uIUMaInQaJnHU_B2Cf_OuZRJg"]["variation"]
        ),
    ]


@pytest.mark.vcr
def test_search_by_interval_with_alias(client: HttpAnyVarClient, alleles: dict):
    """Test use of sequence alias"""
    results = client.search_by_interval("GRCh38.p1:Y", 2781760, 2781760)
    assert sorted(results, key=lambda r: r.id) == [
        models.Allele(
            **alleles["ga4gh:VA.9VDxL0stMBOZwcTKw3yb3UoWQkpaI9OD"]["variation"]
        ),
        models.Allele(
            **alleles["ga4gh:VA.IM4QyU9D2kTJzeftUBBD4Vcd1peq0dn1"]["variation"]
        ),
    ]


@pytest.mark.vcr
def test_search_by_interval_unknown_alias(client: HttpAnyVarClient):
    """Test handling response when sequence alias isn't recognized."""
    assert client.search_by_interval("GRCh45.p1:Y", 2781760, 2781760) == []


@pytest.mark.vcr
def test_search_by_interval_unknown_accession(client: HttpAnyVarClient):
    """Test handling response when accession ID isn't recognized"""
    results = client.search_by_interval(
        "ga4gh:SQ.ZZZZZu1aycC0tPQPFmUaGXJLDs5SbPZ5", 2781760, 2781768
    )
    assert results == []


@pytest.mark.vcr
def test_search_by_interval_not_found(client: HttpAnyVarClient):
    """Test handling response when no matching variants are found"""
    results = client.search_by_interval(
        "ga4gh:SQ.8_liLu1aycC0tPQPFmUaGXJLDs5SbPZ5", 1, 100
    )
    assert results == []
