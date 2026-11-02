.. _setup-docker-compose:

Quick Setup: Docker Compose
!!!!!!!!!!!!!!!!!!!!!!!!!!!

Prerequisites
=============

* `Docker Compose <https://docs.docker.com/compose/install/>`_
* VLM Network credentials

..warning::
    You **must** contact the VLM Network admins and request permission to join the network prior to setup. You will be unable to
    connect to the network until you are given your unique client credentials. The network admins will give you instructions on
    how to obtain these once you are accepted onto the network.

Steps
=====

Clone the AnyVLM repository (optionally switching to a release tag), and enter the directory:

.. code-block:: console

   % git clone https://github.com/genomicmedlab/anyvlm
   % cd anyvlm

Create all required volumes:

.. code-block:: console

   % make volumes

Download ``uta_20241220.pgd.gz`` from https://dl.biocommons.org/uta/ using a web browser and move it to the root of the repository.

Create a `.env` file following the included `.emv.example` template, and set the required environment variables variables as outlined
in the :doc:`VLM API Configuration page </configuration/vlm>`.

Then, launch the application:

.. code-block:: bash

   # Development mode with hot-reload
   make up-dev

   # Or production mode
   make up


Available Docker Compose Configurations
=======================================

.. list-table::

   * - File
     - Purpose
   * - ``compose.yaml``
     - Production deployment with pre-built images
   * - ``compose.dev.yaml``
     - Development with local build and hot-reload
   * - ``compose.anyvar.yaml``
     - AnyVar dependencies (SeqRepo, UTA, AnyVar service)
   * - ``compose.test.yaml``
     - Minimal services for testing

Full stack with AnyVar
======================

.. code-block:: console

   % docker compose -f compose.dev.yaml -f compose.anyvar.yaml up --build

Once the containers are running, visit `http://127.0.0.1:8080 <http://127.0.0.1:8080>`_ to view the interactive Swagger UI and confirm the service is responding.
