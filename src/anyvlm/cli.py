"""CLI for interacting with VLM instance"""

import click

import anyvlm


@click.version_option(anyvlm.__version__)
@click.group()
def _cli() -> None:
    """Manage VLM data."""


@_cli.command()
def ingest_vcf() -> None:
    """Deposit variants and allele frequencies from VCF into VLM instance"""
    raise NotImplementedError
