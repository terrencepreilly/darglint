from unittest import (
    TestCase,
)

from bnf_to_cnf.node import (
    Node,
    NodeType,
)
from bnf_to_cnf.parser import (
    Parser,
)
from utils import (
    random_string,
)

MAX_REPS = 100


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

    def test_terminals_equal(self):
        for _ in range(MAX_REPS):
            name = random_string()
            other_name = random_string()
            while name == other_name:
                name = random_string()

            self.assertTrue(
                Node(NodeType.TERMINAL, value=name).equals(
                    Node(NodeType.TERMINAL, value=name)
                )
            )
            self.assertFalse(
                Node(NodeType.TERMINAL, value=name).equals(
                    Node(NodeType.TERMINAL, value=other_name)
                ),
            )

    def test_grammars_equal(self):
        grammarA = '<A> ::= "b" | "c"'
        self.assertTrue(
            Parser().parse(grammarA).equals(
                Parser().parse(grammarA)
            )
        )
        grammarB = (
            '<Q> ::= "chicken"\n'
            '<D> ::= "sargh"'
        )
        self.assertTrue(
            Parser().parse(grammarB).equals(
                Parser().parse(grammarB)
            ),
        )
        self.assertFalse(
            Parser().parse(grammarA).equals(
                Parser().parse(grammarB)
            ),
        )

    def test_empty_nodes_equal(self):
        for node_type in [
            NodeType.SEQUENCE, NodeType.GRAMMAR, NodeType.EXPRESSION
        ]:
            self.assertTrue(
                Node(node_type, children=[]).equals(
                    Node(node_type, children=[])
                ),
            )

    def test_external_filename_preserved_in_both_python_and_bnf(self):
        external = (
            'from darglint.parse.identifiers import (\n'
            '    ArgumentIdentifier,\n'
            ')\n'
        )
        grammar = f'''
        {external}

        <A> ::= "A"
        '''
        node = Parser().parse(grammar)
        self.assertTrue(external in str(node))
        self.assertTrue(external in node.to_python())
