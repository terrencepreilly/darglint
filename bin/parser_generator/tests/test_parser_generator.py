"""High level integration tests for the parser generator."""

from unittest import TestCase

from parser_generator.generators import generate_parser

from .grammars import (
    lex,
    TokenType,
    ONE_TOKEN_GRAMMAR,
    BINARY_GRAMMAR,
)


class ParserGeneratorTests(TestCase):

    def test_one_token_grammar(self):
        parser_repr = generate_parser(
            ONE_TOKEN_GRAMMAR,
            'from .grammars import (TokenType, Node)'
        )
        module = globals()
        exec(parser_repr, module)
        Parser = module['Parser']
        node = Parser(lex('1')).parse()
        self.assertEqual(
            node.node_type,
            'one',
        )
        self.assertEqual(
            node.value.value,
            '1',
        )

    def test_binary_grammar(self):
        parser_repr = generate_parser(
            BINARY_GRAMMAR,
            'from .grammars import (TokenType, Node)'
        )
        module = globals()
        exec(parser_repr, module)
        Parser = module['Parser']
        node = Parser(lex('0010101')).parse()
        self.assertEqual(
            node.node_type,
            'number',
        )
        self.assertEqual(
            node.value,
            None,
        )
        self.assertEqual(
            len(node.children),
            7,
        )
        self.assertEqual(
            node.children[-1].value.value,
            '1',
        )
