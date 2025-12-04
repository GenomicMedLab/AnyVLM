"""Schemas relating to VLM API."""
from pydantic import BaseModel


class VlmResponse(BaseModel):
    """Define response structure for the vlm-query endpoint."""
    # TODO: Fill this in. See Issue #13