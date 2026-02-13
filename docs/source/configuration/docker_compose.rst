Configuring Docker Compose
!!!!!!!!!!!!!!!!!!!!!!!!!!

This page describes how to use the provided Docker Compose configuration to start AnyVLM and its related services, and explains how the stack is organized for default usage, development, and testing.

Overview
--------

The Docker Compose configuration is split across multiple files to separate concerns and support different workflows. All additional Compose files follow the naming pattern ``compose.<purpose>.yaml`` and are intended to be used explicitly with the ``-f`` flag, which specifies the location of a Compose configuration file.

* ``compose.yaml``
  The **main entry point** for most users. This file starts AnyVLM using pre-built, versioned container images to provide a stable and reproducible default deployment.

  .. important::

      AnyVLM requires access to the AnyVar services. For convenience, a Docker Compose configuration for AnyVar is provided in ``compose.anyvar.yaml``. Users who already have AnyVar running elsewhere do not need to start it again.

  .. note::

      ``compose.yaml`` intentionally uses pinned image tags rather than ``latest``. This helps ensure consistent behavior across deployments. Developers who need to build images locally or work with in-progress changes should use ``compose.dev.yaml`` instead.

* ``compose.dev.yaml``
   Defines AnyVLM-specific development services, including FastAPI and PostgreSQL services built from local Dockerfiles. This file is intended for developers working on the AnyVLM codebase.

   .. note::

      ``compose.dev.yaml`` and the ``Dockerfile`` expect ``ANYVLM_VERSION`` to be set to the AnyVLM version being used (for example, ``1.0.0``) when running Docker Compose or building the image directly. This is handled automatically when using the Makefile.

* ``compose.anyvar.yaml``
   Defines the services required to run the AnyVar REST service and its dependencies. This file is optional and is provided as a convenience for users who do not already have AnyVar running.

* ``compose.test.yaml``
   Defines the minimal set of services required for running tests.

Environment variables
---------------------

An example environment file is documented in :doc:`dotenv_example`. The values shown there match the defaults used by the provided Docker Compose configurations.

If you are using the example targets documented below, those values can be used as-is.

Beacon / handover configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following environment variables are set in ``compose.yaml`` and ``compose.dev.yaml`` and configure the VLM Spec:

.. code-block:: yaml

   environment:
     - HANDOVER_TYPE_ID=CUSTOM:GREGoR-NCH
     - HANDOVER_TYPE_LABEL=GREGoR AnyVLM Reference
     - BEACON_HANDOVER_URL=https://variants.gregorconsortium.org/
     - BEACON_NODE_ID=org.anyvlm.gregor

These defaults are configured for the GREGoR AnyVLM node.

.. note::

   You can change these values directly in ``compose.yaml`` and/or ``compose.dev.yaml`` if needed.

Volumes
-------

The Docker Compose configurations use a small number of Docker volumes for persistent data. Some volumes are declared as ``external: true`` and must exist before starting the corresponding services.

The following volumes may be required, depending on which services you run:

* ``anyvlm_vol``: Persistent storage for the AnyVLM PostgreSQL data directory. Required when running ``compose.yaml`` or ``compose.dev.yaml``.

* ``seqrepo_vol``: Storage for sequence repository data. Required when running ``compose.anyvar.yaml`` or ``compose.test.yaml``.

   .. note::

      If you already have a SeqRepo database on your local filesystem, you can use it directly instead of the Docker volume. Both ``compose.anyvar.yaml`` and ``compose.test.yaml`` can be updated to bind-mount your local SeqRepo directory in place of ``seqrepo_vol``.

      For example, if your SeqRepo lives at ``/usr/local/share/seqrepo/2024-12-20``, replace:

      .. code-block:: yaml

         volumes:
         - seqrepo_vol:/usr/local/share/seqrepo

      with:

      .. code-block:: yaml

         volumes:
         - $SEQREPO_ROOT_DIR:$SEQREPO_ROOT_DIR

      Then export the path before starting the stack:

      .. code-block:: bash

         export SEQREPO_ROOT_DIR=/usr/local/share/seqrepo/2024-12-20

* ``uta_vol``: Storage for UTA database data. Required when running ``compose.anyvar.yaml``.

   .. important::

      You must download ``uta_20241220.pgd.gz`` from https://dl.biocommons.org/uta/ using a web browser and move it to the root of the repository.

* ``anyvar_vol``: Storage for AnyVar application data. Required when running ``compose.anyvar.yaml``.

Before starting a stack that relies on external volumes, ensure the required volumes exist. For example:

.. code-block:: bash

   docker volume create anyvlm_vol
   docker volume create seqrepo_vol
   docker volume create uta_vol
   docker volume create anyvar_vol

Running the default stack
-------------------------

If you already have AnyVar running, you can start AnyVLM on its own:

.. code-block:: bash

   docker compose -f compose.yaml up

If you do not already have AnyVar running, you can start AnyVLM together with the provided AnyVar services:

.. code-block:: bash

   docker compose -f compose.yaml -f compose.anyvar.yaml up

Development configuration
-------------------------

For local development where you already have AnyVar running, start the AnyVLM development services:

.. code-block:: bash

   docker compose -f compose.dev.yaml up

If you do not already have AnyVar running, include the AnyVar configuration:

.. code-block:: bash

   docker compose -f compose.dev.yaml -f compose.anyvar.yaml up

.. note::

   Add the ``--build`` flag if you change build-time configuration such as dependencies or the Dockerfile.

Running tests
-------------

To start the services required for running tests, use the test configuration:

.. code-block:: bash

   docker compose -f compose.test.yaml up

This configuration is intended for local testing and uses test-specific services and volumes.

Makefile shortcuts
------------------

For convenience, common Docker Compose commands are exposed via the project Makefile. These targets wrap the correct Compose file combinations so you do not need to remember which files must be used together.

The following Makefile targets are available:

.. code-block:: bash

   make volumes          # create volumes

   make up               # start the default stack (foreground)
   make up-d             # start the default stack (detached)

   make up-dev           # start the development stack (foreground)
   make up-dev-d         # start the development stack (detached)

   make up-dev-build     # rebuild the image and start the development stack (foreground)
   make up-dev-build-d   # rebuild the image and start the development stack (detached)

   make up-test          # start the test stack

   make stop             # stop running services without removing containers
   make down             # stop and remove containers
