"""Tests for the parser Node class."""
from darglint.node import (
    Node,
    NodeType,
)
from darglint.token import (
    Token,
    TokenType,
)

from unittest import TestCase


class NodeTestCase(TestCase):
    """Tests for Node."""

    def test_node_has_type_value_and_children(self):
        Node(
            node_type=NodeType.DOCSTRING,
            children=[
                Node(
                    node_type=NodeType.SUMMARY,
                    value='This is a docstring.',
                ),
            ]
        )

    def test_supplying_tokens_sets_line_number(self):
        """Make sure giving tokens will set the line numbers to the range."""
        token = Token(value="a", token_type=TokenType.WORD, line_number=3)
        node = Node(
            value="a b c",
            node_type=NodeType.LONG_DESCRIPTION,
            token=token,
        )
        self.assertEqual(
            node.line_numbers,
            (3,3),
            'The line numbers should be a tuple of the lowest and highest.'
        )

    def test_breadth_first_walk_no_leaves(self):
        r"""Make sure we can do a breadth-first walk without traversing leaves.

        Structure:
                        Docstring
                            |
                         Summary
                        /   |   \
                   Return square root.

        """
        tree = Node(
            node_type=NodeType.DOCSTRING,
            children=[
                Node(
                    node_type=NodeType.SUMMARY,
                    children=[
                        Node(
                            node_type=NodeType.WORD,
                            value='Return',
                        ),
                        Node(
                            node_type=NodeType.WORD,
                            value='square',
                        ),
                        Node(
                            node_type=NodeType.WORD,
                            value='root.',
                        )
                    ]
                ),
            ]
        )
        traversal = list(tree.breadth_first_walk(leaves=False))
        expected_types_and_values = [
            (NodeType.DOCSTRING, None),
            (NodeType.SUMMARY, None),
        ]
        self.assertEqual(
            [(x.node_type, x.value) for x in traversal],
            expected_types_and_values,
        )

    def test_breadth_first_walk(self):
        """Make sure we can do a breadth-first walk.

        This will be much easier for finding sections.

        Structure:
                        Docstring
                         |     |
                   Summary     Description
                  /   |   |     |     |   |
            Return square root. Fails for negatives.

        """
        tree = Node(
            node_type=NodeType.DOCSTRING,
            children=[
                Node(
                    node_type=NodeType.SUMMARY,
                    children=[
                        Node(
                            node_type=NodeType.WORD,
                            value='Return',
                        ),
                        Node(
                            node_type=NodeType.WORD,
                            value='square',
                        ),
                        Node(
                            node_type=NodeType.WORD,
                            value='root.',
                        )
                    ]
                ),
                Node(
                    node_type=NodeType.DESCRIPTION,
                    children=[
                        Node(
                            node_type=NodeType.WORD,
                            value='Fails',
                        ),
                        Node(
                            node_type=NodeType.WORD,
                            value='for',
                        ),
                        Node(
                            node_type=NodeType.WORD,
                            value='negatives.',
                        ),
                    ],
                ),
            ]
        )
        traversal = list(tree.breadth_first_walk())
        expected_types_and_values = [
            (NodeType.DOCSTRING, None),
            (NodeType.SUMMARY, None),
            (NodeType.DESCRIPTION, None),
            (NodeType.WORD, 'Return'),
            (NodeType.WORD, 'square'),
            (NodeType.WORD, 'root.'),
            (NodeType.WORD, 'Fails'),
            (NodeType.WORD, 'for'),
            (NodeType.WORD, 'negatives.'),
        ]
        self.assertEqual(
            [(x.node_type, x.value) for x in traversal],
            expected_types_and_values,
        )

    def test_walk_tree_does_post_order_traversal(self):
        """Make sure walking is done post-order.

        Structure:
                        Docstring
                         |     |
                   Summary     Description
                  /   |   |     |     |   |
            Return square root. Fails for negatives.

        """
        tree = Node(
            node_type=NodeType.DOCSTRING,
            children=[
                Node(
                    node_type=NodeType.SUMMARY,
                    children=[
                        Node(
                            node_type=NodeType.WORD,
                            value='Return',
                        ),
                        Node(
                            node_type=NodeType.WORD,
                            value='square',
                        ),
                        Node(
                            node_type=NodeType.WORD,
                            value='root.',
                        )
                    ]
                ),
                Node(
                    node_type=NodeType.DESCRIPTION,
                    children=[
                        Node(
                            node_type=NodeType.WORD,
                            value='Fails',
                        ),
                        Node(
                            node_type=NodeType.WORD,
                            value='for',
                        ),
                        Node(
                            node_type=NodeType.WORD,
                            value='negatives.',
                        ),
                    ],
                ),
            ]
        )
        traversal = list(tree.walk())
        expected_types_and_values = [
            (NodeType.WORD, 'Return'),
            (NodeType.WORD, 'square'),
            (NodeType.WORD, 'root.'),
            (NodeType.SUMMARY, None),
            (NodeType.WORD, 'Fails'),
            (NodeType.WORD, 'for'),
            (NodeType.WORD, 'negatives.'),
            (NodeType.DESCRIPTION, None),
            (NodeType.DOCSTRING, None),
        ]
        self.assertEqual(
            [(x.node_type, x.value) for x in traversal],
            expected_types_and_values,
        )
