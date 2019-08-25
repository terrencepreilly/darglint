from typing import Union  # noqa

from .base import BaseDocstring  # noqa
from . import google, sphinx


class Docstring(object):
    """A factory method for creating docstrings."""

    @staticmethod
    def from_google(root):
        # type: (str) -> BaseDocstring
        return google.Docstring(root)

    @staticmethod
    def from_sphinx(root):
        # type: (str) -> BaseDocstring
        return sphinx.Docstring(root)
