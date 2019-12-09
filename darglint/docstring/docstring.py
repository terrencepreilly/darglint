from typing import (
    Optional,
    Union,
)

from ..config import Configuration
from .base import BaseDocstring  # noqa
from . import google, sphinx


class Docstring(object):
    """A factory method for creating docstrings."""

    @staticmethod
    def from_google(root, config=None):
        # type: (str, Optional[Configuration]) -> BaseDocstring
        return google.Docstring(root, config=config)

    @staticmethod
    def from_sphinx(root, config=None):
        # type: (str, Optional[Configuration]) -> BaseDocstring
        return sphinx.Docstring(root, config=config)
