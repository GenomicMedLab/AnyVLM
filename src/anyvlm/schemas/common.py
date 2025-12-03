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
    artifact: Literal["VLM API"] = "VLM API"
    version: str = __version__


SERVICE_DESCRIPTION = "A VLM-In-A-Box instance"


class ServiceInfo(BaseModel):
    """Define response structure for GA4GH /service_info endpoint."""

    id: Literal["org.biocommons.vlm"] = "org.biocommons.vlm"
    name: Literal["vlm"] = "vlm"
    type: ServiceType
    description: str = SERVICE_DESCRIPTION
    organization: ServiceOrganization
    contactUrl: Literal["Alex.Wagner@nationwidechildrens.org"] = (  # noqa: N815
        "Alex.Wagner@nationwidechildrens.org"
    )
    documentationUrl: Literal["https://github.com/genomicmedlab/vlm_in_a_box"] = (  # noqa: N815
        "https://github.com/genomicmedlab/vlm_in_a_box"
    )
    createdAt: Literal["2025-06-01T00:00:00Z"] = "2025-06-01T00:00:00Z"  # noqa: N815
    updatedAt: Literal["2025-06-01T00:00:00Z"] = "2025-06-01T00:00:00Z"  # noqa: N815
    environment: ServiceEnvironment
    version: str = __version__
