# AnyVLM

[![Python Package CI](https://github.com/genomicmedlab/anyvlm/actions/workflows/python-package.yaml/badge.svg)](https://github.com/genomicmedlab/anyvlm/actions/workflows/python-package.yaml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**AnyVLM** (Any Variant-Level Matching) is an off-the-shelf solution for adding local aggregate-level variant information to a Variant-Level Matching (VLM) network. It provides a REST API service that integrates with GA4GH standards for genomic data exchange.

## Overview

AnyVLM enables genomic research organizations to:

- **Ingest VCF files** containing variant and allele frequency data
- **Register variants** using the GA4GH Variant Representation Specification (VRS) via AnyVar
- **Store cohort allele frequencies** (CAF) with zygosity-stratified counts
- **Serve VLM protocol-compliant responses** with Beacon handover capabilities

This service is designed for rare disease variant frequency tracking in genomic research networks such as GREGoR.

## Features

- **VCF File Ingestion**: Streaming upload with comprehensive validation, batch processing, and support for multiple alternate alleles
- **VRS Compliance**: Integration with AnyVar for standardized variant representation
- **Zygosity Tracking**: Separate counts for homozygous, heterozygous, and hemizygous variants
- **GA4GH Beacon v2 Compatible**: Standards-compliant responses for network interoperability
- **Flexible Deployment**: Docker support, configurable storage backends, and CLI tools
- **Assembly Support**: Both GRCh37/hg19 and GRCh38/hg38 reference assemblies

## Requirements

- Python 3.11 - 3.14
- PostgreSQL 17+
- [AnyVar](https://github.com/biocommons/anyvar) for variant registration
- [SeqRepo](https://github.com/biocommons/biocommons.seqrepo) for sequence data
- [UTA](https://github.com/biocommons/uta) for transcript alignment

## Installation

### Via pip

```bash
pip install anyvlm
```

### Development Installation

```bash
git clone https://github.com/genomicmedlab/anyvlm.git
cd anyvlm
pip install -e ".[dev,test]"
```

### Docker

```bash
docker pull ghcr.io/genomicmedlab/anyvlm:latest
```

## Configuration

AnyVLM is configured via environment variables. Create a `.env` file in your project root:

```bash
# Required: Database connection
ANYVLM_STORAGE_URI=postgresql://anyvlm:anyvlm-pw@localhost:5435/anyvlm

# Required for /variant_counts endpoint: VLM handover configuration
HANDOVER_TYPE_ID="GREGoR-NCH"
HANDOVER_TYPE_LABEL="GREGoR AnyVLM Reference"
BEACON_HANDOVER_URL="https://variants.example.org/"
BEACON_NODE_ID="org.anyvlm.example"

# AnyVar configuration
UTA_DB_URL=postgresql://anonymous@localhost:5433/uta/uta_20241220
SEQREPO_DATAPROXY_URI=seqrepo+file:///usr/local/share/seqrepo/2024-12-20
ANYVAR_STORAGE_URI=postgresql://anyvar:anyvar-pw@localhost:5434/anyvar

# Optional: Service configuration
ANYVLM_ENV=local                          # local, test, dev, staging, prod
ANYVLM_SERVICE_URI=http://localhost:8080
ANYVLM_ANYVAR_URI=http://localhost:8000   # Omit to use embedded Python client

# Optional: Custom logging configuration
ANYVLM_LOGGING_CONFIG=/path/to/logging.yaml
```

See [`.env.example`](.env.example) for a complete template.

## Quick Start

### Using Docker Compose (Recommended)

1. **Create required volumes:**

   ```bash
   make volumes
   ```

2. **Start the full stack:**

   ```bash
   # Development mode with hot-reload
   make up-dev

   # Or production mode
   ANYVLM_VERSION=latest make up
   ```

3. **Access the service:**
   - AnyVLM API: <http://localhost:8080>
   - API Documentation: <http://localhost:8080/docs>
   - AnyVar (if using compose.anyvar.yaml): <http://localhost:8000>

### Available Docker Compose Configurations

| File                  | Purpose                                              |
| --------------------- | ---------------------------------------------------- |
| `compose.yaml`        | Production deployment with pre-built images          |
| `compose.dev.yaml`    | Development with local build and hot-reload          |
| `compose.anyvar.yaml` | AnyVar dependencies (SeqRepo, UTA, AnyVar service)   |
| `compose.test.yaml`   | Minimal services for testing                         |

**Full stack with AnyVar:**

```bash
docker compose -f compose.dev.yaml -f compose.anyvar.yaml up --build
```

## Usage

### REST API

#### Service Info

```bash
curl http://localhost:8080/service-info
```

Returns GA4GH-compliant service metadata.

#### Ingest VCF File

```bash
curl -X POST "http://localhost:8080/ingest_vcf?assembly=grch38" \
  -F "file=@/path/to/variants.vcf.gz"
```

**Requirements:**

- File must be gzip-compressed (`.vcf.gz`)
- Maximum file size: 5GB
- Required INFO fields: `AC`, `AN`, `AC_Het`, `AC_Hom`, `AC_Hemi`

**Response:**

```json
{
  "status": "success",
  "message": "Successfully ingested variants.vcf.gz",
  "details": null
}
```

#### Query Variant Counts

```bash
curl "http://localhost:8080/variant_counts?assemblyId=GRCh38&referenceName=22&start=44389414&referenceBases=A&alternateBases=G"
```

**Parameters:**

| Parameter         | Description              | Example                            |
| ----------------- | ------------------------ | ---------------------------------- |
| `assemblyId`      | Reference assembly       | `GRCh37`, `GRCh38`, `hg19`, `hg38` |
| `referenceName`   | Chromosome               | `1-22`, `X`, `Y`, `MT`             |
| `start`           | Position (1-based)       | `44389414`                         |
| `referenceBases`  | Reference allele         | `A`, `ACGT`, etc.                  |
| `alternateBases`  | Alternate allele         | `G`, `TGCA`, etc.                  |

**Response:**

VLM protocol-compliant JSON with:

- `beaconHandovers`: Handover metadata for network integration
- `meta`: Beacon metadata
- `responseSummary`: Whether variant exists and total results
- `response`: ResultSets grouped by zygosity (Homozygous, Heterozygous, Hemizygous, Unknown)

### Command-Line Interface

```bash
# Ingest a VCF file
anyvlm ingest-vcf --file /path/to/variants.vcf.gz --assembly grch38
```

The CLI sends VCF data to the running AnyVLM service endpoint.

## Project Structure

```text
anyvlm/
├── src/anyvlm/
│   ├── main.py              # FastAPI application
│   ├── cli.py               # Command-line interface
│   ├── config.py            # Configuration management
│   ├── restapi/             # REST API routes
│   │   ├── vlm.py           # VLM protocol endpoints
│   │   └── deps.py          # Dependency injection
│   ├── functions/           # Core business logic
│   │   ├── ingest_vcf.py    # VCF processing
│   │   ├── get_caf.py       # CAF retrieval
│   │   └── build_vlm_response.py
│   ├── storage/             # Database layer
│   │   ├── postgres.py      # PostgreSQL implementation
│   │   └── orm.py           # SQLAlchemy models
│   ├── anyvar/              # AnyVar integration
│   │   ├── http_client.py   # HTTP-based client
│   │   └── python_client.py # Embedded Python client
│   └── schemas/             # Pydantic data models
├── tests/
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
└── docs/                    # Sphinx documentation
```

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/genomicmedlab/anyvlm.git
cd anyvlm

# Install development dependencies
pip install -e ".[dev,test]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
pytest --cov=anyvlm --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_restapi.py

# Start test database services
docker compose -f compose.test.yaml up -d
```

### Code Quality

```bash
# Format code
ruff format src tests

# Lint code
ruff check src tests

# Run all pre-commit hooks
pre-commit run --all-files
```

### Building Documentation

```bash
make -C docs html
# Output: docs/_build/html/index.html
```

## Makefile Commands

| Command          | Description                              |
| ---------------- | ---------------------------------------- |
| `make develop`   | Install package in development mode      |
| `make test`      | Run test suite                           |
| `make volumes`   | Create required Docker volumes           |
| `make up`        | Start production stack                   |
| `make up-dev`    | Start development stack with hot-reload  |
| `make up-test`   | Start test services                      |
| `make down`      | Remove all containers                    |
| `make stop`      | Stop running services                    |

## API Documentation

When the service is running, interactive API documentation is available at:

- **Swagger UI**: <http://localhost:8080/docs>
- **ReDoc**: <http://localhost:8080/redoc>

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`make test && ruff check src tests`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Contact

- **Repository**: <https://github.com/genomicmedlab/anyvlm>
- **Issues**: <https://github.com/genomicmedlab/anyvlm/issues>
- **Email**: <biocommons-dev@googlegroups.com>

## Acknowledgments

AnyVLM is developed by [The Wagner Lab at Nationwide Children's](https://www.nationwidechildrens.org/specialties/institute-for-genomic-medicine/research-labs/wagner-lab) and [The Translational Genomics Group at Broad Institute](https://the-tgg.org/).

This project integrates with:

- [GA4GH VRS](https://vrs.ga4gh.org/) - Variant Representation Specification
- [AnyVar](https://github.com/biocommons/anyvar) - Variant annotation service
- [GA4GH Beacon](https://beacon-project.io/) - Standards for genomic data discovery
