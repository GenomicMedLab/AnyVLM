Configuring Docker Compose
!!!!!!!!!!!!!!!!!!!!!!!!!!

This page describes how to use the provided ``compose.yaml`` file to start AnyVLM alongside its dependencies, and highlights some configuration options you can customize for your environment.

Overview
--------

The compose file defines four main services:

* ``anyvlm_db`` - PostgreSQL database for AnyVLM
* ``anyvlm_test_db`` - PostgreSQL database for AnyVLM Tests

It also defines Docker volumes:

* ``anyvlm_vol`` - storage for the AnyVLM PostgreSQL data directory
* ``anyvlm_test_vol`` - storage for the AnyVLM PostgreSQL Test data directory

These volumes are declared as ``external: true``, so it must exist before
you run ``docker compose up``. For example:

.. code-block:: bash

   docker volume create anyvlm_vol
   docker volume create anyvlm_test_vol

Running the stack
-----------------

After creating the external volumes and configuring any optional environment variables, you can start the stack with:

.. code-block:: bash

   docker compose up
