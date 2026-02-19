Usage
!!!!!

Currently, AnyVLM is used primarily by issuing requests against an HTTP server. This page assumes that such a server is running at ``http://localhost:8080/``.

.. _load-vcf:

Submitting VCFs
===============

Given a VCF describing cohort-level allele frequency, submit a ``POST`` request to ``/ingest_vcf``:

.. code-block:: console

   % curl -X POST "http://localhost:8080/anyvlm/ingest_vcf?assembly=grch38" \
     -F "file=@/path/to/variants.vcf.gz"

VCF Requirements
----------------

- File must be gzip-compressed (``.vcf.gz``)
- Maximum file size: 5GB
- Required INFO fields: ``AC``, ``AN``, ``AC_Het``, ``AC_Hom``, ``AC_Hemi``

Response
--------

After ingestion is complete, a simple response message will confirm success:

.. code-block:: json

   {
     "status": "success",
     "message": "Successfully ingested variants.vcf.gz",
     "details": null
   }

Retrieving CAFs
===============

Issue a ``GET`` request to ``/variant_counts`` with arguments for reference sequence, chromosome, position, and referance/alternate bases, like so:

.. code-block:: console

   % curl "http://localhost:8080/anyvlm/variant_counts?assemblyId=GRCh38&referenceName=22&start=10510105&referenceBases=T&alternateBases=A"

Parameters
----------

.. list-table::

   * - Parameter
     - Description
     - Example
   * - ``assemblyId``
     - Reference assembly
     - ``"GRCh37"``, ``"GRCh38"``, ``"hg19"``, ``"hg38"``
   * - ``referenceName``
     - Chromosome
     - ``1-22``, ``X``, ``Y``, ``MT``
   * - ``start``
     - Position (1-based)
     - ``44389414``
   * - ``referenceBases``
     - Reference allele
     - ``A``, ``ACGT``, etc.
   * - ``alternateBases``
     - Alternate allele
     - ``G``, ``TGCA``, etc.

Response
--------

The AnyVLM server will respond to a valid request with a VLM protocol-compliant JSON object that includes the following fields:

- ``beaconHandovers``: Handover metadata for network integration, describing the data
- ``meta``: Beacon metadata, describing the server itself
- ``responseSummary``: Whether variant exists, and total number of matching results
- ``response``: ResultSets grouped by zygosity (Homozygous, Heterozygous, Hemizygous, Unknown)

For example:

.. code-block:: json

   {
     "beaconHandovers": [
       {
         "handoverType": {
           "id": "GREGoR-NCH",
           "label": "GREGoR AnyVLM Reference"
         },
         "url": "https://variants.gregorconsortium.org/"
       }
     ],
     "meta": {
       "apiVersion": "v1.0",
       "beaconId": "org.anyvlm.gregor",
       "returnedSchemas": [
         {
           "entityType": "genomicVariant",
           "schema": "ga4gh-beacon-variant-v2.0.0"
         }
       ]
     },
     "responseSummary": {
       "exists": true,
       "numTotalResults": 2
     },
     "response": {
       "resultSets": [
         {
           "exists": true,
           "id": "GREGoR-NCH Homozygous",
           "results": [],
           "resultsCount": 2,
           "setType": "genomicVariant"
         },
         {
           "exists": true,
           "id": "GREGoR-NCH Heterozygous",
           "results": [],
           "resultsCount": 0,
           "setType": "genomicVariant"
         },
         {
           "exists": true,
           "id": "GREGoR-NCH Hemizygous",
           "results": [],
           "resultsCount": 0,
           "setType": "genomicVariant"
         }
       ]
     }
   }


GA4GH Service Info
==================

AnyVLM also supports the `GA4GH Service Info Specification <https://www.ga4gh.org/product/service-info/>`_. A ``GET`` request to ``/service-info`` returns GA4GH-compliant service metadata.
