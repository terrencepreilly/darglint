from unittest import TestCase

from random import (
    randint,
)

from darglint.parse.new_google import (
    top_parse,
    lookup,
    parse,
)
from darglint.parse.grammars.google_long_description import (
    LongDescriptionGrammar,
)
from darglint.token import (
    Token,
    TokenType,
)
from darglint.lex import (
    lex,
    condense,
)
from darglint.parse.cyk import (
    parse as cyk_parse,
)

from .utils import (
    random_tokens,
)

MAX_REPS = 10


class NewGoogleParserTests(TestCase):

    def test_top_parse_sections_le_nonnewline_tokens(self):
        r"""Make sure that aren't too many sections.

        We are attempting to guarantee that
            s <= t
        where
            s = the number of sections,
            t = |{ token_i \in string
                    | token_i /= newline
                    \/ ( token_i+1 /= newline
                        /\ token_i-1 /= newline )}|

        """
        for _ in range(MAX_REPS):
            tokens = random_tokens(exclude={TokenType.NEWLINE})
            doubles_amount = randint(0, 10)
            for _ in range(doubles_amount):
                i = randint(0, len(tokens) - 1)
                tokens.insert(
                    i,
                    Token(
                        value='\n',
                        token_type=TokenType.NEWLINE,
                        line_number=0,
                    ),
                )
                tokens.insert(
                    i,
                    Token(
                        value='\n',
                        token_type=TokenType.NEWLINE,
                        line_number=0,
                    ),
                )
            parsed = top_parse(tokens)
            self.assertTrue(
                len(parsed) <= len(tokens)
            )

    def test_expected_amount_of_sections(self):
        docstring = '\n'.join([
            'foobar',
            '',
            'Args:',
            '    foo: foobar',
            '',
            'Returns:',
            '    bar',
        ])
        tokens = condense(lex(docstring))
        sections = top_parse(tokens)
        self.assertEqual(
            len(sections),
            3,
        )

    def test_leading_newlines_stripped(self):
        docstring = '\n    boDqRvgBr # Returns'
        sections = top_parse(condense(lex(docstring)))
        self.assertTrue(sections[0][0].token_type != TokenType.NEWLINE)

    def test_top_parse_separates_by_indent_if_setion_starts(self):
        """Make sure we an ignore indentations if between sections."""
        docstring = '\n'.join([
            'A short summary.',
            '    ',
            'Args:',
            '    x: y.',
            '        ',
            'Returns:',
            '    Something.',
        ])
        parsed = top_parse(condense(lex(docstring)))
        self.assertEqual(len(parsed), 3)

    def test_top_parse_sections_do_not_start_with_newlines_and_nonempty(self):
        for _ in range(MAX_REPS):
            tokens = random_tokens()
            sections = top_parse(tokens)
            for section in sections:
                self.assertTrue(section)
                self.assertTrue(section[0].token_type != TokenType.NEWLINE)

    def has_double_newline(self, section):
        i = 0
        for token in section:
            if token.token_type == TokenType.NEWLINE:
                i += 1
            else:
                i = 0
            if i == 2:
                return True
        return False

    def test_no_double_newlines_after_top_parse(self):
        for _ in range(MAX_REPS):
            tokens = random_tokens()
            parsed = top_parse(tokens)
            for section in parsed:
                self.assertFalse(
                    self.has_double_newline(section),
                )

    def test_specific(self):
        tokens = [
            Token(
                token_type=TokenType.LPAREN,
                value='',
                line_number=0,
            ),
            Token(
                token_type=TokenType.ARGUMENTS,
                value='',
                line_number=0,
            ),
            Token(
                token_type=TokenType.NEWLINE,
                value='',
                line_number=0,
            ),
        ]
        grammar = lookup(tokens)[0]
        self.assertTrue(grammar is not None)
        parsed = cyk_parse(grammar, tokens)
        self.assertTrue(parsed is not None)

    def test_lookup_always_returns_something(self):
        for _ in range(MAX_REPS):
            tokens = random_tokens(exclude={TokenType.DOCTERM})
            node = parse(tokens)
            self.assertTrue(
                node is not None,
                'Unable to parse:\n"{}", {}'.format(
                    ' '.join([x.value for x in tokens]),
                    tokens,
                )
            )

    def test_lookup_tries_return_section_before_long_description(self):
        section = condense(lex('\n'.join([
            'Returns:',
            '    x: A number.',
        ])))
        grammars = lookup(section)
        node = None
        for grammar in grammars:
            node = cyk_parse(grammar, section)
            if node:
                break
        self.assertTrue(node)
        self.assertEqual(
            node.symbol,
            'returns-section',
            str(node),
        )

    def test_parse_args_section(self):
        tokens = condense(lex('\n'.join([
            'Args:',
            '    x: y',
        ])))
        node = parse(tokens)
        self.assertEqual(
            node.symbol,
            'arguments-section',
            str(node),
        )

    def test_parse_args_section_with_type(self):
        tokens = condense(lex('\n'.join([
            'Args:',
            '    x (X): y',
        ])))
        node = parse(tokens)
        self.assertEqual(
            node.symbol,
            'arguments-section',
        )

    def test_parse_yields_section(self):
        tokens = condense(lex('\n'.join([
            'Yields:',
            '    x',
        ])))
        node = parse(tokens)
        self.assertEqual(
            node.symbol,
            'yields-section',
            str(node),
        )

    def test_parse_yields_short_description_for_first_line_if_possible(self):
        tokens = condense(lex('\n'.join([
            'Short description.',
            '',
            'Long description.'
        ])))
        node = parse(tokens)
        self.assertTrue(
            node.contains('short-description')
        )
        self.assertTrue(
            node.contains('long-description')
        )
