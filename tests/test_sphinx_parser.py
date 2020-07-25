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
from darglint.utils import (
    CykNodeUtils,
)
from darglint.errors import (
    IndentError,
)


class SphinxParserTest(TestCase):

    def assert_has_annotation(self, node, annotation):
        for child in node.walk():
            for a in child.annotations:
                if a == annotation:
                    return
        self.fail('Could not find annotation {}'.format(annotation.__name__))

    def assert_has_no_annotation(self, node, annotation):
        for child in node.walk():
            for a in child.annotations:
                if a == annotation:
                    self.fail('Unexpectedly encountered {}'.format(
                        annotation,
                    ))

    def test_parse_short_description_is_line_cyk(self):
        """Make sure a short description is just a single line."""
        content = 'Description!'
        node = parse(condense(lex(content)))
        self.assertTrue(CykNodeUtils.contains(node, 'short-description'))

    def test_parse_short_description_one_word_cyk(self):
        """Make sure a single word can suffice."""
        content = 'Kills.'
        node = parse(condense(lex(content)))
        self.assertTrue(CykNodeUtils.contains(node, 'short-description'))

    def test_parse_short_description_multiple_words_cyk(self):
        """Make sure we can have a normal short description."""
        content = 'Flips the pancake.'
        node = parse(condense(lex(content)))
        self.assertTrue(CykNodeUtils.contains(node, 'short-description'))

    def test_short_description_can_have_colons_cyk(self):
        """Make sure special characters are fine."""
        content = ":Something Should be okay, I guess."
        node = parse(condense(lex(content)))
        self.assertTrue(
            CykNodeUtils.contains(node, 'short-description')
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
                    CykNodeUtils.contains(node, keyword_section),
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
                    CykNodeUtils.contains(node, keyword_section),
                    '{}: {}'.format(keyword_section, node),
                )

    def test_item_without_argument_cyk(self):
        """Test that we can parse an item without an argument."""
        node = parse(condense(lex('a\n\n:returns: A value.')))
        self.assertTrue(CykNodeUtils.contains(node, 'returns-section'))

    def test_parse_argument_item_cyk(self):
        """Make sure we can parse an item with an arity of 1."""
        node = parse(condense(lex('SD\n\n:param x: A vector.')))
        self.assertTrue(CykNodeUtils.contains(node, 'arguments-section'))

    def test_parse_type_item_cyk(self):
        """Ensure we can parse a type item correctly."""
        node = parse(condense(lex('a\n\n:type priorities: List[int]')))
        self.assertTrue(
            CykNodeUtils.contains(node, 'argument-type-section'),
            str(node),
        )

    def test_inline_item_type_cyk(self):
        """Make sure we can get the type of the item in its definition."""
        node = parse(condense(lex('short\n\n:param int x: A number.')))
        self.assertTrue(
            CykNodeUtils.contains(node, 'arguments-section'),
            node,
        )

    def test_definition_with_colon_not_mistaken_for_inline_type_cyk(self):
        node = parse(condense(lex(
            'short description\n'
            '\n'
            ':param x: : That shouldn\'t be there.'
        )))
        self.assertTrue(
            CykNodeUtils.contains(node, 'arguments-section'),
        )

    def test_parse_vartype_item_cyk(self):
        """Ensure we can parse a variable type description."""
        node = parse(condense(lex(
            'short\n\n:vartype foo: Dict[str][str]'
        )))
        self.assertTrue(
            CykNodeUtils.contains(node, 'variable-type-section'),
            node,
        )

    def test_parse_multiline_return(self):
        """Ensure we can parse multiline returns.

        See Issue #63.

        """
        return_variants = [
            ':return: shape: (n, m), dtype: float\n'
            '    Detailed description.\n',

            # No trailing newline
            ':return: shape: (n, m), dtype: float\n'
            '    Detailed description.',

            # Extra separation without indent
            ':return: shape: (n, m), dtype: float\n'
            '\n'
            '    Detailed description\n',

            # Extra separation with indent
            ':return: shape: (n, m), dtype: float\n'
            '    \n'
            '    Detailed description\n',
        ]
        doc_template = 'Short description.\n\n{}'
        for return_variant in return_variants:
            raw_docstring = doc_template.format(return_variant)
            tokens = condense(lex(raw_docstring))
            node = parse(tokens)
            self.assertTrue(
                CykNodeUtils.contains(node, 'returns-section'),
                'Variant failed: {}'.format(repr(return_variant)),
            )

    def test_parse_multiline_raises(self):
        """Ensure we can parse multiline raises.

        See Issue #63.

        """
        raises_variants = [
            ':raises RuntimeError:\n'
            '    Long description of why this happens.',

            # Newline-terminated.
            ':raises RuntimeError:\n'
            '    Long description of why this happens.\n',

            # TODO: Fix the top-parser to parse this correctly.
            # It breaks this into two sections.
            #
            # # Separation without indent
            # ':raises RuntimeError:\n'
            # '\n'
            # '    Long description of why this happens.',

            # Separation with indent
            ':raises RuntimeError:\n'
            '    \n'
            '    Long description of why this happens.',
        ]
        doc_template = 'Short description.\n\n{}'
        for raises_variant in raises_variants:
            raw_docstring = doc_template.format(raises_variant)
            tokens = condense(lex(raw_docstring))
            node = parse(tokens)
            self.assertTrue(
                CykNodeUtils.contains(node, 'raises-section'),
                'Variant failed: {}'.format(repr(raises_variant)),
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
            CykNodeUtils.contains(node, 'long-description'),
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
            self.assertTrue(CykNodeUtils.contains(node, section), node)

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
            CykNodeUtils.contains(node, 'arguments-section'),
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
            CykNodeUtils.contains(node, 'arguments-section'),
            node,
        )
        self.assertTrue(
            CykNodeUtils.contains(node, 'returns-section'),
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
            CykNodeUtils.contains(node, 'returns-section'),
        )
        self.assertTrue(
            CykNodeUtils.contains(node, 'arguments-section'),
        )

    def test_no_short_description_checks_for_others(self):
        program = '\n'.join([
            '@abstract.abstractmethod',
            'def __init__(self, config: dict):',
            '     """',
            '',
            '    :param config: config dict user defined in config file.',
            '    """',
        ])
        doc = ast.get_docstring(ast.parse(program).body[0])
        tokens = condense(lex(doc))
        node = parse(tokens)
        self.assertTrue(
            CykNodeUtils.contains(node, 'arguments-section')
        )

    def test_multiline_param_without_indent_raises_error(self):
        program = '\n'.join([
            'def f(x):',
            '    """Maps some x to some y.',
            '',
            '    :param x: A value of',
            '    some kind.',
            '    :return: Some value of the same kind.',
            '',
            '    """',
            '    return x',
        ])
        doc = ast.get_docstring(ast.parse(program).body[0])
        tokens = condense(lex(doc))
        node = parse(tokens)
        self.assertTrue(
            CykNodeUtils.contains(node, 'arguments-section')
        )
        self.assert_has_annotation(node, IndentError)

    def test_multiline_param_with_indent_doesnt_raise_error(self):
        program = '\n'.join([
            'def f(x):',
            '    """Maps some x to some y.',
            '',
            '    :param x: A value of',
            '        some kind.',
            '    :return: Some value of the same kind.',
            '',
            '    """',
            '    return x',
        ])
        doc = ast.get_docstring(ast.parse(program).body[0])
        tokens = condense(lex(doc))
        node = parse(tokens)
        self.assertTrue(
            CykNodeUtils.contains(node, 'arguments-section')
        )
        self.assert_has_no_annotation(node, IndentError)


class CompatibilityTest(TestCase):
    """Tests against real-world docstrings."""

    def test_parser_can_parse_all_docstrings_cyk(self):
        for docstring in docstrings():
            node = parse(condense(lex(docstring)))
            self.assertTrue(node)
