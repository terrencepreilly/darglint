from unittest import TestCase
from darglint.token import TokenType
from darglint.lex import (
    condense,
    lex,
)


class LexTestCase(TestCase):

    def test_lex_empty_string_returns_no_tokens(self):
        tokens = list(lex(''))
        self.assertEqual(len(tokens), 0)

    def test_lex_yields_indent_for_four_spaces(self):
        tokens = list(lex(' ' * 8))
        self.assertEqual(len(tokens), 2)
        self.assertTrue(all(x.token_type == TokenType.INDENT
            for x in tokens))

    def test_lex_yields_newlines_for_newlines(self):
        tokens = list(lex('\n'))
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].token_type, TokenType.NEWLINE)

    def test_lex_yields_colons(self):
        tokens = list(lex(':'))
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].token_type, TokenType.COLON)

    def test_lex_skips_separators(self):
        tokens = list(lex('\t'))
        self.assertEqual(len(tokens), 0)

    def test_all_other_characters_are_word_characters(self):
        tokens = list(lex('asnotehu&*$!@$`'))
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].token_type, TokenType.WORD)

    def test_tokens_contain_strings_as_values(self):
        string = 'OESNUTHtoahsintoehaEOSUTNH342'
        tokens = list(lex(string))
        token = tokens[0]
        self.assertEqual(token.value, string)

    def test_oneline_docstring(self):
        docstring = '"""A simple explanation using `variable`."""'
        tokens = list(lex(docstring))
        self.assertEqual(len(tokens), 5)
        for token in tokens:
            self.assertEqual(token.token_type, TokenType.WORD)

    def test_hash(self):
        tokens = list(lex('#'))
        token = tokens[0]
        self.assertEqual(token.value, '#')
        self.assertEqual(token.token_type, TokenType.HASH)

    def test_extended_docstring(self):
        docstring = '\n'.join([
            '"""The oneline description.',
            '    ',
            '    The more detailed description, which can be composed',
            '    of multiple lines.',
            '"""',
        ])
        tokens = list(lex(docstring))
        self.assertEqual(tokens[3].token_type, TokenType.NEWLINE)
        self.assertEqual(tokens[4].token_type, TokenType.INDENT)

    def test_args(self):
        docstring = '\n'.join([
            '"""Add two numbers together.',
            '    ',
            '    Args:',
            '        a: The first number.',
            '        b: The second number.',
            '    Returns: The sum of the two numbers.',
            '',
            '    """',
        ])
        tokens = list(lex(docstring))
        self.assertEqual(tokens[8].token_type, TokenType.WORD)
        self.assertEqual(tokens[9].token_type, TokenType.COLON)
        self.assertEqual(tokens[10].token_type, TokenType.NEWLINE)
        self.assertEqual(tokens[11].token_type, TokenType.INDENT)

    def test_parenthesis_in_types(self):
        """Make sure paretheses are their own token."""
        string = '())('
        tokens = list(lex(string))
        token_types = [x.token_type for x in tokens]
        self.assertEqual(
            token_types,
            [
                TokenType.LPAREN,
                TokenType.RPAREN,
                TokenType.RPAREN,
                TokenType.LPAREN,
            ]
        )

    def test_parse_parenthesis_in_word(self):
        """Make sure parentheses are separators."""
        string = 'a('
        tokens = list(lex(string))
        self.assertEqual(
            [x.token_type for x in tokens],
            [TokenType.WORD, TokenType.LPAREN]
        )


class CondenseTests(TestCase):

    def test_dissimilar_types_passes_directly(self):
        tokens = list(lex('This ( something : )'))
        condensed = condense((x for x in tokens))
        self.assertEqual(
            tokens,
            condensed,
        )

    def test_words_get_concatenated(self):
        tokens = lex('word' + '   word' * 4)
        condensed = condense(tokens)
        self.assertEqual(
            len(condensed),
            1,
        )

    def test_condensed_words_single_spaced(self):
        tokens = lex('word' + '   word' * 4)
        condensed = condense(tokens)
        self.assertEqual(
            condensed[0].value,
            'word' + ' word' * 4,
        )

    def test_returns_are_assigned(self):
        tokens = lex('something something Returns something something')
        condensed = condense(tokens)
        self.assertEqual(
            [x.token_type for x in condensed],
            [TokenType.WORD, TokenType.RETURNS, TokenType.WORD]
        )
