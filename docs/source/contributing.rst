Contributing to AnyVLM
!!!!!!!!!!!!!!!!!!!!!!

Installing For Development
==========================

Clone and enter the repo, use the ``devready`` Makefile target to set up a virtual environment, then activate it and install pre-commit hooks:

.. code-block:: shell

    git clone https://github.com/genomicmedlab/anyvlm.git
    cd anyvlm
    make devready
    source venv/3.11/bin/activate
    pre-commit install

Testing
=======

Some configuration is required to run tests:

* **Install test dependencies** - in your AnyVLM environment, ensure that the ``test`` dependency group is available by running ``make testready`` in the root directory.
* **Configure test database** - tests currently make use of two distinct database connection URIs (though they technically could both point to the same place without much issue at present):

.. list-table::
   :header-rows: 1

   * - Database
     - Environment variable
     - Default connection URI
   * - AnyVLM DB (for :py:class:`~anyvlm.storage.postgres.PostgresObjectStore`)
     - ``ANYVLM_TEST_STORAGE_URI``
     - ``"postgresql://postgres:postgres@localhost:5432/anyvlm_test"``
   * - AnyVar DB (for testing :py:class:`~anyvlm.anyvar.python_client.PythonAnyVarClient`)
     - ``ANYVLM_ANYVAR_TEST_STORAGE_URI``
     - ``"postgresql://postgres:postgres@localhost:5432/anyvlm_anyvar_test"``

.. note::

    Ensure that the databases and roles are available in the PostgreSQL instance.

    For example, to support the connection string ``"postgresql://anyvlm_test_user:anyvlm_test_pw@localhost:5432/anyvlm_test_db"``, run:

    .. code-block::

       psql -U postgres -C "CREATE USER anyvlm_test_user WITH PASSWORD anyvlm_test_pw; CREATE DATABASE anyvlm_test_db WITH OWNER anyvlm_test_user;"``

Tests are invoked with the ``pytest`` command. The project Makefile includes an easy shortcut:

.. code-block:: shell

   make test

Documentation
=============

To build documentation, use the ``docs`` Makefile target from the project root directory:

.. code-block::

   make docs

HTML output is built in the subdirectory ``docs/build/html/``.

The docs use `Sphinx GitHub Changelog <https://github.com/ewjoachim/sphinx-github-changelog>`_ to automatically generate the :doc:`changelog <changelog>` page. A GitHub API token must be provided for the Sphinx build process to fetch GitHub release history and generate this page. If not provided, an error will be logged during the build and the page will be blank.
