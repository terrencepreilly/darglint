import ast
from unittest import TestCase

from darglint.lex import (
    lex,
)
from darglint.node import NodeType
from darglint.peaker import Peaker
from darglint.parse.common import (
    ParserException,
)
from darglint.parse.common import (
    parse_keyword,
)
from darglint.parse.sphinx import (
    KEYWORDS,
    parse,
    parse_item,
    parse_long_description,
    parse_short_description,
)


class SphinxParserTest(TestCase):

    def test_parse_short_description_is_line(self):
        """Make sure a short description is just a single line."""
        content = 'Description!\n'
        node = parse_short_description(Peaker(lex(content)))
        node_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            node_types,
            [
                NodeType.WORD,
                NodeType.LINE,
                NodeType.SHORT_DESCRIPTION,
            ],
            'Unexpectedly got {}'.format([
                str(x) for x in node_types
            ])
        )

    def test_parse_short_description_one_word(self):
        """Make sure a single word can suffice."""
        content = 'Kills.\n'
        node = parse_short_description(Peaker(lex(content)))
        self.assertEqual(
            node.node_type,
            NodeType.SHORT_DESCRIPTION,
        )
        self.assertEqual(
            node.children[0].children[0].value,
            'Kills.',
        )

    def test_parse_short_description_multiple_words(self):
        """Make sure we can have a normal short description."""
        content = 'Flips the pancake.\n'
        node = parse_short_description(Peaker(lex(content)))
        self.assertEqual(
            node.node_type,
            NodeType.SHORT_DESCRIPTION,
        )
        self.assertEqual(
            len(node.children[0].children),
            3,
        )

    def test_short_description_can_have_colons(self):
        """Make sure special characters are fine."""
        content = ":param Something: Should be okay, I guess."
        node = parse_short_description(Peaker(lex(content)))
        self.assertEqual(
            node.node_type,
            NodeType.SHORT_DESCRIPTION,
        )

    def test_no_short_description_raises_exception(self):
        """Make sure no short description is unacceptable."""
        content = '\n'
        with self.assertRaises(ParserException):
            parse_short_description(Peaker(lex(content)))

    def test_parse_all_keywords(self):
        """Make sure we can parse all of the keywords."""
        for keyword in [
                'param', 'parameter', 'arg', 'argument', 'key', 'keyword',
                'type', 'raises', 'var', 'ivar', 'cvar',
                'vartype', 'returns', 'rtype',
                'yield', 'yields'
        ]:
            node = parse_keyword(Peaker(lex(keyword)), KEYWORDS)
            self.assertEqual(
                node.node_type,
                KEYWORDS[keyword],
            )
            self.assertEqual(
                node.value,
                keyword,
            )

    def test_item_without_argument(self):
        """Test that we can parse an item without an argument."""
        node = parse_item(
            Peaker(lex(':returns: A value.\n'), lookahead=2)
        )
        self.assertEqual(
            node.node_type,
            NodeType.RETURNS_SECTION,
        )
        node_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            node_types,
            [
                NodeType.COLON,
                NodeType.RETURNS,
                NodeType.COLON,
                NodeType.ITEM_NAME,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.LINE,
                NodeType.ITEM_DEFINITION,
                NodeType.ITEM,
                NodeType.RETURNS_SECTION,
            ],
            'Incorrect node types.  Got: \n\t{}'.format('\n\t'.join([
                str(x) for x in node_types
            ]))
        )

    def test_parse_argument_item(self):
        """Make sure we can parse an item with an arity of 1."""
        node = parse_item(
            Peaker(lex(':param x: A vector.\n'), lookahead=2)
        )
        self.assertEqual(
            node.node_type,
            NodeType.ARGS_SECTION,
        )
        node_types = [x.node_type for x in node.walk()]
        self.assertEqual(node_types, [
            NodeType.COLON,
            NodeType.ARGUMENTS,
            NodeType.WORD,
            NodeType.COLON,
            NodeType.ITEM_NAME,
            NodeType.WORD,
            NodeType.WORD,
            NodeType.LINE,
            NodeType.ITEM_DEFINITION,
            NodeType.ITEM,
            NodeType.ARGS_SECTION,
        ])

    def test_parse_type_item(self):
        """Ensure we can parse a type item correctly."""
        node = parse_item(
            Peaker(lex(':type priorities: List[int]\n'), lookahead=2)
        )
        self.assertEqual(
            node.node_type,
            NodeType.ARGS_SECTION,
        )
        node_types = [x.node_type for x in node.walk()]
        self.assertEqual(node_types, [
            NodeType.COLON,
            NodeType.TYPE,
            NodeType.WORD,
            NodeType.COLON,
            NodeType.ITEM_NAME,
            NodeType.WORD,
            NodeType.LINE,
            NodeType.ITEM_DEFINITION,
            NodeType.ITEM,
            NodeType.ARGS_SECTION,
        ])

    def test_parse_vartype_item(self):
        """Ensure we can parse a variable type description."""
        node = parse_item(
            Peaker(lex(':vartype foo: Dict[str][str]\n'), lookahead=2)
        )
        self.assertEqual(
            node.node_type,
            NodeType.VARIABLES_SECTION,
        )
        node_types = [x.node_type for x in node.walk()]
        self.assertEqual(node_types, [
            NodeType.COLON,
            NodeType.TYPE,
            NodeType.WORD,
            NodeType.COLON,
            NodeType.ITEM_NAME,
            NodeType.WORD,
            NodeType.LINE,
            NodeType.ITEM_DEFINITION,
            NodeType.ITEM,
            NodeType.VARIABLES_SECTION,
        ])

    def test_parse_long_description(self):
        """Make sure we can parse a long description."""
        node = parse_long_description(
            Peaker(lex('\n'.join([
                'A long description should be ',
                'able to be multiple lines.',
                '    Code snippets should be allowed.',
                'As should noqas # noqa',
            ])), lookahead=2)
        )
        self.assertEqual(
            node.node_type,
            NodeType.LONG_DESCRIPTION,
        )
        self.assertEqual(
            len(node.children),
            4,
            'Expected 4 children, but only parsed \n\n'
            + node.reconstruct_string()
        )
        self.assertTrue(all([
            x.node_type == NodeType.LINE
            for x in node.children
        ]))

    def test_parse_whole_docstring(self):
        """Make sure we can parse a whole docstring."""
        node = parse(Peaker(lex('\n'.join([
            'Format the exception with a traceback.',
            '',
            ':param etype: exception type',
            ':param value: exception value',
            ':param tb: traceback object',
            ':param limit: maximum number of stack frames to show',
            ':type limit: integer or None',
            ':rtype: list of strings',
            '',
        ])), lookahead=2))
        self.assertEqual(
            node.node_type,
            NodeType.DOCSTRING,
        )
        colon_count = 0
        has_type_for_limit = False
        for child in node.walk():
            if child.node_type == NodeType.WORD and child.value == 'limit':
                has_type_for_limit = True
            elif child.node_type == NodeType.COLON:
                colon_count += 1

        self.assertTrue(has_type_for_limit)
        self.assertEqual(colon_count, 12)

    def test_parse_from_ast(self):
        """Make sure we can parse the docstring as returned from ast."""
        func = '\n'.join([
            'def get_foobar(self, foo, bar=True):',
            '    """This gets the foobar',
            '',
            '    This really should have a full function definition, but I am too lazy.',
            '',
            '    >>> print get_foobar(10, 20)',
            '    30',
            '    >>> print get_foobar(\'a\', \'b\')',
            '    ab',
            '',
            '    Isn\'t that what you want?',
            '',
            '    :param foo: The foo.',
            '    :param bar: The bar.',
            '    :returns: The foobar.',
            '',
            '    """',
            '    return foo + bar',
        ])
        doc = ast.get_docstring(ast.parse(func).body[0])
        peaker = Peaker(lex(doc), lookahead=2)
        node = parse(peaker)
        self.assertEqual(
            node.node_type,
            NodeType.DOCSTRING,
        )

        param_count = 0
        return_count = 0
        words = set()
        for child in node.walk():
            if child.node_type == NodeType.ARGUMENTS:
                param_count += 1
            elif child.node_type == NodeType.RETURNS:
                return_count += 1
            elif child.node_type == NodeType.WORD:
                words.add(child.value)

        self.assertEqual(
            param_count, 2,
        )
        self.assertEqual(
            return_count, 1,
        )
        for word in ['foobar', 'lazy.', 'get_foobar', 'Isn\'t', 'foo']:
            self.assertTrue(
                word in words,
                '"{}" was not a word, but should have been.'.format(
                    word,
                )
            )
