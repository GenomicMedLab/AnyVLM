.. _anyvar-config:

AnyVar Client Configuration
!!!!!!!!!!!!!!!!!!!!!!!!!!!

AnyVLM employs an `AnyVar <https://anyvar.readthedocs.org/en/stable/>`_ for internal variant storage. AnyVLM defines an internal client abstraction to either connect to AnyVar via HTTP request (:py:class:`~anyvlm.anyvar.http_client.HttpAnyVarClient`) or by instantiating the AnyVar within the AnyVLM process (:py:class:`~anyvlm.anyvar.python_client.PythonAnyVarClient`). The client instance is constructed by the :py:func:`~anyvlm.main.create_anyvar_client` factory function which references the ``ANYVAR_URI`` environmental variable to determine the kind of client.

* If ``ANYVAR_URI`` looks like an HTTP URL (i.e. it starts with ``"http://"`` or ``"https://"``), then an :py:class:`HTTP-based client <~anyvlm.anyvar.http_client.HttpAnyVarClient>` is constructed
* Otherwise,

.. list-table::
