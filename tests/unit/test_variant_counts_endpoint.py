"""Test variant counts endpoint functionality."""

from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from helpers import TEST_VARIANT

from anyvlm.anyvar.base_client import AnyVarClientConnectionError
from anyvlm.main import app as vlm_restapi

TEST_QUERY = {
    "assemblyId": TEST_VARIANT.assembly.value,
    "referenceName": TEST_VARIANT.chromosome,
    "start": TEST_VARIANT.position,
    "referenceBases": TEST_VARIANT.ref,
    "alternateBases": TEST_VARIANT.alt,
}
ENDPOINT = "/variant_counts"


@pytest.fixture(scope="session")
def beacon_handovers_and_meta():
    """Create test fixture for beaconHandovers and meta"""
    return {
        "beaconHandovers": [
            {
                "handoverType": {
                    "id": "GREGoR-NCH",
                    "label": "GREGoR AnyVLM Reference",
                },
                "url": "https://variants.gregorconsortium.org/",
            }
        ],
        "meta": {
            "apiVersion": "v1.0",
            "beaconId": "org.anyvlm.gregor",
            "returnedSchemas": [
                {
                    "entityType": "genomicVariant",
                    "schema": "ga4gh-beacon-variant-v2.0.0",
                }
            ],
        },
    }


@pytest.fixture(scope="session")
def expected_response_with_match(beacon_handovers_and_meta):
    """Create test fixture for response with match found in AnyVar"""
    response = {
        "responseSummary": {"exists": True, "numTotalResults": 1},
        "response": {
            "resultSets": [
                {
                    "exists": True,
                    "id": "GREGoR-NCH Homozygous",
                    "results": [],
                    "resultsCount": 0,
                    "setType": "genomicVariant",
                },
                {
                    "exists": True,
                    "id": "GREGoR-NCH Heterozygous",
                    "results": [],
                    "resultsCount": 1,
                    "setType": "genomicVariant",
                },
                {
                    "exists": True,
                    "id": "GREGoR-NCH Hemizygous",
                    "results": [],
                    "resultsCount": 0,
                    "setType": "genomicVariant",
                },
            ]
        },
    }
    beacon_handovers_and_meta.update(response)
    return beacon_handovers_and_meta


@pytest.fixture(scope="session")
def expected_response_with_no_match(beacon_handovers_and_meta):
    """Create test fixture for response with match not found in AnyVar"""
    response = {
        "responseSummary": {"exists": False, "numTotalResults": 0},
        "response": {"resultSets": []},
    }
    beacon_handovers_and_meta.update(response)
    return beacon_handovers_and_meta


@pytest.fixture
def client_with_populated_dbs(
    anyvar_populated_python_client,
    populated_postgres_storage,
):
    """Create test fixture for client where expected variant is registered in AnyVar, and CAF records exist."""
    vlm_restapi.state.anyvar_client = anyvar_populated_python_client
    vlm_restapi.state.anyvlm_storage = populated_postgres_storage

    client = TestClient(vlm_restapi)

    yield client

    del vlm_restapi.state.anyvar_client
    del vlm_restapi.state.anyvlm_storage


@pytest.fixture
def client_with_registered_variant_no_caf(
    anyvar_populated_python_client,
    postgres_storage,
):
    """Create test fixture for client where expected variant is registered in AnyVar, but no CAF records exist."""
    vlm_restapi.state.anyvar_client = anyvar_populated_python_client
    vlm_restapi.state.anyvlm_storage = postgres_storage

    client = TestClient(vlm_restapi)

    yield client

    del vlm_restapi.state.anyvar_client
    del vlm_restapi.state.anyvlm_storage


@pytest.fixture
def client_with_variant_not_registered(
    anyvar_minimal_populated_python_client,
    populated_postgres_storage,
):
    """Create test fixture for client where expected variant is not registered in AnyVar."""
    vlm_restapi.state.anyvar_client = anyvar_minimal_populated_python_client
    vlm_restapi.state.anyvlm_storage = populated_postgres_storage

    client = TestClient(vlm_restapi)

    yield client

    del vlm_restapi.state.anyvar_client
    del vlm_restapi.state.anyvlm_storage


@pytest.mark.vcr
def test_variant_counts_endpoint_match_found(
    client_with_populated_dbs, expected_response_with_match
):
    """Test case where variant counts returns a match"""
    response = client_with_populated_dbs.get(ENDPOINT, params=TEST_QUERY)

    assert response.status_code == HTTPStatus.OK

    assert response.json() == expected_response_with_match


@pytest.mark.vcr
def test_variant_counts_endpoint_no_results(
    client_with_registered_variant_no_caf, expected_response_with_no_match
):
    """Test case where variant counts does not return a match"""
    response = client_with_registered_variant_no_caf.get(ENDPOINT, params=TEST_QUERY)

    assert response.status_code == HTTPStatus.OK
    assert response.json() == expected_response_with_no_match


@pytest.mark.vcr
def test_variant_counts_endpoint_not_registered(
    client_with_variant_not_registered,
):
    """Test case where variant not registered in AnyVar"""
    response = client_with_variant_not_registered.get(ENDPOINT, params=TEST_QUERY)

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {
        "detail": "Variant GRCh38 Y-2781761-C-A is not registered in AnyVar"
    }


@pytest.mark.vcr
def test_variant_counts_endpoint_anyvar_unavailable(
    client_with_populated_dbs,
    monkeypatch,
):
    """Test case where AnyVarClientConnectionError is raised"""

    def mock_get_registered_allele(*args, **kwargs):
        raise AnyVarClientConnectionError

    anyvar_client = client_with_populated_dbs.app.state.anyvar_client
    monkeypatch.setattr(
        anyvar_client,
        "get_registered_allele",
        mock_get_registered_allele,
    )

    response = client_with_populated_dbs.get(ENDPOINT, params=TEST_QUERY)

    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert response.json() == {"detail": "Unable to establish AnyVar connection"}
