"""Tests for writing a new parser."""

from unittest import TestCase

from darglint.node import (
    Node,
    NodeType,
)
from darglint.lex import (
    lex
)
from darglint.new_parse import (
    parse_keyword,
    parse_indent,
)
from darglint.peaker import (
    Peaker
)
from darglint.parse import ParserException


class NewParserTestCase(TestCase):
    """Tests for developing a new parser."""

    def test_parse_keyword(self):
        """Make sure we can parse keywords."""
        for word, node_type in [
                ('Returns', NodeType.RETURNS),
                ('Args', NodeType.ARGUMENTS),
                ('Arguments', NodeType.ARGUMENTS),
                ('Yields', NodeType.YIELDS),
                ('Raises', NodeType.RAISES)
        ]:
            node = parse_keyword(Peaker(lex(word)))
            self.assertEqual(
                node.node_type,
                node_type
            )
            self.assertEqual(
                node.value,
                word,
            )

    def test_parse_keyword_fails(self):
        """Make sure incorrectly calling the keyword parse fails."""
        for word in ['Not', 'a', 'keyword', 'args']:
            with self.assertRaises(ParserException):
                parse_keyword(Peaker(lex(word)))

    def test_parse_indent(self):
        """Make sure we can correctly parse indents."""
        node = parse_indent(Peaker(lex(' '*4)))
        self.assertEqual(
            node.node_type,
            NodeType.INDENT,
        )
        self.assertEqual(
            node.value,
            ' ' * 4,
        )
        with self.assertRaises(ParserException):
            parse_keyword(Peaker(lex('a')))
