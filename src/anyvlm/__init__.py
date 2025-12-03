"""Off-the-shelf solution for adding local aggregate-level variant information to a VLM network"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("anyvlm")
except PackageNotFoundError:
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError
