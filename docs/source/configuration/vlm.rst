VLM API Configuration
!!!!!!!!!!!!!!!!!!!!!

The VLM API presently requires declaration of several values for service identification and data provenance.

.. note::

   Each of these values is **required**, and no default value is provided. AnyVLM will not launch successfully unless they are set from environment variables or a ``.env`` file.

.. list-table::

   * - Name
     - Description
     - Example
   * - ``HANDOVER_TYPE_ID``
     - Unique ID for the dataset or cohort. In keeping with the Beacon API, MUST be formatted as a CURIE; see `here <https://github.com/ga4gh-beacon/beacon-v2/blob/c6558bf2e6494df3905f7b2df66e903dfe509500/framework/json/common/beaconCommonComponents.json#L144>`_ for a description.
     - ``"CUSTOM:GREGoR-NCH"``
   * - ``HANDOVER_TYPE_LABEL``
     - Description of the dataset or cohort
     - ``"GREGoR AnyVLM Reference"``
   * - ``BEACON_HANDOVER_URL``
     - Homepage or reference for the data
     - ``"https://variants.gregorconsortium.org/"``
   * - ``BEACON_NODE_ID``
     - Unique ID for the service instance
     - ``"org.anyvlm.gregor"``
