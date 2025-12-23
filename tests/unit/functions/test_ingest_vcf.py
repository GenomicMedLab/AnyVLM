from collections.abc import Iterable, Sequence
from pathlib import Path

import pytest
from anyvar.utils.liftover_utils import ReferenceAssembly
from anyvar.utils.types import VrsVariation

from anyvlm.anyvar.base_client import BaseAnyVarClient
from anyvlm.functions.ingest_vcf import VcfAfColumnsError, ingest_vcf


@pytest.fixture(scope="session")
def stub_anyvar_client():
    """Stub implementation of AnyVar client interface"""
    put_allele_expressions_responses = {
        (
            "chr14-18223529-C-A",
            ReferenceAssembly.GRCH38,
        ): "ga4gh:VA.slgr2fnRKaUnQrJZvYNDGMrfZHw6QCr6",
        (
            "chr14-18223557-C-T",
            ReferenceAssembly.GRCH38,
        ): "ga4gh:VA.6Vh1yfYyljQHm6_qLTKqzi1URy8MfcGe",
        (
            "chr14-18223583-C-G",
            ReferenceAssembly.GRCH38,
        ): "ga4gh:VA.7RhOJ6GlTAnbiwEcfvl9ZKSzrJl47Emg",
        (
            "chr14-18223586-T-C",
            ReferenceAssembly.GRCH38,
        ): "ga4gh:VA.srLXVmS7-JU1hLfxMZkkgFMy64GS7D8H",
        (
            "chr14-18223591-G-A",
            ReferenceAssembly.GRCH38,
        ): "ga4gh:VA.1ra1LoRvuvAhbeKl4YgbdrGkXWjc8Lpc",
        (
            "chr14-19000006-C-A",
            ReferenceAssembly.GRCH37,
        ): "ga4gh:VA.A6NA06tRm76hLZulNn0YvSFCqflzJQe9",
        (
            "chr14-19000034-C-T",
            ReferenceAssembly.GRCH37,
        ): "ga4gh:VA.i8WIscnfIDr0xAn6XgCwMUk63Y-Lg3BN",
    }

    class TestAnyVarClient(BaseAnyVarClient):
        def get_registered_allele_expression(
            self,
            expression: str,
            assembly: ReferenceAssembly = ReferenceAssembly.GRCH38,
        ):
            raise NotImplementedError

        def put_allele_expressions(
            self,
            expressions: Iterable[str],
            assembly: ReferenceAssembly = ReferenceAssembly.GRCH38,
        ) -> Sequence[str | None]:
            return [
                put_allele_expressions_responses[(expr, assembly)]
                for expr in expressions
            ]

        def search_by_interval(
            self, accession: str, start: int, end: int
        ) -> list[VrsVariation]:
            raise NotImplementedError

        def close(self) -> None:
            """Clean up AnyVar connection."""

    return TestAnyVarClient()


@pytest.fixture(scope="session")
def input_grch38_vcf_path(test_data_dir: Path) -> Path:
    return test_data_dir / "vcf" / "grch38_vcf.vcf"


@pytest.fixture(scope="session")
def input_grch37_vcf_path(test_data_dir: Path) -> Path:
    return test_data_dir / "vcf" / "grch37_vcf.vcf"


def test_ingest_vcf_grch38(test_data_dir: Path, stub_anyvar_client: BaseAnyVarClient):
    ingest_vcf(test_data_dir / "vcf" / "grch38_vcf.vcf", stub_anyvar_client)


def test_ingest_vcf_grch37(test_data_dir: Path, stub_anyvar_client: BaseAnyVarClient):
    ingest_vcf(
        test_data_dir / "vcf" / "grch37_vcf.vcf",
        stub_anyvar_client,
        ReferenceAssembly.GRCH37,
    )


def test_ingest_vcf_notfound(stub_anyvar_client: BaseAnyVarClient):
    with pytest.raises(FileNotFoundError):
        ingest_vcf(Path("file_that_doesnt_exist.vcf"), stub_anyvar_client)


def test_ingest_vcf_infocol_missing(
    stub_anyvar_client: BaseAnyVarClient, test_data_dir: Path
):
    """Test smooth handling of VCF that's missing one or more required INFO columns"""
    with pytest.raises(VcfAfColumnsError):
        ingest_vcf(test_data_dir / "vcf" / "info_field_missing.vcf", stub_anyvar_client)
