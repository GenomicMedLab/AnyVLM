import os

import pytest
from anyvar.anyvar import create_storage, create_translator
from ga4gh.vrs import models

from anyvlm.anyvar.python_client import PythonAnyVarClient


@pytest.fixture(scope="session")
def postgres_uri():
    uri = os.environ.get(
        "ANYVLM_ANYVAR_TEST_STORAGE_URI",
        "postgresql://postgres:postgres@localhost:5432/anyvlm_anyvar_test",
    )
    return uri


@pytest.fixture
def client(postgres_uri: str) -> PythonAnyVarClient:
    storage = create_storage(postgres_uri)
    storage.wipe_db()
    translator = create_translator()
    return PythonAnyVarClient(translator, storage)


@pytest.fixture
def populated_client(client: PythonAnyVarClient, alleles: dict):
    for allele_fixture in alleles.values():
        client.put_objects([models.Allele(**allele_fixture["variation"])])
    return client


def test_put_objects(client: PythonAnyVarClient, alleles: dict):
    """Test `put_objects` for a basic test suite of variants"""
    for allele_fixture in alleles.values():
        allele = models.Allele(**allele_fixture["variation"])
        result = client.put_objects([allele])
        assert result == [allele]


def test_put_objects_no_ids(client: PythonAnyVarClient, alleles: dict):
    """Test `put_objects` for objects with IDs/digest/etc removed"""
    for allele_fixture in alleles.values():
        allele = models.Allele(**allele_fixture["variation"])
        allele.id = None
        allele.digest = None
        allele.location.id = None
        allele.location.digest = None
        result = client.put_objects([allele])
        assert result == [models.Allele(**allele_fixture["variation"])]


def test_search_by_interval(populated_client: PythonAnyVarClient, alleles: dict):
    """Test `search_by_interval` for a couple of basic cases"""
    results = populated_client.search_by_interval(
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
    results = populated_client.search_by_interval(
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
def test_search_by_interval_with_alias(
    populated_client: PythonAnyVarClient, alleles: dict
):
    """Test use of sequence alias"""
    results = populated_client.search_by_interval("GRCh38.p1:Y", 2781760, 2781760)
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
def test_search_by_interval_unknown_alias(populated_client: PythonAnyVarClient):
    """Test handling response when sequence alias isn't recognized."""
    assert populated_client.search_by_interval("GRCh45.p1:Y", 2781760, 2781760) == []


def test_search_by_interval_unknown_accession(populated_client: PythonAnyVarClient):
    """Test handling response when accession ID isn't recognized"""
    results = populated_client.search_by_interval(
        "ga4gh:SQ.ZZZZZu1aycC0tPQPFmUaGXJLDs5SbPZ5", 2781760, 2781768
    )
    assert results == []


def test_search_by_interval_not_found(populated_client: PythonAnyVarClient):
    """Test handling response when no matching variants are found"""
    results = populated_client.search_by_interval(
        "ga4gh:SQ.8_liLu1aycC0tPQPFmUaGXJLDs5SbPZ5", 1, 100
    )
    assert results == []
