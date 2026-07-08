"""Compatibility aliases for AnyVar/VRS object types.

These names preserve AnyVLM's broader type intent even when upstream AnyVar stops
exporting its convenience aliases.
"""

from ga4gh.vrs.models import Allele

try:
    from anyvar.core.objects import SupportedVrsObject, SupportedVrsVariation
except ImportError:
    SupportedVrsObject = Allele
    SupportedVrsVariation = Allele
