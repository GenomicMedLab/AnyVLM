"""Define REST API schemas"""

from enum import Enum
from typing import Literal

from pydantic import BaseModel

from anyvlm import __version__


class ServiceEnvironment(str, Enum):
    """Define current runtime environment."""

    LOCAL = "local"
    TEST = "test"
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


class ServiceOrganization(BaseModel):
    """Define service_info response for organization field"""

    name: Literal["Biocommons"] = "Biocommons"
    url: Literal["https://biocommons.org/"] = "https://biocommons.org/"


class ServiceType(BaseModel):
    """Define service_info response for type field"""

    group: Literal["org.biocommons"] = "org.biocommons"
    artifact: Literal["AnyVLM API"] = "AnyVLM API"
    version: str = __version__


SERVICE_DESCRIPTION = "An AnyVLM instance"


class ServiceInfo(BaseModel):
    """Define response structure for GA4GH /service_info endpoint."""

    id: Literal["org.biocommons.anyvlm"] = "org.biocommons.anyvlm"
    name: Literal["anyvlm"] = "anyvlm"
    type: ServiceType
    description: str = SERVICE_DESCRIPTION
    organization: ServiceOrganization
    contactUrl: Literal["Alex.Wagner@nationwidechildrens.org"] = (  # noqa: N815
        "Alex.Wagner@nationwidechildrens.org"
    )
    documentationUrl: Literal["https://github.com/genomicmedlab/anyvlm"] = (  # noqa: N815
        "https://github.com/genomicmedlab/anyvlm"
    )
    createdAt: Literal["2025-06-01T00:00:00Z"] = "2025-06-01T00:00:00Z"  # noqa: N815
    updatedAt: Literal["2025-06-01T00:00:00Z"] = "2025-06-01T00:00:00Z"  # noqa: N815
    environment: ServiceEnvironment
    version: str = __version__
