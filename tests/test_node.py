"""Tests for the parser Node class."""
from darglint.node import (
    Node,
    NodeType,
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
