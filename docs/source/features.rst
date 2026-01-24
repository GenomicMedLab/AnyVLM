AnyVLM Features
!!!!!!!!!!!!!!!

Variant-Level Matching (VLM) Protocol
=====================================

AnyVLM implements the nascent `Variant-Level Matching <https://www.ga4gh.org/what-we-do/ga4gh-implementation-forum/federated-variant-level-matching-vlm-project/>`_, or VLM, protocol. This framework enables construction of a federated genomic knowledge network, allowing laboratories and consortia to make internal variation data discoverable and reusable by other researchers and clinicians. AnyVLM is designed as a lightweight and portable solution for rapidly spinning up a new VLM node and introducing new data to the network.

The VLM protocol is still in development, and is subject to change.

Cohort Allele Frequency (CAF) Retrieval
=======================================

At present, AnyVLM serves `Cohort Allele Frequency (CAF) <https://va-spec.ga4gh.org/en/1.0/va-standard-profiles/base-profiles/study-result-profiles.html#cohort-allele-frequency-study-result>`_ objects, describing the frequency of an allele in a cohort. CAF objects may also report additional data, including frequency broken down by zygosity and quality control filters declared by the original variant calls.

.. figure:: /_static/img/caf.png
   :width: 80%
   :align: center
   :alt: Summary of CAF object structure

   Summary of CAF object structure

VCF Ingestion
=============

Data is submitted to AnyVLM by way of Variant Call Format (VCF) files. Presently, incoming VCFs must use INFO fields to declare cohort frequency data. See the specific requirements described in the :ref:`Usage <load-vcf>` section for more information.

AnyVar Storage Backend
======================

While an AnyVLM instance stores allele frequency data internally, it utilizes `AnyVar <https://anyvar.readthedocs.io/en/latest/>`_ for registration and retrieval of the variants themselves. An AnyVar instance may be constructed internally, or an external AnyVar instance available on the local network may be used.

Genomics Standards Conformance
==============================

This version of AnyVLM validates data using the following data standards:


.. list-table::

   * - Standard
     - Version
     - Datatypes used
   * - `Variation Representation Specification (VRS) <https://vrs.ga4gh.org/en/stable/>`_
     - |VRS_VERSION|
     - `Allele <https://vrs.ga4gh.org/en/stable/concepts/MolecularVariation/Allele.html>`_
   * - `Variant Annotation Specification (VA-Spec) <https://va-spec.ga4gh.org/en/stable/>`_
     - |VASPEC_VERSION|
     - `Cohort Allele Frequency <https://va-spec.ga4gh.org/en/stable/va-standard-profiles/base-profiles/study-result-profiles.html#cohort-allele-frequency-study-result>`_
