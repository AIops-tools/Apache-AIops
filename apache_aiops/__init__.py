"""Apache AIops: governed Apache HTTP Server operations."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("apache-aiops")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"
