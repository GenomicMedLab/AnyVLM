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

TODO fix this

.. code-block:: bash

   % docker volume create seqrepo_vol
   % docker volume create uta_vol
   % docker volume create anyvar_vol

Then, launch the application:

.. code-block:: console

   % docker compose up

This will:

TODO clean this up

* pull the necessary images,
* start SeqRepo (or use your local SeqRepo if configured),
* start UTA and AnyVar’s PostgreSQL database,
* and launch AnyVar REST service.

Once the containers are running, visit `http://127.0.0.1:8010/docs <http://127.0.0.1:8010/docs>`_ to view the interactive Swagger UI and confirm the service is responding.
