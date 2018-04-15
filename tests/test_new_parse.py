"""Tests for writing a new parser."""

from unittest import TestCase

from darglint.node import (
    NodeType,
)
from darglint.lex import (
    lex
)
from darglint.new_parse import (
    parse_keyword,
    parse_colon,
    parse_word,
    parse_type,
    parse_line,
    parse_line_with_type,
    parse_simple_section,
    parse_item,
)
from darglint.peaker import (
    Peaker
)
from darglint.parse import ParserException


class NewParserTestCase(TestCase):
    """Tests for developing a new parser.

    The final tree will not have any whitespace (indents or
    newlines).  However, it will use these tokens while
    parsing.

    """

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

    def test_parse_colon(self):
        """Make sure we can parse colons."""
        node = parse_colon(Peaker(lex(':')))
        self.assertEqual(
            node.node_type, NodeType.COLON
        )

    def test_parse_word(self):
        """Make sure we can parse a word."""
        node = parse_word(Peaker(lex('joHwI\'')))
        self.assertEqual(
            node.node_type,
            NodeType.WORD,
        )
        self.assertEqual(
            node.value,
            'joHwI\'',
        )

    def test_parse_primitive_type(self):
        """Make sure we can parse a primitive type like int or str."""
        node = parse_type(Peaker(lex('(int)')))
        self.assertEqual(
            node.node_type,
            NodeType.TYPE,
        )
        self.assertEqual(
            node.value,
            'int',
        )

    def test_parse_type_with_colon(self):
        """Parse a type using the colon syntax."""
        node = parse_type(Peaker(lex('str:')))
        self.assertEqual(
            node.node_type,
            NodeType.TYPE,
        )
        self.assertEqual(
            node.value,
            'str',
        )

    def test_must_have_parentheses_around_without_spaces(self):
        """Make sure the type has to start with ( and end with )."""
        with self.assertRaises(ParserException):
            parse_type(Peaker(lex('(int')))
        with self.assertRaises(ParserException):
            parse_type(Peaker(lex('int)')))
        with self.assertRaises(ParserException):
            parse_type(Peaker(lex('( int )')))

    def test_parse_line_without_indent(self):
        """Make sure lines don't need to have indents."""
        node = parse_line(Peaker(lex('word word\n')))
        self.assertEqual(
            node.node_type,
            NodeType.LINE,
        )
        child_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            child_types,
            [NodeType.WORD, NodeType.WORD, NodeType.LINE],
        )

    def test_parse_empty_line(self):
        """Make sure we can parse a line with just an indent."""
        node = parse_line(Peaker(lex(' '*4 + '\n')))
        self.assertEqual(
            node.node_type,
            NodeType.LINE,
        )
        child_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            child_types,
            [NodeType.INDENT, NodeType.LINE],
        )

    def test_parse_line_with_words(self):
        """Make sure we can parse a line with words."""
        node = parse_line(Peaker(lex(
            '    this is a line with words\n'
        )))
        self.assertEqual(
            node.node_type,
            NodeType.LINE,
        )
        child_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            child_types,
            [
                NodeType.INDENT,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.LINE,
            ]
        )

    def test_parse_line_with_multiple_indents(self):
        """Make sure code snippets are okay."""
        node = parse_line(Peaker(lex(
            '        word.\n'
        )))
        self.assertEqual(
            node.node_type,
            NodeType.LINE,
        )
        child_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            child_types,
            [
                NodeType.INDENT,
                NodeType.INDENT,
                NodeType.WORD,
                NodeType.LINE,
            ]
        )

    def test_parse_line_with_colons(self):
        """Make sure lines with colons can be parsed."""
        node = parse_line(Peaker(lex(
            '    ::\n'
        )))
        self.assertEqual(
            node.node_type,
            NodeType.LINE,
        )
        child_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            child_types,
            [
                NodeType.INDENT,
                NodeType.COLON,
                NodeType.COLON,
                NodeType.LINE,
            ]
        )

    def test_parse_line_which_looks_like_definition(self):
        """Make sure a line which looks like a definition can be parsed."""
        node = parse_line(Peaker(lex(
            '    Returns: Some value.\n'
        )))
        self.assertEqual(
            node.node_type,
            NodeType.LINE,
        )
        child_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            child_types,
            [
                NodeType.INDENT,
                NodeType.RETURNS,
                NodeType.COLON,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.LINE,
            ]
        )

    def test_parse_returns_section(self):
        """Make sure can parse returns section."""
        node = parse_simple_section(Peaker(lex(
            '    Returns:\n'
            '        A meaningful value.\n'
            '\n'
        )))
        self.assertEqual(
            node.node_type,
            NodeType.SECTION,
        )
        child_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            child_types,
            [
                NodeType.INDENT,
                NodeType.RETURNS,
                NodeType.COLON,
                NodeType.SECTION_HEAD,
                NodeType.INDENT,
                NodeType.INDENT,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.LINE,
                NodeType.SECTION_SIMPLE_BODY,
                NodeType.SECTION,
            ]
        )

    def test_parse_line_with_type(self):
        """Make sure we can parse a line when it starts with a type.

        (Really, we should just equip the Peaker to allow constant 2
        lookahead -- the grammar requires it and this is just a workaround.)
        
        """
        node = parse_line_with_type(Peaker(lex(
            '        int: the square of something.\n'
        )))
        self.assertEqual(
            node.node_type,
            NodeType.LINE,
        )
        child_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            child_types,
            [
                NodeType.INDENT,
                NodeType.INDENT,
                NodeType.TYPE,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.LINE,
            ]
        )

    def test_parse_returns_section_with_type(self):
        """Make sure the returns section can have a type."""
        node = parse_simple_section(Peaker(lex(
            '    Returns:\n'
            '        int: The square of something.\n'
            '\n'
        )))
        self.assertEqual(
            node.node_type,
            NodeType.SECTION,
        )
        child_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            child_types,
            [
                NodeType.INDENT,
                NodeType.RETURNS,
                NodeType.COLON,
                NodeType.SECTION_HEAD,
                NodeType.INDENT,
                NodeType.INDENT,
                NodeType.TYPE,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.LINE,
                NodeType.SECTION_SIMPLE_BODY,
                NodeType.SECTION,
            ]
        )

    def test_parse_yields_section(self):
        """Make sure we can parse a yields section."""
        node = parse_simple_section(Peaker(lex(
            '    Yields:\n'
            '        Nodes in a stream.\n'
            '\n'
        )))
        self.assertEqual(
            node.node_type,
            NodeType.SECTION,
        )
        child_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            child_types,
            [
                NodeType.INDENT,
                NodeType.YIELDS,
                NodeType.COLON,
                NodeType.SECTION_HEAD,
                NodeType.INDENT,
                NodeType.INDENT,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.LINE,
                NodeType.SECTION_SIMPLE_BODY,
                NodeType.SECTION,
            ]
        )

    def test_parse_simple_section_cannot_start_with_args(self):
        """Make sure the simple section starts with return or yield."""
        with self.assertRaises(ParserException):
            parse_simple_section(Peaker(lex(
                '    Args:\n'
                '        Not a simple section.\n'
                '\n'
            )))

    def test_parse_item(self):
        """Make sure we can parse the parts of a compound section."""
        node = parse_item(Peaker(lex(
            'x (int): The first number\n'
            '            to add\n'
        ), lookahead=3))
        self.assertEqual(
            node.node_type,
            NodeType.ITEM,
        )
        child_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            child_types,
            [
                NodeType.WORD,
                NodeType.TYPE,
                NodeType.ITEM_NAME,
                NodeType.COLON,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.LINE,
                NodeType.INDENT,
                NodeType.INDENT,
                NodeType.INDENT,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.LINE,
                NodeType.ITEM_DEFINITION,
                NodeType.ITEM,
            ]
        )
