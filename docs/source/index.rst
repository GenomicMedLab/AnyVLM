AnyVLM |version|
!!!!!!!!!!!!!!!!

**AnyVLM** is an off-the-shelf solution for adding local aggregate-level variant information to a `Variant-Level Matching (VLM) network <https://www.ga4gh.org/what-we-do/ga4gh-implementation-forum/federated-variant-level-matching-vlm-project/>`_. It provides a REST API service that integrates with GA4GH standards for genomic data exchange.

AnyVLM enables genomic research organizations to:

- **Ingest VCF files** containing variant and allele frequency data
- **Register variants** using the GA4GH Variant Representation Specification (VRS) via AnyVar
- **Store cohort allele frequencies** (CAF) with zygosity-stratified counts
- **Serve VLM protocol-compliant responses** with Beacon handover capabilities

This service is designed for rare disease variant frequency tracking in genomic research networks such as `GREGoR <https://gregorconsortium.org/>`_.

If you're setting up AnyVLM for the first time, begin with the :doc:`Getting Started guide <getting_started/index>`, which covers different installation options. To learn how to use AnyVar as a service, see :doc:`Usage <usage>`. For further assistance, please refer to :doc:`Getting Help <help>`.

.. toctree::
   :maxdepth: 2
   :caption: Contents
   :hidden:

   Getting Started<getting_started/index>
   Features<features>
   Usage<usage>
   Configuration<configuration/index>
   API Reference<api/index>
   Getting Help<help>
   Changelog<changelog>
   Contributing<contributing>
   Project Roadmap<roadmap>
   License<license>
