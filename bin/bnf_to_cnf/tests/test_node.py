from unittest import (
    TestCase,
)

from bnf_to_cnf.node import (
    Node,
    NodeType,
)


class NodeTest(TestCase):

    def test_str(self):
        node = Node(
            NodeType.GRAMMAR,
            children=[
                Node(
                    NodeType.PRODUCTION,
                    children=[
                        Node(
                            NodeType.SYMBOL,
                            value='header',
                        ),
                        Node(
                            NodeType.EXPRESSION,
                            children=[
                                Node(
                                    NodeType.SEQUENCE,
                                    children=[
                                        Node(
                                            NodeType.SYMBOL,
                                            value='arg',
                                        )
                                    ],
                                ),
                                Node(
                                    NodeType.SEQUENCE,
                                    children=[
                                        Node(
                                            NodeType.SYMBOL,
                                            value='returns',
                                        )
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
                Node(
                    NodeType.PRODUCTION,
                    children=[
                        Node(
                            NodeType.SYMBOL,
                            value='arg',
                        ),
                        Node(
                            NodeType.EXPRESSION,
                            children=[
                                Node(
                                    NodeType.SEQUENCE,
                                    children=[
                                        Node(
                                            NodeType.TERMINAL,
                                            value='"Arg"',
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )
        self.assertEqual(
            str(node),
            '\n'.join([
                '<header> ::= <arg> | <returns>',
                '<arg> ::= "Arg"',
            ]),
        )
