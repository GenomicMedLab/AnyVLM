.. _setup-docker-compose:

Quick Setup: Docker Compose
!!!!!!!!!!!!!!!!!!!!!!!!!!!

Prerequisites
=============

* `Docker Compose <https://docs.docker.com/compose/install/>`_

Steps
=====

Clone the AnyVLM repository (optionally switching to a release tag), and enter the directory:

.. code-block:: console

   % git clone https://github.com/genomicmedlab/anyvlm
   % cd anyvlm

Create all required volumes:

.. code-block:: console

   % make volumes

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

Once the containers are running, visit `http://127.0.0.1:8080/docs <http://127.0.0.1:8080/docs>`_ to view the interactive Swagger UI and confirm the service is responding.
