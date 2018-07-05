from typing import Union  # noqa

from .base import BaseDocstring  # noqa
from . import google, sphinx

from ..node import Node  # noqa


class Docstring(object):
    """A factory method for creating docstrings."""

    @staticmethod
    def from_google(root):
        # type: (Union[Node, str]) -> BaseDocstring
        return google.Docstring(root)

    @staticmethod
    def from_sphinx(root):
        # type: (Union[Node, str]) -> BaseDocstring
        return sphinx.Docstring(root)
