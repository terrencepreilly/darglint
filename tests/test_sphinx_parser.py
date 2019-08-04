import ast
from unittest import TestCase

from darglint.lex import (
    condense,
    lex,
)
from darglint.parse.sphinx import (
    parse,
)
from .sphinx_docstrings import docstrings


class SphinxParserTest(TestCase):

    def test_parse_short_description_is_line_cyk(self):
        """Make sure a short description is just a single line."""
        content = 'Description!'
        node = parse(condense(lex(content)))
        self.assertTrue(node.contains('short-description'))

    def test_parse_short_description_one_word_cyk(self):
        """Make sure a single word can suffice."""
        content = 'Kills.'
        node = parse(condense(lex(content)))
        self.assertTrue(node.contains('short-description'))

    def test_parse_short_description_multiple_words_cyk(self):
        """Make sure we can have a normal short description."""
        content = 'Flips the pancake.'
        node = parse(condense(lex(content)))
        self.assertTrue(node.contains('short-description'))

    def test_short_description_can_have_colons_cyk(self):
        """Make sure special characters are fine."""
        content = ":param Something: Should be okay, I guess."
        node = parse(condense(lex(content)))
        self.assertTrue(
            node.contains('short-description')
        )

    def test_parse_all_keywords_cyk(self):
        """Make sure we can parse all of the keywords."""
        keywords = {
            'arguments-section': [
                'param', 'parameter', 'arg', 'argument',
            ],
            'variables-section': [
                'key', 'keyword',
                'var', 'ivar', 'cvar',
            ],
            'argument-type-section': ['type'],
            'variable-type-section': ['vartype'],
            'raises-section': ['raises'],
            # 'returns-section': ['returns'],
            # 'return-type-section': ['rtype'],
            'yields-section': ['yield', 'yields'],
        }
        for keyword_section in keywords:
            for keyword in keywords[keyword_section]:
                docstring = 'Short description.\n\n:{} a: something'.format(
                    keyword,
                )
                node = parse(condense(lex(docstring)))
                self.assertTrue(
                    node.contains(keyword_section),
                    '{}: {}'.format(keyword_section, node)
                )

    def test_parse_return_keywords_cyk(self):
        keywords = {
            'returns-section': ['returns'],
            'return-type': ['rtype'],
        }
        for keyword_section in keywords:
            for keyword in keywords[keyword_section]:
                docstring = 'Short.\n\n:{}: something'.format(keyword)
                node = parse(condense(lex(docstring)))
                self.assertTrue(
                    node.contains(keyword_section),
                    '{}: {}'.format(keyword_section, node),
                )

    def test_item_without_argument_cyk(self):
        """Test that we can parse an item without an argument."""
        node = parse(condense(lex('a\n\n:returns: A value.')))
        self.assertTrue(node.contains('returns-section'))

    def test_parse_argument_item_cyk(self):
        """Make sure we can parse an item with an arity of 1."""
        node = parse(condense(lex('SD\n\n:param x: A vector.')))
        self.assertTrue(node.contains('arguments-section'))

    def test_parse_type_item_cyk(self):
        """Ensure we can parse a type item correctly."""
        node = parse(condense(lex('a\n\n:type priorities: List[int]')))
        self.assertTrue(
            node.contains('argument-type-section'),
            str(node),
        )

    def test_inline_item_type_cyk(self):
        """Make sure we can get the type of the item in its definition."""
        node = parse(condense(lex('short\n\n:param int x: A number.')))
        self.assertTrue(
            node.contains('arguments-section'),
            node,
        )

    def test_definition_with_colon_not_mistaken_for_inline_type_cyk(self):
        node = parse(condense(lex(
            'short description\n'
            '\n'
            ':param x: : That shouldn\'t be there.'
        )))
        self.assertTrue(
            node.contains('arguments-section'),
        )

    def test_item_name_with_return_can_have_type_but_not_argument_cyk(self):
        """Make sure the return item can can a type."""
        node = parse(condense(lex(
            'short\n\n:returns int: Whoa.'
        )))
        self.assertTrue(
            node.contains('returns-section'),
        )

    def test_parse_vartype_item_cyk(self):
        """Ensure we can parse a variable type description."""
        node = parse(condense(lex(
            'short\n\n:vartype foo: Dict[str][str]'
        )))
        self.assertTrue(
            node.contains('variable-type-section'),
            node,
        )

    def test_parse_long_description_cyk(self):
        """Make sure we can parse a long description."""
        node = parse(condense(lex('\n'.join([
            'Short descr.',
            '',
            'A long description should be ',
            'able to be multiple lines.',
            '    Code snippets should be allowed.',
            'As should noqas # noqa',
        ]))))
        self.assertTrue(
            node.contains('long-description'),
        )

    def test_parse_whole_docstring_cyk(self):
        """Make sure we can parse a whole docstring."""
        node = parse(condense(lex('\n'.join([
            'Format the exception with a traceback.',
            '',
            ':param etype: exception type',
            ':param value: exception value',
            ':param tb: traceback object',
            ':param limit: maximum number of stack frames to show',
            ':type limit: integer or None',
            ':rtype: list of strings',
        ]))))
        for section in [
            'arguments-section',
            'argument-type-section',
            'return-type-section',
        ]:
            self.assertTrue(node.contains(section), node)

    def test_multiple_line_item_definition_cyk(self):
        """Make sure item definitions can span multiple lines."""
        func = '\n'.join([
            'def do_nothing(x):',
            '    """Do nothing with x.',
            '    ',
            '    :param x: This is an argument which must be ',
            '        qualified by a large amount of text.',
            '',
            '    """',
            '    pass',
        ])
        doc = ast.get_docstring(ast.parse(func).body[0])
        node = parse(condense(lex(doc)))
        self.assertTrue(
            node.contains('arguments-section'),
            node,
        )

    def test_parse_from_ast_cyk(self):
        """Make sure we can parse the docstring as returned from ast."""
        func = '\n'.join([
            'def get_foobar(self, foo, bar=True):',
            '    """This gets the foobar',
            '',
            '    This really should have a full function definition, but I '
            'am too lazy.',
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
        node = parse(condense(lex(doc)))
        self.assertTrue(
            node.contains('arguments-section'),
            node,
        )
        self.assertTrue(
            node.contains('returns-section'),
            node,
        )

    def test_parser_sections_correctly(self):
        program = '\n'.join([
            'def func(x, l):',
            '    """Add an item to the head of the list.',
            '    ',
            '    :param x: The item to add to the list.',
            '    :return: The list with the item attached.',
            '    ',
            '    """',
            '    return l.appendleft(x)',
        ])
        doc = ast.get_docstring(ast.parse(program).body[0])
        tokens = condense(lex(doc))
        node = parse(tokens)
        self.assertTrue(
            node.contains('returns-section'),
        )
        self.assertTrue(
            node.contains('arguments-section'),
        )


class CompatibilityTest(TestCase):
    """Tests against real-world docstrings."""

    def test_parser_can_parse_all_docstrings_cyk(self):
        for docstring in docstrings():
            node = parse(condense(lex(docstring)))
            self.assertTrue(node)
