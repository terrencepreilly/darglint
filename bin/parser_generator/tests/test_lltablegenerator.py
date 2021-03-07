from unittest import (
    TestCase,
    skip,
)


from parser_generator.generators import (
    LLTableGenerator,
    Grammar,
)
from .grammars import (
    TWO_LOOKAHEAD,
    BINARY_GRAMMAR,
)
from .utils import (
    GrammarGenerator,
    FollowSetGenerator,
)


MAX_FUZZ_TEST = 50


class FollowFuzz(TestCase):
    def _followtest(self, instance=0):
        known_followsets = list()
        while not known_followsets:
            productions = GrammarGenerator().generate_ll1_grammar()
            start, productions = productions[0], productions[1:]
            grammar = Grammar(productions, start[1][0])

            # We don't want infinite left recursion.
            if grammar.has_infinite_left_recursion():
                continue

            fsg = FollowSetGenerator(grammar, start[1][0], 2)
            known_followsets = list(fsg)
        known_lookup = dict()
        for key, values in known_followsets:
            if key not in known_lookup:
                known_lookup[key] = set()
            known_lookup[key].add(tuple(values))
        gen = LLTableGenerator(str(grammar))
        actual = gen.kfollow(2)
        for key in known_lookup:
            if key not in actual:
                self.fail(
                    f"Known lookup contains {key}, which is not in actual.\n\n"
                    f"{grammar}"
                )
            message = (
                f"{instance} For the following grammar:\n\n"
                f"{grammar}\n\nMissing from followset for {key}: {{}}"
            )
            self.assertEqual(
                len(known_lookup[key] - actual[key]),
                0,
                message.format(known_lookup[key] - actual[key]),
            )

    def test_follows(self):
        for i in range(MAX_FUZZ_TEST):
            self._followtest()


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
            productions = gen.generate_ll1_grammar()
            start, productions = productions[0], productions[1:]
            grammar = Grammar(productions, start[1][0])
            while grammar.has_infinite_left_recursion():
                productions = gen.generate_ll1_grammar()
                start, productions = productions[0], productions[1:]
                grammar = Grammar(productions, start[1][0])
            table_gen = LLTableGenerator(str(grammar))
            first = table_gen.first()
            table_gen.follow(first)

    def test_table(self):
        grammar = r"""
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
        """
        gen = LLTableGenerator(grammar)
        expected = [
            ("S", ["E"]),
            ("E", ["T", "Plus", "E"]),
            ("E", ["T", "Minus", "E"]),
            ("T", ['"TokenType.Int"']),
            ("T", ["LP", "E", "RP"]),
            ("Plus", ['"TokenType.Plus"']),
            ("Minus", ['"TokenType.Minus"']),
            ("LP", ['"TokenType.LeftParen"']),
            ("RP", ['"TokenType.RightParen"']),
        ]
        self.assertEqual(
            expected,
            gen.table,
        )

    def test_first_one_terminal(self):
        grammar = r"""
            start: <S>

            <S> ::= "TokenType\.A"
        """
        expected = {
            "S": {'"TokenType.A"'},
        }
        gen = LLTableGenerator(grammar)
        self.assertEqual(
            gen.first(),
            expected,
        )

    def test_first_infer_from_nonterminal(self):
        grammar = r"""
            start: <S>

            <S> ::= <A> | <B>
            <A> ::= "TokenType\.A"
            <B> ::= "TokenType\.B"
        """
        expected = {
            "S": {'"TokenType.A"', '"TokenType.B"'},
            "A": {'"TokenType.A"'},
            "B": {'"TokenType.B"'},
        }
        gen = LLTableGenerator(grammar)
        actual = gen.first()
        self.assertEqual(
            actual,
            expected,
            f"\n\nGot:\n{actual}\n\nExpected:\n{expected}",
        )

    def test_first_infer_with_epsilon(self):
        grammar = r"""
            start: <S>

            <S> ::= <A> <B>
            <A> ::= <C> | ε
            <B> ::= "TokenType\.B"
            <C> ::= "TokenType\.C"
        """
        expected = {
            "S": {'"TokenType.C"', '"TokenType.B"', "ε"},
            "A": {'"TokenType.C"', "ε"},
            "B": {'"TokenType.B"'},
            "C": {'"TokenType.C"'},
        }
        gen = LLTableGenerator(grammar)
        actual = gen.first()
        self.assertEqual(
            actual,
            expected,
            f"\n\nGot:\n{actual}\n\nExpected:\n{expected}",
        )

    def test_first_with_lots_of_epsilons(self):
        grammar = r"""
            start: <S>

            <S> ::= <A> <B> <C> <D>
            <A> ::= "TokenType\.A" | ε
            <B> ::= "TokenType\.B" | ε
            <C> ::= "TokenType\.C" | ε
            <D> ::= "TokenType\.D"
        """
        expected = {
            "S": {
                '"TokenType.A"',
                '"TokenType.B"',
                '"TokenType.C"',
                '"TokenType.D"',
                "ε",
            },
            "A": {'"TokenType.A"', "ε"},
            "B": {'"TokenType.B"', "ε"},
            "C": {'"TokenType.C"', "ε"},
            "D": {'"TokenType.D"'},
        }
        gen = LLTableGenerator(grammar)
        actual = gen.first()
        self.assertEqual(
            actual,
            expected,
            f"\n\nGot:\n{actual}\n\nExpected:\n{expected}",
        )

    def test_follow_simple(self):
        grammar = r"""
            start: <S>

            <S> ::= <A> <B>
            <A> ::= "TokenType\.A"
            <B> ::= "TokenType\.B"

        """
        gen = LLTableGenerator(grammar)
        first = gen.first()
        actual = gen.follow(first)
        expected = {
            "S": {"$"},
            "A": {'"TokenType.B"'},
            "B": {"$"},
        }
        self.assertEqual(
            actual,
            expected,
            f"\n\nGot:\n{actual}\n\nExpected:\n{expected}",
        )

    def test_follow_binary(self):
        gen = LLTableGenerator(BINARY_GRAMMAR)
        first = gen.first()
        actual = gen.follow(first)
        expected = {
            "number": {"$"},
            "one": {'"TokenType.ONE"', '"TokenType.ZERO"', "$"},
            "zero": {'"TokenType.ONE"', '"TokenType.ZERO"', "$"},
        }
        self.assertEqual(
            actual,
            expected,
            f"\n\nGot:\n{actual}\n\nExpected:\n{expected}",
        )

    def test_follow_complex_example(self):
        grammar = r"""
            start: <E>

            <E> ::= <T> <E2>
            <E2> ::= "TokenType\.Plus" <T> <E2>
                | ε
            <T> ::= <F> <T2>
            <T2> ::= "TokenType\.Times" <F> <T2>
                | ε
            <F> ::= "TokenType\.LParen" <E> "TokenType\.RParen"
                | "TokenType\.Int"
        """
        gen = LLTableGenerator(grammar)
        first = gen.first()
        actual = gen.follow(first)
        expected = {
            "E": {"$", '"TokenType.RParen"'},
            "E2": {"$", '"TokenType.RParen"'},
            "T": {'"TokenType.Plus"', "$", '"TokenType.RParen"'},
            "T2": {'"TokenType.Plus"', "$", '"TokenType.RParen"'},
            "F": {
                '"TokenType.Times"',
                '"TokenType.Plus"',
                "$",
                '"TokenType.RParen"',
            },
        }
        extra = {
            key: (value - expected[key] if key in expected else value)
            for key, value in actual.items()
        }
        missing = {
            key: (value - actual[key] if key in actual else value)
            for key, value in expected.items()
        }
        self.assertEqual(
            actual,
            expected,
            f"\n\nGot extra:\n{extra}\n\nMissing:\n{missing}\n\n"
            f"Got:\n{actual}\n\nExpected:\n{expected}",
        )

    def test_follow_many_epsilons(self):
        grammar = r"""
            start: <S>

            <S> ::= <A> <B> <C> <D>
            <A> ::= "A"
            <B> ::= "B"
                | ε
            <C> ::= "C"
                | ε
            <D> ::= "D"
                | ε
        """
        gen = LLTableGenerator(grammar)
        first = gen.first()
        actual = gen.follow(first)
        expected = {
            "S": {"$"},
            "A": {"$", '"B"', '"C"', '"D"'},
            "B": {"$", '"C"', '"D"'},
            "C": {"$", '"D"'},
            "D": {"$"},
        }
        self.assertEqual(
            actual,
            expected,
            f"\n\nGot:\n{actual}\n\nExpected:\n{expected}",
        )

    def test_table_binary(self):
        gen = LLTableGenerator(BINARY_GRAMMAR)
        first = gen.first()
        follow = gen.follow(first)
        actual = gen.generate_table(first, follow)
        expected = {
            'number': {
                '"TokenType.ZERO"': (
                    'number',
                    ['zero', 'number'],
                ),
                '"TokenType.ONE"': (
                    'number',
                    ['one', 'number'],
                ),
                '$': (
                    'number',
                    ['ε'],
                ),
            },
            'one': {
                '"TokenType.ONE"': (
                    'one',
                    ['"TokenType.ONE"'],
                ),
            },
            'zero': {
                '"TokenType.ZERO"': (
                    'zero',
                    ['"TokenType.ZERO"'],
                ),
            }
        }
        self.assertEqual(actual, expected)

    def test_table_complex_example(self):
        grammar = r"""
            start: <E>

            <E> ::= <T> <E2>
            <E2> ::= "TokenType\.Plus" <T> <E2>
                | ε
            <T> ::= <F> <T2>
            <T2> ::= "TokenType\.Times" <F> <T2>
                | ε
            <F> ::= "TokenType\.LParen" <E> "TokenType\.RParen"
                | "TokenType\.Int"
        """
        gen = LLTableGenerator(grammar)
        first = gen.first()
        follow = gen.follow(first)
        actual = gen.generate_table(first, follow)
        expected = {
            "E": {
                '"TokenType.LParen"': ("E", ["T", "E2"]),
                '"TokenType.Int"': ("E", ["T", "E2"]),
            },
            "E2": {
                '"TokenType.Plus"': ("E2", ['"TokenType.Plus"', "T", "E2"]),
                '"TokenType.RParen"': ("E2", ["ε"]),
                "$": ("E2", ["ε"]),
            },
            "T": {
                '"TokenType.LParen"': ("T", ["F", "T2"]),
                '"TokenType.Int"': ("T", ["F", "T2"]),
            },
            "T2": {
                '"TokenType.Plus"': ("T2", ["ε"]),
                '"TokenType.Times"': ("T2", ['"TokenType.Times"', "F", "T2"]),
                '"TokenType.RParen"': ("T2", ["ε"]),
                "$": ("T2", ["ε"]),
            },
            "F": {
                '"TokenType.LParen"': (
                    "F",
                    ['"TokenType.LParen"', "E", '"TokenType.RParen"'],
                ),
                '"TokenType.Int"': ("F", ['"TokenType.Int"']),
            },
        }
        # Loop through the keys and values to have an easier time
        # seeing where they differ.
        for key in expected:
            for key2 in expected[key]:
                self.assertEqual(
                    actual[key][key2],
                    expected[key][key2],
                    f"\n\nProduct at index <{key}, {key2}> was\n\n"
                    f"{actual[key][key2]}\n\n"
                    f"but expected\n\n"
                    f"{expected[key][key2]}\n\n",
                )
            self.assertEqual(
                len(expected[key].keys()), len(actual[key].keys()))
        self.assertEqual(len(expected.keys()), len(actual.keys()))

    def test_table_simple_example(self):
        grammar = r"""
            start: <S>

            <S> ::= <F>
            <S> ::= "LParen" <S> "Plus" <F> "RParen"
            <F> ::= "Int"
        """
        gen = LLTableGenerator(grammar)
        first = gen.first()
        follow = gen.follow(first)
        actual = gen.generate_table(first, follow)
        expected = {
            "S": {
                '"LParen"': ("S", ['"LParen"', "S", '"Plus"', "F", '"RParen"']),
                '"Int"': ("S", ["F"]),
            },
            "F": {
                '"Int"': ("F", ['"Int"']),
            },
        }
        self.assertEqual(
            actual,
            expected,
        )

    def test_first_with_two_lookahead(self):
        expected = {
            "S": {
                '"TokenType.A"',
                "ε",
                ('"TokenType.A"', '"TokenType.A"'),
                ('"TokenType.A"', '"TokenType.C"'),
            },
            "A": {
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

    def test_first_with_three_lookahead(self):
        grammar = r"""
            start: <S>

            <S> ::= <A>
              | <B>
            <A> ::= "a" "a" "a"
            <B> ::= "a" "a" "b"
        """
        expected = {
            "S": {
                ('"a"', '"a"', '"a"'),
                ('"a"', '"a"', '"b"'),
                ('"a"', '"a"'),
                '"a"',
            },
            "A": {
                ('"a"', '"a"', '"a"'),
                ('"a"', '"a"'),
                '"a"',
            },
            "B": {
                ('"a"', '"a"', '"b"'),
                ('"a"', '"a"'),
                '"a"',
            },
        }
        gen = LLTableGenerator(grammar, lookahead=3)
        actual = gen.kfirst(3)
        self.assertEqual(actual, expected)

    def test_first_with_two_lookahead_no_partials(self):
        """Make sure we don't get fragments mixed in.

        If we have a subproduction, S, of the form

            <E, s_0, s_1, ..., s_n>

        And we want kfirst(S, k), where k > 1,
        we have to make sure that when iterating through possible
        kfirst sets of E, that we only take "complete" sets.  For example,
        if we have k = 2 and

            E -> "(" Value ")"

        Then the value of `kfirst(S, 2) = kfirst(E, 2)`.  The value
        `kfirst(E, 1) x kfirst(<s_0, S_1, ...,s_n>, 1)` would not be
        valid.

        """
        grammar = r"""
            start: <S>

            <S> ::= <E> <M>
                | <M>
            <E> ::= "a" "b" "a"
            <M> ::= "c"
        """
        expected = {
            "S": {
                ('"a"', '"b"'),
                # However, the value ('"a"', '"c"') should not appear.
                '"a"',
                '"c"',
            },
            "E": {
                ('"a"', '"b"'),
                '"a"',
            },
            "M": {'"c"'},
        }
        gen = LLTableGenerator(grammar, lookahead=2)
        actual = gen.kfirst(2)
        self.assertEqual(
            actual, expected, f"\n\nGot:\n{actual}\n\nExpected:\n{expected}"
        )

    def test_first_with_three_lookahead_no_partials_deep_tree(self):
        grammar = r"""
        start: <S>

        <S> ::= <A> <M>
        <A> ::= "a" <B>
        <B> ::= "b" <C>
        <C> ::= "c"
        <M> ::= "m"
        """
        expected = {
            "S": {
                '"a"',
                ('"a"', '"b"'),
                ('"a"', '"b"', '"c"'),
            },
            "A": {
                '"a"',
                ('"a"', '"b"'),
                ('"a"', '"b"', '"c"'),
            },
            "B": {
                '"b"',
                ('"b"', '"c"'),
            },
            "C": {
                '"c"',
            },
            "M": {
                '"m"',
            },
        }
        gen = LLTableGenerator(grammar, lookahead=3)
        actual = gen.kfirst(3)
        self.assertEqual(
            actual, expected, f"\n\nGot:\n{actual}\n\nExpected:\n{expected}"
        )

    def test_kfollow_with_two_lookahead(self):
        gen = LLTableGenerator(TWO_LOOKAHEAD)
        actual = gen.kfollow(2)
        expected = {
            "S": {
                "$",
                '"TokenType.A"',
                '"TokenType.C"',
                ('"TokenType.A"', '"TokenType.B"'),
                ('"TokenType.C"', '"TokenType.C"'),
                ('"TokenType.C"', '"TokenType.A"'),
                ('"TokenType.C"', "$"),
            },
            "A": {
                "$",
                '"TokenType.A"',
                '"TokenType.C"',
                ('"TokenType.A"', '"TokenType.B"'),
                ('"TokenType.C"', '"TokenType.C"'),
                ('"TokenType.C"', '"TokenType.A"'),
                ('"TokenType.C"', "$"),
            },
        }
        extra = {
            key: value - expected[key]
            for key, value in actual.items()
            if key in expected
        }
        missing = {
            key: expected[key] - value
            for key, value in actual.items()
            if key in expected
        }
        self.assertEqual(
            actual,
            expected,
            f"\n\nGot extra:\n{extra}\n\nMissing:\n{missing}\n\n"
            f"Got:\n{actual}\n\nExpected:\n{expected}",
        )

    def test_table_with_two_lookahead(self):
        expected = {
            'S': {
                '$': (
                    'S', ['ε']
                ),
                '"TokenType.A"': (
                    'S',
                    [
                        '"TokenType.A"',
                        'S',
                        'A',
                    ]
                ),
                ('"TokenType.A"', '"TokenType.A"'): (
                    'S',
                    [
                        '"TokenType.A"',
                        'S',
                        'A',
                    ]
                ),
                ('"TokenType.A"', '"TokenType.B"'): (
                    'S', ['ε']
                ),
                ('"TokenType.A"', '"TokenType.C"'): (
                    'S',
                    [
                        '"TokenType.A"',
                        'S',
                        'A',
                    ]
                ),
                '"TokenType.C"': (
                    'S', ['ε']
                ),
                ('"TokenType.C"', "$"): (
                    'S', ['ε']
                ),
                ('"TokenType.C"', '"TokenType.A"'): (
                    'S', ['ε']
                ),
                ('"TokenType.C"', '"TokenType.C"'): (
                    'S', ['ε']
                ),
            },
            'A': {
                '"TokenType.A"': (
                    'A', ['"TokenType.A"', '"TokenType.B"', 'S']
                ),
                '"TokenType.C"': (
                    'A', ['"TokenType.C"']
                ),
                ('"TokenType.A"', '"TokenType.B"'): (
                    'A', ['"TokenType.A"', '"TokenType.B"', 'S']
                ),
            },
        }
        gen = LLTableGenerator(TWO_LOOKAHEAD)
        first = gen.kfirst(2)
        follow = gen.kfollow(2)
        actual = gen.generate_ktable(first, follow, 2)
        # Loop through the keys and values to have an easier time
        # seeing where they differ.
        for key in expected:
            for key2 in expected[key]:
                self.assertEqual(
                    actual[key][key2],
                    expected[key][key2],
                    f"\n\nProduct at index <{key}, {key2}> was\n\n"
                    f"{actual[key][key2]}\n\n"
                    f"but expected\n\n"
                    f"{expected[key][key2]}\n\n",
                )
            missing = set(expected[key].keys()) - set(actual[key].keys())
            self.assertEqual(
                len(missing),
                0,
                f'Missing expected keys {key}: {missing}'
            )
            extra = set(actual[key].keys()) - set(expected[key].keys())
            self.assertEqual(
                len(extra),
                0,
                f'Extra keys at {key}: {extra}'
            )
        missing = set(expected.keys()) - set(actual.keys())
        self.assertEqual(len(missing), 0, f'Missing expected keys {missing}')
        extra = set(actual.keys()) - set(expected.keys())
        self.assertEqual(len(extra), 0, f'Extra keys {extra}')

    def test_table_single_forward_to_epsilon(self):
        grammar = '''
            Grammar: ShortDescriptionGrammar

            start: <short-description>

            <short-description> ::= <line>

            <line> ::= <word> <line>
              | ε

            <word> ::= "buffalo" | "Buffalo"
        '''
        gen = LLTableGenerator(grammar)
        first = gen.first()
        follow = gen.follow(first)

        # This was previously failing because it couldn't look up
        # the production `L -> ε`
        gen.generate_table(first, follow)
