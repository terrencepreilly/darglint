from unittest import (
    TestCase,
)


from parser_generator.generators import (
    LLTableGenerator,
)
from .grammars import (
    TWO_LOOKAHEAD,
)
from .utils import (
    GrammarGenerator,
)


MAX_FUZZ_TEST = 50


class LLTableGeneratorTests(TestCase):

    def test_fuzz_first(self):
        """Make sure it doen't barf when generating the first set."""
        for _ in range(MAX_FUZZ_TEST):
            gen = GrammarGenerator()
            grammar = gen.to_grammar(gen.generate_ll1_grammar())
            table_gen = LLTableGenerator(grammar)
            table_gen.first()

    def test_fuzz_follow(self):
        """Make sure it dosen't barf when generating the follow set."""
        for _ in range(MAX_FUZZ_TEST):
            gen = GrammarGenerator()
            grammar = gen.to_grammar(gen.generate_ll1_grammar())
            table_gen = LLTableGenerator(grammar)
            first = table_gen.first()
            table_gen.follow(first)

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
        actual = gen.first()
        self.assertEqual(
            actual,
            expected,
            f'\n\nGot:\n{actual}\n\nExpected:\n{expected}',
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

    def test_first_with_lots_of_epsilons(self):
        grammar = r'''
            start: <S>

            <S> ::= <A> <B> <C> <D>
            <A> ::= "TokenType\.A" | ε
            <B> ::= "TokenType\.B" | ε
            <C> ::= "TokenType\.C" | ε
            <D> ::= "TokenType\.D"
        '''
        expected = {
            'S': {
                '"TokenType.A"',
                '"TokenType.B"',
                '"TokenType.C"',
                '"TokenType.D"',
            },
            'A': {'"TokenType.A"', 'ε'},
            'B': {'"TokenType.B"', 'ε'},
            'C': {'"TokenType.C"', 'ε'},
            'D': {'"TokenType.D"'},
        }
        gen = LLTableGenerator(grammar)
        actual = gen.first()
        self.assertEqual(
            actual,
            expected,
            f'\n\nGot:\n{actual}\n\nExpected:\n{expected}',
        )

    def test_follow_simple(self):
        grammar = r'''
            start: <S>

            <S> ::= <A> <B>
            <A> ::= "TokenType\.A"
            <B> ::= "TokenType\.B"

        '''
        gen = LLTableGenerator(grammar)
        first = gen.first()
        actual = gen.follow(first)
        expected = {
            'S': {'$'},
            'A': {'"TokenType.B"'},
            'B': {'$'},
        }
        self.assertEqual(
            actual,
            expected,
            f'\n\nGot:\n{actual}\n\nExpected:\n{expected}',
        )

    def test_follow_complex_example(self):
        grammar = r'''
            start: <E>

            <E> ::= <T> <E2>
            <E2> ::= "TokenType\.Plus" <T> <E2>
                | ε
            <T> ::= <F> <T2>
            <T2> ::= "TokenType\.Times" <F> <T2>
                | ε
            <F> ::= "TokenType\.LParen" <E> "TokenType\.RParen"
                | "TokenType\.Int"
        '''
        gen = LLTableGenerator(grammar)
        first = gen.first()
        actual = gen.follow(first)
        expected = {
            'E': {'$', '"TokenType.RParen"'},
            'E2': {'$', '"TokenType.RParen"'},
            'T': {'"TokenType.Plus"', '$', '"TokenType.RParen"'},
            'T2': {'"TokenType.Plus"', '$', '"TokenType.RParen"'},
            'F': {
                '"TokenType.Times"',
                '"TokenType.Plus"', '$',
                '"TokenType.RParen"'
            },
        }
        self.assertEqual(
            actual,
            expected,
            f'\n\nGot:\n{actual}\n\nExpected:\n{expected}',
        )

    def test_follow_many_epsilons(self):
        grammar = r'''
            start: <S>

            <S> ::= <A> <B> <C> <D>
            <A> ::= "A"
            <B> ::= "B"
                | ε
            <C> ::= "C"
                | ε
            <D> ::= "D"
                | ε
        '''
        gen = LLTableGenerator(grammar)
        first = gen.first()
        actual = gen.follow(first)
        expected = {
            'S': {'$'},
            'A': {'$', '"B"', '"C"', '"D"'},
            'B': {'$', '"C"', '"D"'},
            'C': {'$', '"D"'},
            'D': {'$'},
        }
        self.assertEqual(
            actual,
            expected,
            f'\n\nGot:\n{actual}\n\nExpected:\n{expected}',
        )

    def test_table_complex_example(self):
        grammar = r'''
            start: <E>

            <E> ::= <T> <E2>
            <E2> ::= "TokenType\.Plus" <T> <E2>
                | ε
            <T> ::= <F> <T2>
            <T2> ::= "TokenType\.Times" <F> <T2>
                | ε
            <F> ::= "TokenType\.LParen" <E> "TokenType\.RParen"
                | "TokenType\.Int"
        '''
        gen = LLTableGenerator(grammar)
        first = gen.first()
        follow = gen.follow(first)
        actual = gen.generate_table(first, follow)
        expected = {
            'E': {
                '"TokenType.LParen"': ('E', ['T', 'E2']),
                '"TokenType.Int"': ('E', ['T', 'E2']),
            },
            'E2': {
                '"TokenType.Plus"': ('E2', ['"TokenType.Plus"', 'T', 'E2']),
                '"TokenType.RParen"': ('E2', ['ε']),
                '$': ('E2', ['ε']),
            },
            'T': {
                '"TokenType.LParen"': ('T', ['F', 'T2']),
                '"TokenType.Int"': ('T', ['F', 'T2']),
            },
            'T2': {
                '"TokenType.Plus"': ('T2', ['ε']),
                '"TokenType.Times"': ('T2', ['"TokenType.Times"', 'F', 'T2']),
                '"TokenType.RParen"': ('T2', ['ε']),
                '$': ('T2', ['ε']),
            },
            'F': {
                '"TokenType.LParen"': (
                    'F', ['"TokenType.LParen"', 'E', '"TokenType.RParen"']
                ),
                '"TokenType.Int"': ('F', ['"TokenType.Int"']),
            },
        }
        # Loop through the keys and values to have an easier time
        # seeing where they differ.
        for key in expected:
            for key2 in expected[key]:
                self.assertEqual(
                    actual[key][key2],
                    expected[key][key2],
                    f'\n\nProduct at index <{key}, {key2}> was\n\n'
                    f'{actual[key][key2]}\n\n'
                    f'but expected\n\n'
                    f'{expected[key][key2]}\n\n'
                )
            self.assertEqual(
                len(expected[key].keys()),
                len(actual[key].keys())
            )
        self.assertEqual(
            len(expected.keys()),
            len(actual.keys())
        )

    def test_table_simple_example(self):
        grammar = r'''
            start: <S>

            <S> ::= <F>
            <S> ::= "LParen" <S> "Plus" <F> "RParen"
            <F> ::= "Int"
        '''
        gen = LLTableGenerator(grammar)
        first = gen.first()
        follow = gen.follow(first)
        actual = gen.generate_table(first, follow)
        expected = {
            'S': {
                '"LParen"': ('S', ['"LParen"', 'S', '"Plus"', 'F', '"RParen"']),
                '"Int"': ('S', ['F']),
            },
            'F': {
                '"Int"': ('F', ['"Int"']),
            },
        }
        self.assertEqual(
            actual,
            expected,
        )

    def test_first_with_two_lookahead(self):
        expected = {
            'S': {
                '"TokenType.A"',
                'ε',
                ('"TokenType.A"', '"TokenType.A"'),
                ('"TokenType.A"', '"TokenType.C"')
            },
            'A': {
                '"TokenType.A"',
                '"TokenType.C"',
                ('"TokenType.A"', '"TokenType.B"'),
            },
        }
        gen = LLTableGenerator(TWO_LOOKAHEAD, lookahead=2)
        actual = gen.kfirst(2)
        self.assertEqual(
            actual,
            expected,
        )
