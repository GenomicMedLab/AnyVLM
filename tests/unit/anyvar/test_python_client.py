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
        if "vcf_expression" not in allele_fixture:
            continue
        client.put_allele_expressions([allele_fixture["vcf_expression"]])
    return client


def test_put_allele_expressions(client: PythonAnyVarClient, alleles: dict):
    """Test `put_allele_expressions` for a basic test suite of variants"""
    for allele_fixture in alleles.values():
        if "vcf_expression" not in allele_fixture:
            continue
        client.put_allele_expressions([allele_fixture["vcf_expression"]])


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
