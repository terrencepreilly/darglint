"""Tests darglint's implementation of CYK."""

from collections import (
    deque,
)
from unittest import (
    TestCase,
)
import random

from darglint.parse.cyk import parse
from darglint.parse.grammar import (
    BaseGrammar,
)
from darglint.parse.grammar import Production as P
from darglint.token import (
    Token,
    BaseTokenType,
)


class KT(BaseTokenType):

    VERB = 0
    NOUN = 1

    UNKNOWN = -1


class SimpleKlingonGrammar(BaseGrammar):
    productions = [
        P('noun', (KT.NOUN, 0)),
        P('verb', (KT.VERB, 0)),
        P('sentence', ([], 'verb', 'noun', 0)),
    ]

    start = "sentence"


class KlingonGrammarTest(TestCase):

    def test_parse_simple_member(self):
        """Make sure that we can recognize a valid string in the language."""
        lexed = [
            Token(
                value="SuS",
                token_type=KT.VERB,
                line_number=0,
            ),
            Token(
                value="be'",
                token_type=KT.NOUN,
                line_number=0,
            ),
        ]
        self.assertTrue(parse(SimpleKlingonGrammar, lexed))

    def test_parse_simple_nonmember(self):
        """Make sure we reject invalid strings."""
        lexed = [
            Token(
                value="qet",
                token_type=KT.UNKNOWN,
                line_number=0,
            ),
            Token(
                value="be'",
                token_type=KT.NOUN,
                line_number=0,
            ),
        ]
        self.assertFalse(parse(SimpleKlingonGrammar, lexed))

    def test_parse_empty_is_never_part_of_grammar(self):
        """Make sure we don't crash with an empty list."""
        self.assertFalse(parse(SimpleKlingonGrammar, []))

    def test_parse_returns_parse_tree(self):
        """Make sure the parse returned a valid tree."""
        lexed = [
            Token(
                value="SuS",
                token_type=KT.VERB,
                line_number=0,
            ),
            Token(
                value="be'",
                token_type=KT.NOUN,
                line_number=1,
            ),
        ]
        node = parse(SimpleKlingonGrammar, lexed)
        self.assertTrue(node is not None)
        self.assertEqual(node.symbol, 'sentence')
        self.assertEqual(node.lchild.symbol, 'verb')
        self.assertEqual(node.lchild.value, lexed[0])
        self.assertEqual(node.rchild.symbol, 'noun')
        self.assertEqual(node.rchild.value, lexed[1])


class AKT(BaseTokenType):

    # Could be a noun or a negation.
    BE = 1

    VERB = 1
    NOUN = 2


class AmbiguousKlingonGrammar(BaseGrammar):

    productions = [
        P('verb', (AKT.VERB, 0), ([], 'verb', 'negation', 0)),
        P('negation', (AKT.BE, 0)),
        P('noun', (AKT.NOUN, 0), (AKT.BE, 0)),
        P('sentence', ([], 'verb', 'noun', 0)),
    ]

    start = 'sentence'


class AmbiguousKlingonGrammarTest(TestCase):

    def test_parses_ambiguous_grammars(self):
        """Make sure it can parse an ambigous grammar."""
        lexed_positive = [
            Token(
                value="Hegh",
                token_type=AKT.VERB,
                line_number=0,
            ),
            Token(
                value="be'",
                token_type=AKT.BE,
                line_number=0,
            ),
        ]
        self.assertTrue(parse(AmbiguousKlingonGrammar, lexed_positive))

        lexed_negative = [
            Token(
                value="Hegh",
                token_type=AKT.VERB,
                line_number=0,
            ),
            Token(
                value="be'",
                token_type=AKT.BE,
                line_number=0,
            ),
            Token(
                value="be'",
                token_type=AKT.BE,
                line_number=0,
            ),
        ]
        self.assertTrue(parse(AmbiguousKlingonGrammar, lexed_negative))


class EKG(BaseTokenType):

    NOUN = 0
    TRANSITIVE_VERB = 1
    INTRANSITIVE_VERB = 2


def ekg_lex(s):
    lookup = {
        'loD': EKG.NOUN,
        'qam': EKG.NOUN,
        'qet': EKG.INTRANSITIVE_VERB,
        'qIp': EKG.TRANSITIVE_VERB,
    }
    ret = []
    i = 0
    for line in s.split('\n'):
        for word in line.split():
            ret.append(
                Token(
                    value=word,
                    token_type=lookup[word],
                    line_number=i,
                )
            )
        i += 1
    return ret


class KlingonError(BaseException):
    pass


class ErrorKlingonGrammar(BaseGrammar):
    """Represents a grammar which can handle erroneous members."""

    productions = [
        P('sentence',
            ([], 'verb_phrase', 'noun', 0),
            ([], 'intransitive_verb', 'noun', 0)),
        P('verb_phrase', ([], 'noun', 'transitive_verb', 0)),
        P('verb_phrase', ([KlingonError], 'noun', 'intransitive_verb', 0)),
        P('noun', (EKG.NOUN, 0)),
        P('intransitive_verb', (EKG.INTRANSITIVE_VERB, 0)),
        P('transitive_verb', (EKG.TRANSITIVE_VERB, 0)),
    ]

    start = 'sentence'


class ErrorKlingonGrammarTest(TestCase):

    def has_annotation(self, node, guard=0):
        assert guard < 100, 'We have some sort of loop.'
        if node is None:
            return False
        if node.annotations:
            return True
        return (
            self.has_annotation(node.lchild, guard + 1)
            or self.has_annotation(node.rchild, guard + 1)
        )

    def _debug(self, node, indent=0):
        print(
            ' ' * indent
            + node.symbol
            + ', '.join([str(x) for x in node.annotations])
        )
        if node.lchild:
            self._debug(node.lchild, indent + 2)
        if node.rchild:
            self._debug(node.rchild, indent + 2)

    def test_valid_case(self):
        lexed = ekg_lex('qet loD')
        node = parse(ErrorKlingonGrammar, lexed)
        self.assertTrue(node is not None)
        self.assertEqual(node.symbol, 'sentence')
        self.assertEqual(node.lchild.symbol, 'intransitive_verb')
        self.assertEqual(node.rchild.symbol, 'noun')
        self.assertFalse(self.has_annotation(node))

    def test_invalid_case(self):
        lexed = ekg_lex('qam qet')
        node = parse(ErrorKlingonGrammar, lexed)
        self.assertTrue(node is None)

    def test_error_case(self):
        lexed = ekg_lex('qam qet loD')
        node = parse(ErrorKlingonGrammar, lexed)
        self.assertTrue(node is not None)
        self._debug(node)
        self.assertTrue(self.has_annotation(node))


class ST(BaseTokenType):

    ZERO = 0
    ONE = 1
    EPSILON = 2


class SmallGrammar(BaseGrammar):
    """Represents a very small grammar."""

    productions = [
        P('one', (ST.ONE, 0)),
        P('epsilon', (ST.EPSILON, 0)),
        P('zero', (ST.ZERO, 0)),
        P(
            'number',
            ([], 'one', 'epsilon', 0),
            ([], 'zero', 'epsilon', 0),
            ([], 'one', 'number', 0),
            ([], 'zero', 'number', 0),
        ),
    ]

    start = 'number'


class SimpleGrammarTest(TestCase):

    def test_parse_long_sentence_small_grammar(self):
        """Make sure we can handle a decently long string."""
        max_string_length = 50
        sentence = list()
        for _ in range(max_string_length):
            if random.random() < 0.5:
                sentence.append(Token(
                    value='0',
                    token_type=ST.ZERO,
                    line_number=0,
                ))
            else:
                sentence.append(Token(
                    value='1',
                    token_type=ST.ONE,
                    line_number=0,
                ))
        sentence.append(Token(
            value='ε',
            token_type=ST.EPSILON,
            line_number=0,
        ))
        self.assertTrue(parse(
            SmallGrammar,
            sentence
        ))


class ConfusionError(object):
    pass


class PN(BaseTokenType):
    r"""Tokens for the following grammar:

        Grammar: PhoneNumberGrammar

        start: <phone-number>

        <phone-number>
            ::= 40 <american-number>
            |   40 <french-number>
            |   20 <confusion-number>
        <american-number>
            ::= <number-group> <dash> <american-number>
            |   <number-group>
        <french-number>
            ::= <number-group> <dot> <french-number>
            |   <number-group>
        <confusion-number>
            ::= @ConfusionError <number-group> <dot> <confusion-number>
            |   @ConfusionError <number-group> <dash> <confusion-number>
            |   <number-group>

        <number-group>
            ::= <number> <number-group>
            |   <number>

        <number> ::= "PN\.NUMBER"
        <dash> ::= "PN\.DASH"
        <dot> ::= "PN\.DOT"

    """

    NUMBER = 0
    DASH = 1
    DOT = 2


def pn_lex(source):
    tokens = list()
    for letter in source:
        if letter.isspace():
            continue
        elif letter == '.':
            tokens.append(Token(
                token_type=PN.DOT,
                value='.',
                line_number=0,
            ))
        elif letter == '-':
            tokens.append(Token(
                token_type=PN.DASH,
                value='-',
                line_number=0,
            ))
        elif letter.isdigit:
            tokens.append(Token(
                token_type=PN.NUMBER,
                value=letter,
                line_number=0,
            ))
    return tokens


# Generated on 2019-07-07 13:31:04.922045
class PhoneNumberGrammar(BaseGrammar):
    productions = [
        P("phone-number",
            ([], "number-group", "american-number0", 40),
            ([], "number", "number-group", 40),
            (PN.NUMBER, 40),
            ([], "number-group", "french-number0", 40),
            ([ConfusionError], "number-group", "confusion-number1", 20),
            ([ConfusionError], "number-group", "confusion-number3", 20),
            ([], "number", "number-group", 20),
            (PN.NUMBER, 20)),
        P("american-number",
            ([], "number-group", "american-number0", 0),
            ([], "number", "number-group", 0),
            (PN.NUMBER, 0)),
        P("french-number",
            ([], "number-group", "french-number0", 0),
            ([], "number", "number-group", 0),
            (PN.NUMBER, 0)),
        P("confusion-number",
            ([ConfusionError], "number-group", "confusion-number1", 0),
            ([ConfusionError], "number-group", "confusion-number3", 0),
            ([], "number", "number-group", 0),
            (PN.NUMBER, 0)),
        P("number-group", ([], "number", "number-group", 0), (PN.NUMBER, 0)),
        P("number", (PN.NUMBER, 0)),
        P("dash", (PN.DASH, 0)),
        P("dot", (PN.DOT, 0)),
        P("american-number0", ([], "dash", "american-number", 0)),
        P("french-number0", ([], "dot", "french-number", 0)),
        P("confusion-number1", ([], "dot", "confusion-number", 0)),
        P("confusion-number3", ([], "dash", "confusion-number", 0)),
    ]
    start = "phone-number"


class PhoneNumberTests(TestCase):

    def contains_annotation(self, node, target):
        queue = deque([node])
        while queue:
            curr = queue.pop()
            if curr.annotations:
                for annotation in curr.annotations:
                    if issubclass(annotation, target):
                        return True
            if curr.lchild:
                queue.appendleft(curr.lchild)
            if curr.rchild:
                queue.appendleft(curr.rchild)
        return False

    def test_correct_number_prefered(self):
        for number in [
            '983-32',
            '38-328-288',
            '1-1-1-1',
            '3829279-32879',
        ]:
            tokens = pn_lex(number)
            node = parse(PhoneNumberGrammar, tokens)
            self.assertTrue(node, 'Unable to parse {}'.format(number))
            self.assertFalse(self.contains_annotation(node, ConfusionError))

    def test_backup_determined_by_weight(self):
        for number in [
            '983-32.1',
            '38.328-288',
            '1-1.1-1',
            '3829279-32879.1',
        ]:
            tokens = pn_lex(number)
            node = parse(PhoneNumberGrammar, tokens)
            self.assertTrue(node, 'Unable to parse {}'.format(number))
            self.assertTrue(self.contains_annotation(node, ConfusionError))


def verify_implementation():
    """Run many iterations and report the data for analysis.

    This test is intended to be run by hand in order to validate
    the runtime of the algorithm.  (If the runtime is roughly
    polynomial of degree 3, then it's probably correct.)

    One means of testing this is to apply a log_3 transform
    to the data, then perform a test of linearity. (A QQ plot
    would probably be sufficient.)  Of course, there may be
    some other, lower-order terms.

    """
    import csv
    import time

    times = dict()
    max_run_times = 200
    for n in range(1, max_run_times):
        sentence = ''
        for _ in range(n):
            sentence += random.choice('01')
        sentence += 'ε'
        start = time.time()
        parse(SmallGrammar, sentence)
        end = time.time()
        times[n] = end - start
        print(n)
    with open('cyk_run_times.csv', 'w') as fout:
        writer = csv.writer(fout)
        for n in range(1, max_run_times):
            writer.writerow([n, times[n]])
