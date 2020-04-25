from typing import (
    Optional,
    Union,
)

from .base import BaseDocstring  # noqa
from . import google, sphinx, numpy


class Docstring(object):
    """A factory method for creating docstrings."""

    @staticmethod
    def from_google(root):
        # type: (str) -> BaseDocstring
        return google.Docstring(root)

    @staticmethod
    def from_sphinx(root, config=None):
        # type: (str) -> BaseDocstring
        return sphinx.Docstring(root)

    @staticmethod
    def from_numpy(root, config=None):
        # type: (str) -> BaseDocstring
        return numpy.Docstring(root)
