"""Define core FastAPI app"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from anyvar.anyvar import create_storage, create_translator
from fastapi import FastAPI

from anyvlm import __version__
from anyvlm.anyvar.base_client import BaseAnyVarClient
from anyvlm.anyvar.http_client import HttpAnyVarClient
from anyvlm.anyvar.python_client import PythonAnyVarClient
from anyvlm.config import get_config
from anyvlm.schemas.common import (
    SERVICE_DESCRIPTION,
    ServiceInfo,
    ServiceOrganization,
    ServiceType,
)
from anyvlm.storage.base_storage import Storage
from anyvlm.utils.types import (
    EndpointTag,
)

_logger = logging.getLogger(__name__)


def create_anyvar_client(
    connection_string: str | None = None,
) -> BaseAnyVarClient:
    """Construct new AnyVar client instance

    If given a string for connecting to an AnyVar instance via HTTP requests, then
    create an HTTP-based client. Otherwise, try to use AnyVar resource factory functions
    for standing up a Python-based client. In the latter case, see the AnyVar documentation
    for configuration info (i.e. environment variables)

    :param connection_string: description of connection param
    :return: client instance
    """
    if not connection_string:
        connection_string = get_config().anyvar_uri
    if connection_string.startswith("http://"):
        _logger.info(
            "Initializing HTTP-based AnyVar client under hostname %s", connection_string
        )
        return HttpAnyVarClient(connection_string)
    _logger.info("Initializing AnyVar instance directly")
    storage = create_storage()
    translator = create_translator()
    return PythonAnyVarClient(translator, storage)


def create_anyvlm_storage(uri: str | None = None) -> Storage:
    """Provide factory to create storage based on `uri`, the ANYVLM_STORAGE_URI
    environment value, or the default value if neither is provided.

    The URI format is as follows:

    `postgresql://[username]:[password]@[domain]/[database]`

    :param uri: AnyVLM storage URI
    :raises ValueError: if the URI scheme is not supported
    :return: AnyVLM storage instance
    """
    if not uri:
        uri = get_config().storage_uri

    parsed_uri = urlparse(uri)
    if parsed_uri.scheme == "postgresql":
        from anyvlm.storage.postgres import PostgresObjectStore  # noqa: PLC0415

        storage = PostgresObjectStore(uri)
    else:
        msg = f"URI scheme {parsed_uri.scheme} is not implemented"
        raise ValueError(msg)

    _logger.debug("create_storage: %s → %s}", storage.sanitized_url, storage)
    return storage


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Configure FastAPI instance lifespan.

    :param app: FastAPI app instance
    :return: async context handler
    """
    app.state.anyvar_client = create_anyvar_client()
    app.state.anyvlm_storage = create_anyvlm_storage()
    yield
    app.state.anyvar_client.close()
    app.state.anyvlm_storage.close()


app = FastAPI(
    title="AnyVLM",
    description=SERVICE_DESCRIPTION,
    version=__version__,
    license={
        "name": "Apache 2.0",
        "url": "https://github.com/genomicmedlab/anyvlm/blob/main/LICENSE",
    },
    contact={
        "name": "Alex H. Wagner",
        "email": "Alex.Wagner@nationwidechildrens.org",
        "url": "https://www.nationwidechildrens.org/specialties/institute-for-genomic-medicine/research-labs/wagner-lab",
    },
    swagger_ui_parameters={"tryItOutEnabled": True},
    lifespan=lifespan,
)


@app.get(
    "/service-info",
    summary="Get basic service information",
    description="Retrieve service metadata, such as versioning and contact info. Structured in conformance with the [GA4GH service info API specification](https://www.ga4gh.org/product/service-info/)",
    tags=[EndpointTag.META],
)
def service_info() -> ServiceInfo:
    """Provide service info per GA4GH Service Info spec"""
    return ServiceInfo(
        organization=ServiceOrganization(),
        type=ServiceType(),
        environment=get_config().env,
    )
