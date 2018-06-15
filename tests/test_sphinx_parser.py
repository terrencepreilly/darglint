from unittest import TestCase

from darglint.lex import (
    lex,
)
from darglint.node import NodeType
from darglint.peaker import Peaker
from darglint.parse import (
    ParserException,
)
from darglint.sphinx_parse import (
    parse_short_description,
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
