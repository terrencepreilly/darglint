from unittest import TestCase

from parser_generator.generators import (
    Grammar,
    LLTableGenerator,
    SubProduction,
)
from .grammars import (
    TWO_LOOKAHEAD,
)


class GrammarTests(TestCase):

    def setUp(self):
        gen = LLTableGenerator(TWO_LOOKAHEAD)
        self.two_lookahead = Grammar(gen.table)

    def test_get_by_index(self):
        self.assertEqual(
            self.two_lookahead[0],
            SubProduction(['"TokenType.A"', 'S', 'A']),
        )

    def test_get_by_symbol(self):
        self.assertEqual(
            self.two_lookahead['S'],
            [
                SubProduction(['"TokenType.A"', 'S', 'A']),
                SubProduction(['ε']),
            ],
        )

    def test_get_exact_production_length_simple(self):
        self.assertEqual(
            list(self.two_lookahead.get_exact('S', 0)),
            [SubProduction([])],
        )

    def test_get_exact_production_length_doesnt_exist(self):
        self.assertEqual(
            list(self.two_lookahead.get_exact('S', 1)),
            [],
        )

    def test_get_exact_production_length_longer(self):
        self.assertEqual(
            list(self.two_lookahead.get_exact('S', 2)),
            [SubProduction(['"TokenType.A"', '"TokenType.C"'])],
        )

    def test_get_exact_production_length_terminals_are_one(self):
        # A grammar for words starting with "a" and having one or more "b"s.
        raw_grammar = '''
            start: <A>

            <A> ::= "a" <B>
            <B> ::= "b" <B>
                | "b"
        '''
        gen = LLTableGenerator(raw_grammar)
        grammar = Grammar(gen.table)
        self.assertEqual(
            list(grammar.get_exact('"a"', 1)),
            [SubProduction(['"a"'])],
        )
        self.assertEqual(
            list(grammar.get_exact('A', 2)),
            [SubProduction(['"a"', '"b"'])],
        )
        self.assertEqual(
            list(grammar.get_exact('A', 3)),
            [SubProduction(['"a"', '"b"', '"b"'])],
        )

    def test_get_exact_larger_number(self):
        got = list(self.two_lookahead.get_exact('S', 10))
        self.assertTrue(
            len(got) > 0,
        )
        self.assertTrue(
            all([len(x) == 10 for x in got])
        )

    def test_can_iterate_through_grammar(self):
        self.assertEqual(
            [x for x in self.two_lookahead],
            [
                ('S', SubProduction(['"TokenType.A"', 'S', 'A'])),
                ('S', SubProduction(['ε'])),
                ('A', SubProduction(['"TokenType.A"', '"TokenType.B"', 'S'])),
                ('A', SubProduction(['"TokenType.C"'])),
            ],
        )
