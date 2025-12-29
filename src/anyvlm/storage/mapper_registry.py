"""Central registry for all object mappers."""

from types import MappingProxyType
from typing import TypeVar

from ga4gh.va_spec.base import CohortAlleleFrequencyStudyResult

from anyvlm.storage import orm
from anyvlm.storage.mappers import AlleleFrequencyMapper, BaseMapper

T = TypeVar("T")


class MapperRegistry:
    """Central registry for all object mappers."""

    va_model_to_db_mapping: MappingProxyType = MappingProxyType(
        {CohortAlleleFrequencyStudyResult: orm.AlleleFrequencyData}
    )

    _mappers: MappingProxyType[type, BaseMapper] = MappingProxyType(
        {orm.AlleleFrequencyData: AlleleFrequencyMapper()}
    )

    def get_mapper(self, entity_type: type[T]) -> BaseMapper:
        """Get mapper for the given entity type."""
        mapper = self._mappers.get(entity_type)
        if mapper is None:
            raise ValueError(f"No mapper registered for type: {entity_type}")
        return mapper

    def from_db_entity(self, db_entity):  # noqa: ANN201, ANN001
        """Convert any DB entity to its corresponding VA-Spec model."""
        mapper = self.get_mapper(type(db_entity))
        return mapper.from_db_entity(db_entity)

    def to_db_entity(self, va_model) -> orm.Base:  # noqa: ANN001
        """Convert any VA-Spec model to its corresponding DB entity."""
        db_type = self.va_model_to_db_mapping.get(type(va_model))
        if db_type is None:
            raise ValueError(f"No DB entity type mapped for VA model: {type(va_model)}")

        mapper = self.get_mapper(db_type)
        return mapper.to_db_entity(va_model)


# Global registry instance
mapper_registry = MapperRegistry()
