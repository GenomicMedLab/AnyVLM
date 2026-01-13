Logging Configuration
!!!!!!!!!!!!!!!!!!!!!

Default Behavior
========================

By default, an AnyVLM server logs at the ``INFO`` level to a file named ``anyvlm.log``, providing sufficient details for general usage. The default format includes timestamps, log levels, and messages.

Customizing Logging Configuration
=================================

AnyVLM can load a configuration dictionary from a YAML file for more granular control over logging behavior. To enable customized logging:

1. Create a YAML configuration file (e.g., ``logging.yaml``).
2. Set the environment variable ``ANYVLM_LOGGING_CONFIG`` to point to this file in your ``.env`` file: ::

    ANYVLM_LOGGING_CONFIG="/path/to/logging.yaml"

See the official Python documentation on `configuration dictionary schema <https://docs.python.org/3/library/logging.config.html#configuration-dictionary-schema>`_ for more details.

Applying Logging Configuration
==============================

Note that a service environment (e.g. a Python console, ``uvicorn`` server instance, or Celery worker) must be restarted for configuration changes to take effect.

Example YAML Configuration
==========================

Here's a comprehensive logging configuration example: ::

    version: 1
    disable_existing_loggers: true

    formatters:
      standard:
        format: "%(threadName)s %(asctime)s - %(name)s - %(levelname)s - %(message)s"

    handlers:
      console:
        class: logging.StreamHandler
        level: DEBUG
        formatter: standard
        stream: ext://sys.stdout

      file:
        class: logging.FileHandler
        level: INFO
        formatter: standard
        filename: "anyvlm.log"
        mode: "a"

    root:
      level: INFO
      handlers: [console, file]
      propagate: yes

    loggers:
      anyvlm.main:
        level: INFO
        handlers: [console, file]
        propagate: no

      anyvlm.storage
        level: DEBUG
        handlers: [console, file]
        propagate: no
