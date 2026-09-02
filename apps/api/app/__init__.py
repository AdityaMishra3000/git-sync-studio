"""GitSync Studio backend.

A modular monolith: one deployable FastAPI application whose feature modules are
isolated by package, plus a Celery worker that shares this codebase.
"""

__all__ = ["__version__"]

__version__ = "0.1.0"
