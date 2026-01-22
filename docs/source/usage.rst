Usage
!!!!!

Submitting VCFs
===============

Given a VCF describing cohort-level allele frequency, submit a ``POST`` request to ``/ingest_vcf``:

.. code-block:: console

   % curl -X POST "http://localhost:8080/ingest_vcf?assembly=grch38" \
     -F "file=@/path/to/variants.vcf.gz"

Requirements
------------

- File must be gzip-compressed (``.vcf.gz``)
- Maximum file size: 5GB
- Required INFO fields: ``AC``, ``AN``, ``AC_Het``, ``AC_Hom``, ``AC_Hemi``

Response:
---------

```json
{
  "status": "success",
  "message": "Successfully ingested variants.vcf.gz",
  "details": null
}
```

Retrieving CAFs
===============

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


GA4GH Service Info
==================

```bash
curl http://localhost:8080/service-info
```

Returns GA4GH-compliant service metadata.
