# *AnyVLM* - Lightweight, Portable Variant-Level Matching

**AnyVLM** is an off-the-shelf solution for adding local aggregate-level variant information to a [Variant-Level Matching (VLM) network](https://www.ga4gh.org/what-we-do/ga4gh-implementation-forum/federated-variant-level-matching-vlm-project/). It provides a REST API service that integrates with GA4GH standards for genomic data exchange.

AnyVLM enables genomic research organizations to:

- **Ingest VCF files** containing variant and allele frequency data
- **Register variants** using the GA4GH Variant Representation Specification (VRS) via AnyVar
- **Store cohort allele frequencies** (CAF) with zygosity-stratified counts
- **Serve VLM protocol-compliant responses** with Beacon handover capabilities

This service is designed for rare disease variant frequency tracking in genomic research networks such as [GREGoR](https://gregorconsortium.org/).

## Information

[![rtd](https://img.shields.io/badge/docs-readthedocs-green.svg)](http://anyvlm.readthedocs.io/) [![changelog](https://img.shields.io/badge/docs-changelog-green.svg)](https://anyvlm.readthedocs.io/en/latest/changelog.html) [![GitHub license](https://img.shields.io/github/license/genomicmedlab/anyvlm.svg)](https://github.com/genomicmedlab/anyvlm/blob/main/LICENSE) [![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.18249699-blue)](https://doi.org/10.5281/zenodo.18249699)

## Latest Release

[![GitHub tag](https://img.shields.io/github/tag/genomicmedlab/anyvlm.svg)](https://github.com/genomicmedlab/anyvlm) [![pypi_rel](https://img.shields.io/pypi/v/genomicmedlab.anyvlm.svg)](https://pypi.org/project/genomicmedlab.anyvlm/)

## Development

[![action status](https://github.com/genomicmedlab/anyvlm/actions/workflows/python-package.yml/badge.svg)](https://github.com/genomicmedlab/anyvlm/actions/workflows/python-cqa.yml) [![issues](https://img.shields.io/github/issues-raw/genomicmedlab/anyvlm.svg)](https://github.com/genomicmedlab/anyvlm/issues) [![GitHub Open Pull Requests](https://img.shields.io/github/issues-pr/genomicmedlab/anyvlm.svg)](https://github.com/genomicmedlab/anyvlm/pull/) [![GitHub Contributors](https://img.shields.io/github/contributors/genomicmedlab/anyvlm.svg)](https://github.com/genomicmedlab/anyvlm/graphs/contributors/) [![GitHub stars](https://img.shields.io/github/stars/genomicmedlab/anyvlm.svg?style=social&label=Stars)](https://github.com/genomicmedlab/anyvlm/stargazers) [![GitHub forks](https://img.shields.io/github/forks/genomicmedlab/anyvlm.svg?style=social&label=Forks)](https://github.com/genomicmedlab/anyvlm/forks)

## Installation

A set of Docker Compose resources are provided as part of the AnyVLM project. See the [Docker-based installation instructions](https://anyvlm.readthedocs.org/en/stable/getting_started/docker_compose.html).

## Examples

Given an available AnyVLM node, submit a VCF which contains allele frequency data:

```bash
curl -X POST "http://localhost:8080/ingest_vcf?assembly=grch38" \
  -F "file=@/path/to/variants.vcf.gz"
```

Then, submit a query for allele frequency

```bash
curl "http://localhost:8080/variant_counts?assemblyId=GRCh38&referenceName=22&start=44389414&referenceBases=A&alternateBases=G"
```

A successful query returns a response like the following:

```json
{"beaconHandovers":[{"handoverType":{"id":"GREGoR-NCH","label":"GREGoR AnyVLM Reference"},"url":"https://variants.gregorconsortium.org/"}],"meta":{"apiVersion":"v1.0","beaconId":"org.anyvlm.gregor","returnedSchemas":[{"entityType":"genomicVariant","schema":"ga4gh-beacon-variant-v2.0.0"}]},"responseSummary":{"exists":true,"numTotalResults":2},"response":{"resultSets":[{"exists":true,"id":"GREGoR-NCH Homozygous","results":[],"resultsCount":2,"setType":"genomicVariant"},{"exists":true,"id":"GREGoR-NCH Heterozygous","results":[],"resultsCount":0,"setType":"genomicVariant"},{"exists":true,"id":"GREGoR-NCH Hemizygous","results":[],"resultsCount":0,"setType":"genomicVariant"}]}}
```

See the [usage](https://anyvlm.readthedocs.org/en/stable/usage.html) page in the documentation for more information.

## Feedback and contributing

We welcome [bug reports](https://github.com/genomicmedlab/anyvlm/issues/new?template=bug-report.md), [feature requests](https://github.com/genomicmedlab/anyvlm/issues/new?template=feature-request.md), and code contributions from users and interested collaborators. The [documentation](https://anyvlm.readthedocs.io/en/latest/contributing.html) contains guidance for submitting feedback and contributing new code.
