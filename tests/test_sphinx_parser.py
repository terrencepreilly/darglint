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
    parse_short_description,
    parse_item,
    KEYWORDS,
)


# - [ ] Add support for the following fields:
#   - [ ] param, parameter, arg, argument, key, keyword: Description of a
#         parameter.
#   - [ ] type: Type of a parameter. Creates a link if possible.
#   - [ ] raises, raise, except, exception: That (and when) a specific
#         exception is raised.
#   - [ ] var, ivar, cvar: Description of a variable.
#   - [ ] vartype: Type of a variable. Creates a link if possible.
#   - [ ] returns, return: Description of the return value.
#   - [ ] rtype: Return type. Creates a link if possible.
#
#
# - Make sure types match if typing is also used:
#   :type priorities: list(int)
#   :type priorities: list[int]
#   :type mapping: dict(str, int)
#   :type mapping: dict[str, int]
#   :type point: tuple(float, float)
#   :type point: tuple[float, float]


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

#  item = indent, colon, keyword, [word], colon, item-body;
#  item-body = line, {line};
#  line = unline, newline
#  unline = { word
#           , hash
#           , colon
#           , indent
#           , keyword
#           , lparen
#           , rparen
#           }, [noqa];

    def test_item_without_argument(self):
        """Test that we can parse an item without an argument."""
        node = parse_item(
            Peaker(lex('    :returns: A value.\n'), lookahead=2)
        )
        self.assertEqual(
            node.node_type,
            NodeType.RETURNS_SECTION,
        )
        node_types = [x.node_type for x in node.walk()]
        self.assertEqual(
            node_types,
            [
                NodeType.INDENT,
                NodeType.COLON,
                NodeType.RETURNS,
                NodeType.COLON,
                NodeType.ITEM_NAME,
                NodeType.WORD,
                NodeType.WORD,
                NodeType.LINE,
                NodeType.ITEM_DEFINITION,
                NodeType.RETURNS_SECTION,
            ],
            'Incorrect node types.  Got: \n\t{}'.format('\n\t'.join([
                str(x) for x in node_types
            ]))
        )

    def test_parse_argument_item(self):
        """Make sure we can parse an item with an arity of 1."""
        pass
