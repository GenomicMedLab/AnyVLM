"""Provide tools and implementations of AnyVLM storage backends."""

from .base_storage import Storage

DEFAULT_STORAGE_URI = "postgresql://postgres@localhost:5432/anyvlm"

__all__ = ["DEFAULT_STORAGE_URI", "Storage"]
