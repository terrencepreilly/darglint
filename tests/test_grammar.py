"""Tests for the Grammar class."""

from unittest import TestCase

from darglint.parse.grammar import BaseGrammar


class GrammarTest(TestCase):
    """Tests for the grammar class.

    Since most of the structure/logic of the docstring is going
    to be moved to data, it makes sense to represent this with
    a flexible data structure.

    """

    def test_grammar_must_have_productions_and_start(self):
        class BadGrammar(BaseGrammar):
            pass

        with self.assertRaises(Exception):
            BadGrammar()

    def test_only_productions_and_start_necessary(self):
        class GoodGrammar(BaseGrammar):
            productions = []
            start = ''

        GoodGrammar()
