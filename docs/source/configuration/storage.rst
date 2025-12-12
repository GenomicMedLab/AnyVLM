Object Storage Configuration
!!!!!!!!!!!!!!!!!!!!!!!!!!!!

Storage Connection
==================

Use the ``ANYVLM_STORAGE_URI`` environment variable to pass a `libpq connection string <https://www.postgresql.org/docs/current/libpq.html>`_ to the PostgreSQL connection constructor.

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Environment Variable
     - Default Value
   * - ``ANYVLM_STORAGE_URI``
     - ``"postgresql://postgres@localhost:5432/anyvlm"``
