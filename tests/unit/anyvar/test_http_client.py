from collections import namedtuple
from http import HTTPStatus

import pytest
import responses
from anyvar.utils.types import recursive_identify
from ga4gh.vrs import models
from responses import matchers

from anyvlm.anyvar.http_client import HttpAnyVarClient


@pytest.fixture
def client() -> HttpAnyVarClient:
    return HttpAnyVarClient()


# simple namedtuple to make accessing different parts of the fixture easier
_InputVariant = namedtuple(
    "InputVariant", ["fn_input", "anyvar_input", "anyvar_return", "expected"]
)


@pytest.fixture
def input_variants() -> list[_InputVariant]:
    alleles = [
        models.Allele(
            location=models.SequenceLocation(
                sequenceReference=models.SequenceReference(
                    refgetAccession="SQ.ss8r_wB0-b9r44TQTMmVTI92884QvBiB"
                ),
                start=87894076,
                end=87894077,
            ),
            state=models.LiteralSequenceExpression(sequence=models.sequenceString("T")),
        )
    ]
    return [
        _InputVariant(
            fn_input=a,
            anyvar_input=a.model_dump(exclude_none=True, mode="json"),
            anyvar_return=recursive_identify(a).model_dump(
                exclude_none=True, mode="json"
            ),
            expected=recursive_identify(a),
        )
        for a in alleles
    ]


@responses.activate
def test_put_objects(client: HttpAnyVarClient, input_variants: list[_InputVariant]):
    for input_variant in input_variants:
        responses.add(
            responses.PUT,
            "http://localhost:8000/vrs_variation",
            headers={"Content-Type": "application/json"},
            match=[matchers.json_params_matcher(input_variant.anyvar_input)],
            json={
                "messages": [],
                "object": input_variant.anyvar_return,
                "object_id": input_variant.anyvar_return["id"],
            },
            status=HTTPStatus.ACCEPTED,
        )
        result = client.put_objects([input_variant.fn_input])
        assert result == [input_variant.expected]
