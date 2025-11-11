"""
PyResolvers - High-Performance DNS Resolver Validation & Speed Testing

Modern async DNS validator with speed testing and ordering.

Example:
    >>> from pyresolvers import Validator
    >>> validator = Validator()
    >>> results = validator.validate_by_speed(['1.1.1.1', '8.8.8.8'])
    >>> for server, latency in results:
    ...     print(f"{server}: {latency:.2f}ms")

High concurrency:
    >>> validator = Validator(concurrency=100)
    >>> results = validator.validate_by_speed(large_list)

Async usage:
    >>> import asyncio
    >>> results = await validator.validate_by_speed_async(servers)
"""

from __future__ import annotations

from .lib.core.__version__ import __version__
from .validator import ValidationResult, Validator

__all__ = ['Validator', 'ValidationResult', '__version__']
__version__ = __version__
