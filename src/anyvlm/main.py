"""Define core FastAPI app"""

import contextlib
import logging
import logging.config
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from urllib.parse import urlparse

import anyio
import yaml
from anyvar.anyvar import create_storage, create_translator
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, status
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from anyvlm import __version__
from anyvlm.anyvar.base_client import BaseAnyVarClient
from anyvlm.anyvar.http_client import HttpAnyVarClient
from anyvlm.anyvar.python_client import PythonAnyVarClient
from anyvlm.config import get_config
from anyvlm.restapi.vlm import router as vlm_router
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

load_dotenv()
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
    if connection_string and connection_string.startswith(("http://", "https://")):
        _logger.info(
            "AnyVar client factory initializing HTTP-based AnyVar client under hostname %s",
            connection_string,
        )
        return HttpAnyVarClient(connection_string)
    _logger.info(
        "AnyVar client factory initializing AnyVar instance directly; falling back on AnyVar-specific env vars"
    )
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

    _logger.info(
        "AnyVLM storage factory initializing object store instance via {%s -> %s}",
        storage.sanitized_url,
        storage,
    )
    return storage


async def _configure_logging() -> None:
    """Initialize logging.

    Either load settings from a file at env var ``ANYVLM_LOGGING_CONFIG``, or
    fall back on defaults.

    Note that the value provided at the config file env var must point to
    a) an existing path that is b) a file, or else an unhandled exception will be
    raised.
    """
    config_file = get_config().logging_config
    if config_file:
        with contextlib.suppress(Exception):
            async with await anyio.open_file(config_file, "r") as f:
                config = yaml.safe_load(await f.read())
            logging.config.dictConfig(config)
            _logger.info("Logging using configs set from %s", config_file)
            return
    logging.basicConfig(
        filename="anyvlm.log",
        format="[%(asctime)s] - %(name)s - %(levelname)s : %(message)s",
        level=logging.INFO,
    )
    if config_file:
        _logger.error(
            "Error in Logging Configuration located at %s. Falling back to default configs",
            config_file,
        )
    _logger.info("Logging with default configs.")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Configure FastAPI instance lifespan.

    :param app: FastAPI app instance
    :return: async context handler
    """
    await _configure_logging()
    app.state.anyvar_client = create_anyvar_client()
    app.state.anyvlm_storage = create_anyvlm_storage()
    yield
    app.state.anyvar_client.close()
    app.state.anyvlm_storage.close()


app = FastAPI(
    title="AnyVLM",
    description=SERVICE_DESCRIPTION,
    version=__version__,
    docs_url="/",
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
app.include_router(vlm_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> Response:
    """Override default FastAPI request validation to return 400, not 422

    This is part of the VLM response spec. Unfortunately, exception handler overrides get
    set app-wide, but we want to preserve 422 as a validation error response outside of
    the main VLM endpoint.

    :param request: incoming request
    :param exc: raised exception (based on the decorator, should always be RequestValidationError)
    :return: custom response with same error msg and HTTP 400 status code
    """
    if request.url.path == "/variant_counts":
        return JSONResponse(
            exc.errors(),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return await request_validation_exception_handler(request, exc)


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
