from unittest import (
    TestCase,
)
from bnf_to_cnf.parser import (
    Parser,
)
from bnf_to_cnf.node import (
    Node,
)


class ParserTestCase(TestCase):

    def test_parse_simple_rule(self):
        """Make sure a simple, terminal rule works."""
        node = Parser().parse('<args> ::= "Args"')
        self.assertTrue(isinstance(node, Node))
        self.assertEqual(
            str(node),
            '<args> ::= "Args"',
        )

    def test_parse_rule_with_spaces(self):
        """Test conjunction in rules."""
        node = Parser().parse('<heading> ::= <ident> ":"')
        self.assertEqual(
            str(node),
            '<heading> ::= <ident> ":"',
        )

    def test_multiple_sequences(self):
        """Make sure we can have multiple sequences."""
        node = Parser().parse('<heading> ::= "Args" ":" | "Returns" ":"')
        self.assertEqual(
            str(node),
            '<heading> ::= "Args" ":" | "Returns" ":"'
        )

    def test_multiple_rules(self):
        """Make sure we can handle multiple rules in a grammar."""
        node = Parser().parse('''
            <head> ::= <keyword> ":"

            <keyword> ::= "Args" | "Returns"
        ''')
        self.assertEqual(
            str(node),
            '\n'.join([
                '<head> ::= <keyword> ":"',
                '<keyword> ::= "Args" | "Returns"',
            ]),
        )
