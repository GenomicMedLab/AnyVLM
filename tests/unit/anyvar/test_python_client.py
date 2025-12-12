import pytest
from ga4gh.vrs import models

from anyvlm.anyvar.base_client import UnidentifiedObjectError
from anyvlm.anyvar.python_client import PythonAnyVarClient


def test_put_objects(anyvar_python_client: PythonAnyVarClient, alleles: dict):
    """Test `put_objects` for a basic test suite of variants"""
    for allele_fixture in alleles.values():
        allele = models.Allele(**allele_fixture["variation"])
        anyvar_python_client.put_objects([allele])


def test_put_objects_no_ids(anyvar_python_client: PythonAnyVarClient, alleles: dict):
    """Test `put_objects` for objects with IDs/digest/etc removed"""
    allele_iter = iter(alleles.values())
    allele = models.Allele(**next(allele_iter)["variation"])
    allele.id = None
    other_allele = models.Allele(**next(allele_iter)["variation"])
    with pytest.raises(UnidentifiedObjectError):
        anyvar_python_client.put_objects([other_allele, allele])


def test_search_by_interval(
    anyvar_populated_python_client: PythonAnyVarClient, alleles: dict
):
    """Test `search_by_interval` for a couple of basic cases"""
    results = anyvar_populated_python_client.search_by_interval(
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
    results = anyvar_populated_python_client.search_by_interval(
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
    anyvar_populated_python_client: PythonAnyVarClient, alleles: dict
):
    """Test use of sequence alias"""
    results = anyvar_populated_python_client.search_by_interval(
        "GRCh38.p1:Y", 2781760, 2781760
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


@pytest.mark.vcr
def test_search_by_interval_unknown_alias(
    anyvar_populated_python_client: PythonAnyVarClient,
):
    """Test handling response when sequence alias isn't recognized."""
    assert (
        anyvar_populated_python_client.search_by_interval(
            "GRCh45.p1:Y", 2781760, 2781760
        )
        == []
    )


def test_search_by_interval_unknown_accession(
    anyvar_populated_python_client: PythonAnyVarClient,
):
    """Test handling response when accession ID isn't recognized"""
    results = anyvar_populated_python_client.search_by_interval(
        "ga4gh:SQ.ZZZZZu1aycC0tPQPFmUaGXJLDs5SbPZ5", 2781760, 2781768
    )
    assert results == []


def test_search_by_interval_not_found(
    anyvar_populated_python_client: PythonAnyVarClient,
):
    """Test handling response when no matching variants are found"""
    results = anyvar_populated_python_client.search_by_interval(
        "ga4gh:SQ.8_liLu1aycC0tPQPFmUaGXJLDs5SbPZ5", 1, 100
    )
    assert results == []
