"""Tests for writing a new parser."""

from unittest import TestCase

from darglint.node import (
    NodeType,
)
from darglint.lex import (
    lex
)
from darglint.parse import (
    parse_keyword,
    parse_colon,
    parse_word,
    parse_type,
    parse_line,
    parse_line_with_type,
    parse_simple_section,
    parse_yields,
    parse_returns,
    parse_item,
    parse_compound_section,
    parse_args,
    parse_raises,
    parse_description,
    parse_short_description,
    parse_noqa,
    parse,
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
            node.children[1].value,
            'int',
        )

    def test_type_cannot_by_empty(self):
        """Make sure that if we have a type it cannot be empty."""
        with self.assertRaises(ParserException):
            parse_type(Peaker(lex('()')))

    def test_parse_compound_type(self):
        """Make sure we can parse a type declaration with multiple items.

        These items should form a comma-separated list, and be enclosed in
        parentheses.

        """
        node = parse_type(Peaker(lex('(int, optional)')))
        self.assertEqual(
            node.node_type,
            NodeType.TYPE,
        )
        self.assertEqual(
            node.children[1].value,
            'int,',
        )
        self.assertEqual(
            node.children[2].value,
            'optional',
        )

    def test_parse_type_with_colon(self):
        """Parse a type using the colon syntax."""
        node = parse_type(Peaker(lex('str:')))
        self.assertEqual(
            node.node_type,
            NodeType.TYPE,
        )
        self.assertEqual(
            node.children[0].value,
            'str',
        )

    def test_must_have_parentheses_around(self):
        """Make sure the type has to start with ( and end with )."""
        with self.assertRaises(ParserException):
            parse_type(Peaker(lex('(int')))
        with self.assertRaises(ParserException):
            parse_type(Peaker(lex('int)')))
        with self.assertRaises(ParserException):
            parse_type(Peaker(lex('( int (')))

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

    def test_parse_line_with_parentheses(self):
        """Make sure lines can have parentheses in them."""
        node= parse_line(Peaker(lex(
            'This is a (parenthis-containing) line.\n'
        )))
        self.assertEqual(
            node.node_type,
            NodeType.LINE,
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
            'Returns:\n'
            '    A meaningful value.\n'
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
                NodeType.RETURNS,
                NodeType.COLON,
                NodeType.SECTION_HEAD,
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
        """Make sure we can parse a line when it starts with a type."""
        node = parse_line_with_type(Peaker(lex(
            '    int: the square of something.\n'
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
            'Returns:\n'
            '    int: The square of something.\n'
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
                NodeType.RETURNS,
                NodeType.COLON,
                NodeType.SECTION_HEAD,
                NodeType.INDENT,
                NodeType.WORD,
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
            'Yields:\n'
            '    Nodes in a stream.\n'
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
                NodeType.YIELDS,
                NodeType.COLON,
                NodeType.SECTION_HEAD,
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
                'Args:\n'
                '    Not a simple section.\n'
                '\n'
            )))

    def test_parse_item(self):
        """Make sure we can parse the parts of a compound section."""
        node = parse_item(Peaker(lex(
            '    x (int): The first number\n'
            '        to add\n'
        ), lookahead=3))
        self.assertEqual(
            node.node_type,
            NodeType.ITEM,
        )
        child_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            child_types,
            [
                NodeType.INDENT,
                NodeType.WORD,
                NodeType.LPAREN,
                NodeType.WORD,
                NodeType.RPAREN,
                NodeType.TYPE,
                NodeType.ITEM_NAME,
                NodeType.COLON,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.LINE,
                NodeType.INDENT,
                NodeType.INDENT,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.LINE,
                NodeType.ITEM_DEFINITION,
                NodeType.ITEM,
            ]
        )

    def test_parse_compound(self):
        """Make sure we can parse a compound section."""
        node = parse_compound_section(Peaker(lex('\n'.join([
            'Args:',
            '    x: X.',
            '    y: Y1.',
            '        Y2.',
            '    z (int, optional): Z.',
            '\n'
        ])), lookahead=3))
        self.assertEqual(node.node_type, NodeType.SECTION)
        body = node.children[1]
        self.assertEqual(
            body.node_type,
            NodeType.SECTION_COMPOUND_BODY,
        )
        self.assertEqual(
            len(body.children),
            3,
        )
        self.assertEqual(
            body.children[0].node_type,
            NodeType.ITEM,
        )

    def test_parse_args(self):
        """Make sure we can parse an args section."""
        node = parse_args(Peaker(lex('\n'.join([
            'Args:',
            '    x: the item.',
            '\n',
        ])), lookahead=3))
        self.assertEqual(node.node_type, NodeType.ARGS_SECTION)

    def test_parse_raises(self):
        """Make sure we can parse the exceptions section."""
        node = parse_raises(Peaker(lex(
            'Raises:\n'
            '    ArrayIndexOutOfBounds: When the array index\n'
            '        is out of bounds.\n'
            '\n'
        ), lookahead=3))
        self.assertEqual(
            node.node_type,
            NodeType.RAISES_SECTION,
        )

    def test_parse_yields(self):
        node = parse_yields(Peaker(lex(
            'Yields:\n'
            '    The total amount of information.\n'
            '\n'
        ), lookahead=3))
        self.assertEqual(
            node.node_type,
            NodeType.YIELDS_SECTION,
        )

    def test_parse_returns(self):
        node = parse_returns(Peaker(lex(
            'Returns:\n'
            '    A number of different\n'
            '    people, even species.\n'
            '\n'
        ), lookahead=3))
        self.assertEqual(
            node.node_type,
            NodeType.RETURNS_SECTION,
        )

    def test_parse_short_description(self):
        """Make sure we can parse the first line in the docstring."""
        node = parse_short_description(Peaker(lex(
            'This is a short description.\n'
        ), lookahead=3))
        child_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            child_types,
            [
                NodeType.WORD,
            ] * 5 + [
                NodeType.SHORT_DESCRIPTION,
            ]
        )

    def test_parse_whole_description(self):
        """Make sure we can handle descriptions of multiple lines."""
        node = parse_description(Peaker(lex(
            'Short description\n'
            '\n'
            'Long : (description)\n'
            '\n'
            '    <code></code>\n'
            '\n'
        ), lookahead=3))
        child_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            child_types,
            [
                NodeType.WORD,
                NodeType.WORD,
                NodeType.SHORT_DESCRIPTION,
                NodeType.LINE,
                NodeType.WORD,
                NodeType.COLON,
                NodeType.LPAREN,
                NodeType.WORD,
                NodeType.RPAREN,
                NodeType.LINE,
                NodeType.LINE,
                NodeType.INDENT,
                NodeType.WORD,
                NodeType.LINE,
                NodeType.LINE,
                NodeType.LONG_DESCRIPTION,
                NodeType.DESCRIPTION,
            ]
        )

    def test_description_ends_with_sections(self):
        """Make sure the description section doesn't eat everything."""
        peaker = Peaker(lex(
            'Short description.\n'
            '\n'
            'Long Description.\n'
            '\n'
            'Returns:\n'
            '    Nothing!\n'
            '\n'
        ), lookahead=3)
        parse_description(peaker)
        self.assertTrue(
            peaker.has_next()
        )
        node = parse_returns(peaker)
        self.assertEqual(
            node.node_type,
            NodeType.RETURNS_SECTION,
        )


    def test_long_description_can_come_between_sections(self):
        """Make sure non-standard parts are treated as descriptions."""
        node = parse(Peaker(lex('\n'.join([
            'Double the number.',
            '',
            'Args:',
            '    x: The only argument..',
            '',
            'Requires:',
            '    Some kind of setup.',
            '',
        ])), lookahead=3))
        self.assertEqual(
            node.node_type,
            NodeType.DOCSTRING,
        )
        self.assertEqual(
            node.children[2].node_type,
            NodeType.LONG_DESCRIPTION,
        )

    def test_parses_all_section_types(self):
        """Make sure all section types can be parsed."""
        node = parse(Peaker(lex('\n'.join([
            'Short description.',
            '',
            'Long Description.',
            '',
            'Args:',
            '    x: The first argument with',
            '        two lines.',
            '    y: The second argument.',
            '',
            'Raises:',
            '    SomethingException: Randomly.',
            '',
            'Non-Standard:'
            '    Everything about this.',
            '',
            'Yields:',
            '    Values to analyze.',
            '\n',
        ])), lookahead=3))
        child_types = [x.node_type for x in node.children]
        self.assertEqual(
            child_types,
            [
                NodeType.DESCRIPTION,
                NodeType.ARGS_SECTION,
                NodeType.RAISES_SECTION,
                NodeType.LONG_DESCRIPTION,
                NodeType.YIELDS_SECTION,
            ]
        )

    def test_parse_bare_noqa_statement(self):
        """Make sure we can parse noqa statements."""
        node = parse_noqa(Peaker(lex('# noqa\n')))
        self.assertEqual(
            [x.node_type for x in node.walk()],
            [
                NodeType.HASH,
                NodeType.WORD,
                NodeType.NOQA_HEAD,
                NodeType.NOQA
            ]
        )

    def test_parse_noqa_with_target(self):
        """Make sure we can target a specific error message."""
        node = parse_noqa(Peaker(lex('# noqa: I203\n')))
        self.assertEqual(
            [x.node_type for x in node.walk()],
            [
                NodeType.HASH,
                NodeType.WORD,
                NodeType.NOQA_HEAD,
                NodeType.COLON,
                NodeType.WORD,
                NodeType.NOQA_BODY,
                NodeType.NOQA,
            ],
        )

    def test_parse_noqa_with_target_and_argument(self):
        """Make sure we can target specific args in a noqa."""
        node = parse_noqa(Peaker(lex('# noqa: I101 arg1, arg2\n')))
        self.assertEqual(
            [x.node_type for x in node.walk()],
            [
                NodeType.HASH,
                NodeType.WORD,
                NodeType.NOQA_HEAD,
                NodeType.COLON,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.LIST,
                NodeType.NOQA_BODY,
                NodeType.NOQA,
            ]
        )

    def test_parse_inline_noqa_statements(self):
        """Make sure we can parse noqa statements."""
        node = parse_line(Peaker(lex('Something something.  # noqa: I201\n')))
        child_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            child_types,
            [
                NodeType.WORD,
                NodeType.WORD,
                NodeType.HASH,
                NodeType.WORD,
                NodeType.NOQA_HEAD,
                NodeType.COLON,
                NodeType.WORD,
                NodeType.NOQA_BODY,
                NodeType.NOQA,
                NodeType.LINE,
            ]
        )

    def test_parse_long_description_with_noqa(self):
        """Make sure noqas can appear in a global scope."""
        node = parse(Peaker(lex('\n'.join([
            'Short description can\'t have a noqa.'
            ''
            'But a long description can.'
            ''
            '# noqa: I101 arg1'
            '\n'
        ])), lookahead=3))
