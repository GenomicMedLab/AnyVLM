"""CLI for interacting with AnyVLM instance"""

import click

import anyvlm


@click.version_option(anyvlm.__version__)
@click.group()
def _cli() -> None:
    """Manage AnyVLM data."""


@_cli.command()
def ingest_vcf() -> None:
    """Deposit variants and allele frequencies from VCF into AnyVLM instance"""
    raise NotImplementedError
