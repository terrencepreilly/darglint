"""High level integration tests for the parser generator."""

from unittest import TestCase
from collections import deque

from parser_generator.generators import generate_parser

from .grammars import (
    lex,
    TokenType,
    ONE_TOKEN_GRAMMAR,
    BINARY_GRAMMAR,
)


class ParserGeneratorTests(TestCase):

    def assertTerminals(self, node, *terminals):
        """Assert the node's terminal values in an In-Order Traversal.

        Args:
            node: The root of the tree we're checking.
            terminals: The terminal values we expect to encounter during
                an in-order traversal of the tree.
        """
        stack = deque([node])
        terminals_remaining = deque(terminals)
        while stack:
            curr = stack.pop()
            if isinstance(curr.node_type, TokenType):
                terminal = terminals_remaining.popleft()
                self.assertEqual(
                    terminal,
                    curr.value.value,
                )
            stack.extend(curr.children[::-1])


    def test_one_token_grammar(self):
        parser_repr = generate_parser(
            ONE_TOKEN_GRAMMAR,
            'from .grammars import (Token, TokenType, Node)'
        )
        module = globals()
        exec(parser_repr, module)
        Parser = module['Parser']
        node = Parser(lex('1')).parse()
        self.assertEqual(
            node.node_type,
            'one',
        )
        self.assertTerminals(
            node,
            '1',
        )

    def test_binary_grammar(self):
        parser_repr = generate_parser(
            BINARY_GRAMMAR,
            'from .grammars import (Token, TokenType, Node)'
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
        self.assertTerminals(
            node,
            *'0010101'
        )
