"""Defines a node for the docstring AST."""

from enum import Enum
from typing import (
    Any,
    List,
    Iterator,
)


class NodeType(Enum):
    """The type of node in a docstring."""
    # Non-Terminals
    DOCSTRING = 0
    SUMMARY = 1
    DESCRIPTION = 2
    TYPE = 10
    LINE = 11

    # Terminals
    KEYWORD = 3
    WORD = 4
    COLON = 5
    RETURNS = 6
    ARGUMENTS = 7
    YIELDS = 8
    RAISES = 9
    INDENT = 12

class Node(object):
    """A node in a docstring AST."""

    def __init__(self, node_type, value=None, children=[]):
        # type: (NodeType, Any, List[Node]) -> None
        self.node_type = node_type
        self.value = value
        self.children = children

    def walk(self):
        # type: () -> Iterator[Node]
        """Iterate over nodes in the tree rooted at this node.

        Recursion isn't too horrible here, as the syntax tree
        in this case never gets very deep.  Does a post-order
        traversal of the tree.

        """
        for child in self.children:
            yield from child.walk()
        yield self
