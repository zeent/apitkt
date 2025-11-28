"""
apitkt - Lightweight toolkit for building robust API clients in Python.
"""

from .client import APIClient
from .log import LoggedClient
from .exceptions import APIError, APIRequestError, APIResponseError

__all__ = [
    "APIClient",
    "LoggedClient",
    "APIError",
    "APIRequestError",
    "APIResponseError",
]

__version__ = "0.1.0"