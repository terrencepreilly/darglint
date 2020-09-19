from unittest import TestCase

from parser_generator.generators import (
    LLTableGenerator,
)


class LLTableGeneratorTests(TestCase):

    def test_table(self):
        grammar = r'''
            start: <S>

            <S> ::= <E>
            <E> ::= <T> <Plus> <E>
                | <T> <Minus> <E>
            <T> ::= "TokenType\.Int"
                | <LP> <E> <RP>
            <Plus> ::= "TokenType\.Plus"
            <Minus> ::= "TokenType\.Minus"
            <LP> ::= "TokenType\.LeftParen"
            <RP> ::= "TokenType\.RightParen"
        '''
        gen = LLTableGenerator(grammar)
        expected = [
            ('S', ['E']),
            ('E', ['T', 'Plus', 'E']),
            ('E', ['T', 'Minus', 'E']),
            ('T', ['"TokenType.Int"']),
            ('T', ['LP', 'E', 'RP']),
            ('Plus', ['"TokenType.Plus"']),
            ('Minus', ['"TokenType.Minus"']),
            ('LP', ['"TokenType.LeftParen"']),
            ('RP', ['"TokenType.RightParen"']),
        ]
        self.assertEqual(
            expected,
            gen.table,
        )

    def test_first_one_terminal(self):
        grammar = r'''
            start: <S>

            <S> ::= "TokenType\.A"
        '''
        expected = {
            'S': {'"TokenType.A"'},
        }
        gen = LLTableGenerator(grammar)
        self.assertEqual(
            gen.first(),
            expected,
        )

    def test_first_infer_from_nonterminal(self):
        grammar = r'''
            start: <S>

            <S> ::= <A> | <B>
            <A> ::= "TokenType\.A"
            <B> ::= "TokenType\.B"
        '''
        expected = {
            'S': {'"TokenType.A"', '"TokenType.B"'},
            'A': {'"TokenType.A"'},
            'B': {'"TokenType.B"'},
        }
        gen = LLTableGenerator(grammar)
        self.assertEqual(
            gen.first(),
            expected,
        )

    def test_first_infer_with_epsilon(self):
        grammar = r'''
            start: <S>

            <S> ::= <A> <B>
            <A> ::= <C> | ε
            <B> ::= "TokenType\.B"
            <C> ::= "TokenType\.C"
        '''
        expected = {
            'S': {'"TokenType.C"', '"TokenType.B"'},
            'A': {'"TokenType.C"', 'ε'},
            'B': {'"TokenType.B"'},
            'C': {'"TokenType.C"'},
        }
        gen = LLTableGenerator(grammar)
        actual = gen.first()
        self.assertEqual(
            actual,
            expected,
            f'\n\nGot:\n{actual}\n\nExpected:\n{expected}',
        )
