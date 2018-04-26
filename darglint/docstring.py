"""Defines the Docstring class, which interprets the AST."""

from collections import defaultdict
from typing import (
    Dict,
    List,
)
from .node import (
    Node,
    NodeType,
)


class Docstring(object):
    """The docstring class interprets the AST of a docstring."""

    def __init__(self, root):
        # type: (Node) -> None
        """Create a new docstring from the AST."""
        self.root = root
        self.long_description = ''
        self.arguments_descriptions = dict()  # type: Dict[str, str]
        self.argument_types = dict()  # type: Dict[str, str]
        self.returns_description = ''
        self.return_type = None  # type: str
        self.yields_description = ''
        self.raises_descriptions = dict()  # type: Dict[str, str]
        self.noqa = dict()  # type: Dict[str, str]

        self._lookup = self._discover()

    def _discover(self):
        # type: () -> Dict[NodeType, List[Node]]
        """Walk the tree, finding all non-terminal nodes."""
        lookup = defaultdict(list) # type: Dict[NodeType, List[Node]]
        for node in self.root.breadth_first_walk(leaves=False):
            lookup[node.node_type].append(node)
        return lookup

    @property
    def short_description(self):
        # () -> Node
        """Get the short description of the docstring.

        Returns:
            The short description in the docstring, or None.

        """
        nodes = self._lookup[NodeType.SHORT_DESCRIPTION]
        if not nodes:
            return None
        words = list()
        for node in nodes[0].walk():
            if node.is_leaf:
                words.append(node.value)
        return ' '.join(words)

    @property
    def ignore_all(self):
        # type: () -> bool
        """Return whether we should ignore everything in the docstring.

        This happens when there is a bare noqa in the docstring, or
        there is "# noqa: *" in the docstring.

        Returns: True if we should ignore everything, otherwise false.

        """
        for node in self._lookup[NodeType.NOQA]:
            body = None
            for child in node.walk():
                if child.node_type == NodeType.NOQA_BODY:
                    body = child
                    break

            if body is None or any([x.value == '*' for x in body.children]):
                return True

        return False
