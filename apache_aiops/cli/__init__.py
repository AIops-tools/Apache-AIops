"""CLI package for apache-aiops.

Re-exports ``app`` so the pyproject entry point
``apache-aiops = "apache_aiops.cli:app"`` works unchanged.
"""

from apache_aiops.cli._root import app

__all__ = ["app"]
