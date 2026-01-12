"""CLI for interacting with AnyVLM instance"""

from pathlib import Path

import click
import requests
from anyvar.utils.liftover_utils import ReferenceAssembly

import anyvlm
from anyvlm.config import Settings, get_config


@click.version_option(anyvlm.__version__)
@click.group()
def _cli() -> None:
    """Manage AnyVLM data."""


@_cli.command()
@click.option(
    "--file",
    "vcf_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="Path to a gzip-compressed VCF file (.vcf.gz)",
)
@click.option(
    "--assembly",
    type=click.Choice(
        [assembly.value for assembly in ReferenceAssembly], case_sensitive=False
    ),
    required=True,
    callback=lambda _, __, value: ReferenceAssembly(value),
    help="Reference genome assembly",
)
def ingest_vcf(vcf_path: Path, assembly: ReferenceAssembly) -> None:
    """Deposit variants and allele frequencies from VCF into AnyVLM instance"""
    click.echo(f"Uploading {vcf_path}")

    config: Settings = get_config()
    endpoint: str = f"{config.service_uri}/ingest_vcf"

    params = {"assembly": assembly.value}

    with vcf_path.open("rb") as fh:
        files = {"file": (vcf_path.name, fh, "application/gzip")}

        try:
            requests.post(
                endpoint,
                files=files,
                params=params,
                timeout=1800,
            )
        except requests.RequestException as e:
            raise click.ClickException(str(e)) from e

    click.echo("Ingestion complete")
