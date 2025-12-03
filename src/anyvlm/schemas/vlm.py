"""Schemas relating to VLM API."""
from pydantic import BaseModel


class VlmResponse(BaseModel):
    """Define response structure for the vlm-query endpoint."""