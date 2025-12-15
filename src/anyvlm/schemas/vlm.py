"""Schemas relating to VLM API."""

from pydantic import BaseModel


class VlmResponse(BaseModel):
    """Define response structure for the variant_counts endpoint."""

    # TODO: Fill this in. See Issue #13
