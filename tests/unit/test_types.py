"""Tests for types and validator functions found in src/anyvlm/utils/types.py"""

import re

import pytest
from pydantic import TypeAdapter, ValidationError

from anyvlm.utils.types import ChromosomeName, _normalize_chromosome_name


@pytest.fixture
def valid_chromosomes() -> list[tuple[str, str]]:
    """List of tuples of unnormalized chromosome names & expected normalized values"""
    return [
        ("1", "1"),
        ("22", "22"),
        ("X", "X"),
        ("Y", "Y"),
        ("MT", "MT"),
        ("chr1", "1"),
        ("Chr22", "22"),
        ("cHrX", "X"),
        ("chrM", "M"),
    ]


@pytest.fixture
def invalid_chromosomes() -> list[str | None]:
    return ["0", "23", "chr23", "M", "chrMT", "XY", "", "chr", "1a", None]


@pytest.fixture
def chromosome_adapter() -> TypeAdapter[ChromosomeName]:
    return TypeAdapter(ChromosomeName)


### Test chromosome name normalization function ###
def test_normalize_chromosome_name_valid(valid_chromosomes):
    for unnormalized_name, expected_name in valid_chromosomes:
        assert _normalize_chromosome_name(unnormalized_name) == expected_name


def test_normalize_chromosome_name_invalid(invalid_chromosomes):
    for chromosome_name in invalid_chromosomes:
        if chromosome_name is not None:
            with pytest.raises(
                ValueError,
                match=(
                    re.escape(
                        "Invalid chromosome name. Must be a string consisting of either a number between 1-22, or one of the values 'X', 'Y', or 'MT'; optionally prefixed with 'chr'."
                    )
                ),
            ):
                _normalize_chromosome_name(chromosome_name)
        else:
            with pytest.raises(AttributeError):
                _normalize_chromosome_name(chromosome_name)


### Test ChromosomeName annotated type ###
def test_chromosome_name_adapter_valid(chromosome_adapter, valid_chromosomes):
    for raw, expected in valid_chromosomes:
        assert chromosome_adapter.validate_python(raw) == expected


def test_chromosome_name_adapter_invalid(chromosome_adapter, invalid_chromosomes):
    for chromosome_name in invalid_chromosomes:
        with pytest.raises(ValidationError):
            chromosome_adapter.validate_python(chromosome_name)
