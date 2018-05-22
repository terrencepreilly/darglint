"""Defines a node for the docstring AST."""

from collections import deque

from enum import Enum
from typing import (
    Any,
    List,
    Iterator,
    Tuple,
    Optional,
)
from .token import (
    Token,
)


class NodeType(Enum):
    """The type of node in a docstring."""
    # Non-Terminals
    DOCSTRING = 0
    SUMMARY = 1
    DESCRIPTION = 2
    SHORT_DESCRIPTION = 26
    TYPE = 10
    LINE = 11
    SECTION_HEAD = 13
    SECTION_SIMPLE_BODY = 14
    SECTION_COMPOUND_BODY = 15
    SECTION = 16
    ITEM_NAME = 17
    ITEM_DEFINITION = 18
    ITEM = 19
    ARGS_SECTION = 22
    RAISES_SECTION = 23
    RETURNS_SECTION = 24
    YIELDS_SECTION = 25
    LONG_DESCRIPTION = 27
    NOQA = 28
    LIST = 29
    NOQA_HEAD = 30
    NOQA_BODY = 31

    # Terminals
    KEYWORD = 3
    WORD = 4
    COLON = 5
    RETURNS = 6
    ARGUMENTS = 7
    YIELDS = 8
    RAISES = 9
    INDENT = 12
    LPAREN = 20
    RPAREN = 21
    HASH = 32


class Node(object):
    """A node in a docstring AST."""

    def __init__(self, node_type, value=None, children=None, token=None):
        # type: (NodeType, str, List[Node], Token) -> None
        """Instantiate the new node.

        If the node is terminal, it will get the line number from the
        token.  If it is non-terminal, it will derive the line number(s)
        from the children.

        Args:
            node_type: The type of node.
            value: The value of the node.  Should only be specified for
                terminal nodes.
            children: The children of this node. Should only be specified
                for non-terminal nodes.
            token: The token this node was made from.  Should only be
                specified for terminal nodes.

        """
        self.node_type = node_type
        self.value = value
        self.children = children or list()
        self.line_numbers = None  # type: Optional[Tuple[int, int]]
        if token:
            self.line_numbers = (
                token.line_number,
                token.line_number
            )
        elif children:
            child_min_line_numbers = [
                x.line_numbers[0] for x in children
                if x.line_numbers
            ]
            child_max_line_numbers = [
                x.line_numbers[1] for x in children
                if x.line_numbers
            ]
            if child_min_line_numbers and child_max_line_numbers:
                self.line_numbers = (
                    min(child_min_line_numbers),
                    max(child_max_line_numbers),
                )

    @property
    def is_keyword(self):
        return self.node_type in {
            NodeType.KEYWORD,
            NodeType.RETURNS,
            NodeType.ARGUMENTS,
            NodeType.YIELDS,
            NodeType.RAISES,
        }

    @property
    def is_leaf(self):
        """Tell whether this node is a leaf.

        Returns:
            True if this node is a leaf.

        """
        return self.node_type in {
            NodeType.KEYWORD,
            NodeType.WORD,
            NodeType.COLON,
            NodeType.RETURNS,
            NodeType.ARGUMENTS,
            NodeType.YIELDS,
            NodeType.RAISES,
            NodeType.INDENT,
            NodeType.LPAREN,
            NodeType.RPAREN,
            NodeType.HASH,
        }

    def walk(self):
        # type: () -> Iterator[Node]
        """Iterate over nodes in the tree rooted at this node.

        Recursion isn't too horrible here, as the syntax tree
        in this case never gets very deep.  Does a post-order
        traversal of the tree.

        Yields:
            Nodes in the tree.

        """
        for child in self.children:
            yield from child.walk()
        yield self

    def breadth_first_walk(self, leaves=True):
        # type: (bool) -> Iterator[Node]
        """Iterate over the nodes in the tree using Breadth First Traversal.

        A breadth-first traversal will be much faster when identifying
        sections.

        Args:
            leaves: True if leaves of the tree should also be yielded,
                otherwise only parent nodes will be yielded.

        Yields:
            Nodes in the tree.

        """
        queue = deque()  # type: deque
        queue.appendleft(self)
        while queue:
            curr = queue.pop()
            yield curr
            queue.extendleft([
                child for child in curr.children
                if leaves or not child.is_leaf
            ])

    def reconstruct_string(self):
        # type: () -> str
        """Attempt to reconstruct how the node looked before.

        Unfortunately, with how the parser works, we can't do this
        perfectly.  Nor would it likely be worthwhile. For example, if
        there are extra spaces (not in multiples of 4), then they will
        not be represented.

        If the parser ever changes, this will likely have to change.
        Which is fine, because it's gross anyway.

        Returns:
            Something close to the original string.

        """
        lines = [[]]  # type: List[List[str]]
        keyword = None
        for child in self.walk():
            if child.node_type == NodeType.INDENT:
                # When joined, it will have 4 spaces.
                lines[-1].append(' '*3)
            elif child.node_type == NodeType.COLON:
                # Remove the space before the colon. (This is more common.)
                if keyword:
                    lines[-1].append(keyword + ':')
                    keyword = None
                    lines.append(list())
                elif lines[-1]:
                    lines[-1][-1] += ':'
                elif child.value:
                    lines[-1].append(child.value)
            elif child.is_keyword:
                # Keywords always have colons after them, so wait for
                # the colon.
                keyword = child.value
            elif child.is_leaf and child.value:
                lines[-1].append(child.value)
            elif child.node_type == NodeType.LINE:
                lines.append(list())
        return '\n'.join([' '.join(line) for line in lines])
