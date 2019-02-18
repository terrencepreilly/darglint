"""Tests darglint's implementation of CYK."""

from unittest import (
    TestCase,
)
import random
from collections import OrderedDict

from darglint.parse.cyk import parse


class SimpleKlingonGrammar(object):
    productions = OrderedDict([
        ("verb", ["SuS"]),
        ("noun", ["be'"]),
        ("sentence", [("verb", "noun")]),
    ])

    start = "sentence"


class AmbiguousKlingonGrammar(object):

    productions = OrderedDict([
        ('verb', ['SuS', ('verb', 'negation')]),
        ('noun', ['be\'']),
        ('negation', ['be\'']),
        ('sentence', [('verb', 'noun')]),
    ])

    start = 'sentence'


class SmallGrammar(object):
    """Represents a very small grammar."""

    productions = OrderedDict([
        ('one', ['1']),
        ('epsilon', ['ε']),
        ('zero', ['0']),
        ('number', [
            ('one', 'epsilon'),
            ('zero', 'epsilon'),
            ('one', 'number'),
            ('zero', 'number'),
        ]),
    ])

    start = 'number'


class CykTest(TestCase):
    """Test the CYK parse implementation."""

    def test_parse_simple_member(self):
        """Make sure that we can recognize a valid string in the language."""
        self.assertTrue(parse(SimpleKlingonGrammar, ["SuS", "be'"]))

    def test_parse_simple_nonmember(self):
        """Make sure we reject invalid strings."""
        self.assertFalse(parse(SimpleKlingonGrammar, ["qet", "be'"]))

    def test_parse_empty_is_never_part_of_grammar(self):
        """Make sure we don't crash with an empty list."""
        self.assertFalse(parse(SimpleKlingonGrammar, []))

    def test_parse_long_sentence_small_grammar(self):
        """Make sure we can handle a decently long string."""
        max_string_length = 50
        sentence = ''
        for _ in range(max_string_length):
            sentence += random.choice('01')
        sentence += 'ε'
        self.assertTrue(parse(
            SmallGrammar,
            sentence
        ))

    def test_parse_returns_parse_tree(self):
        """Make sure the parse returned a valid tree."""
        node = parse(SimpleKlingonGrammar, ["SuS", "be'"])
        self.assertTrue(node is not None)
        self.assertEqual(node.symbol, 'sentence')
        self.assertEqual(node.lchild.symbol, 'verb')
        self.assertEqual(node.lchild.value, 'SuS')
        self.assertEqual(node.rchild.symbol, 'noun')
        self.assertEqual(node.rchild.value, 'be\'')

    def test_parses_ambiguous_grammars(self):
        """Make sure it can parse an ambigous grammar."""
        positive = parse(AmbiguousKlingonGrammar, ["SuS", "be'"])
        self.assertTrue(positive is not None)
        negated = parse(AmbiguousKlingonGrammar, ["SuS", "be'", "be'"])
        self.assertTrue(negated is not None)


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
