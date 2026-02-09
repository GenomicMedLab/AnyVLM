import pytest
from fastapi.testclient import TestClient

from anyvlm.main import app as vlm_restapi


@pytest.fixture
def restapi_client(anyvar_populated_python_client, postgres_storage):
    vlm_restapi.state.anyvar_client = anyvar_populated_python_client
    vlm_restapi.state.anyvlm_storage = postgres_storage
    return TestClient(app=vlm_restapi)


def test_variantcounts_handle_unrecognized(restapi_client: TestClient):
    pass


# TODO test that unrecognized variant -> 200 OK

# TODO test that invalid request -> 400
