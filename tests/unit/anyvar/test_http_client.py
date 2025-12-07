"""Test HTTP-based AnyVar client

These tests use VCR-style recordings for HTTP calls. In practice, there's obviously no
'true' behavior for search results, since it depends on what the AnyVar instance does
or doesn't contain -- so it's probably easiest to assume that the variants deposited by
the `put_objects` test are all that's in there (i.e. use a clean AnyVar DB to record
new test cassettes)
"""

import pytest
from ga4gh.vrs import models

from anyvlm.anyvar.base_client import AnyVarConnectionError
from anyvlm.anyvar.http_client import HttpAnyVarClient


@pytest.fixture
def client() -> HttpAnyVarClient:
    return HttpAnyVarClient()


@pytest.mark.vcr
def test_put_objects(client: HttpAnyVarClient, alleles: dict):
    """Test `put_objects` for a basic test suite of variants"""
    for allele_fixture in alleles.values():
        allele = models.Allele(**allele_fixture["variation"])
        result = client.put_objects([allele])
        assert result == [allele]


@pytest.mark.vcr
def test_put_objects_no_ids(client: HttpAnyVarClient, alleles: dict):
    """Test `put_objects` for objects with IDs/digest/etc removed"""
    for allele_fixture in alleles.values():
        allele = models.Allele(**allele_fixture["variation"])
        allele.id = None
        allele.digest = None
        allele.location.id = None
        allele.location.digest = None
        result = client.put_objects([allele])
        assert result == [models.Allele(**allele_fixture["variation"])]


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
        models.Allele(
            **alleles["ga4gh:VA.xbX035HgURWIUAjn6x3cS26jafP8Q_bk"]["variation"]
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
            **alleles["ga4gh:VA.xbX035HgURWIUAjn6x3cS26jafP8Q_bk"]["variation"]
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
        models.Allele(
            **alleles["ga4gh:VA.xbX035HgURWIUAjn6x3cS26jafP8Q_bk"]["variation"]
        ),
    ]


@pytest.mark.vcr
def test_search_by_interval_unknown_alias(client: HttpAnyVarClient):
    """Test handling response when sequence alias isn't recognized.

    This specific behavior might currently be wrong in AnyVar, so this may need to be updated later.
    """
    with pytest.raises(AnyVarConnectionError):
        client.search_by_interval("GRCh45.p1:Y", 2781760, 2781760)


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
