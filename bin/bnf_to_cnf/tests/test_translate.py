from unittest import (
    TestCase,
)

from bnf_to_cnf.translator import (
    Translator,
)
from bnf_to_cnf.parser import (
    Parser,
)


class TranslatorTestCase(TestCase):

    def test_already_cnf_doesnt_change(self):
        """Make sure that it doesn't alter already cnf grammars."""
        examples = [
            '<args> ::= "Args"',
            '<colon> ::= ":"',
            '\n'.join([
                '<one> ::= "1"',
                '<zero> ::= "0"'
            ]),
        ]
        for example in examples:
            tree = Parser().parse(example)
            translated = Translator().translate(tree)
            self.assertEqual(
                str(translated),
                example,
            )

    def test_start_symbol_reassigned(self):
        """Make sure that the start symbol is reassigned, if present."""
        tree = Parser().parse('<section> ::= <head> <start>')
        node = Translator().translate(tree)
        self.assertEqual(
            str(node),
            '\n'.join([
                '<start> ::= <start0>',
                '<section> ::= <head> <start0>',
            ])
        )

    def test_nonsolitary_terminals(self):
        """Make sure non-solitary terminals are factored out."""
        tree = Parser().parse('<arg-header> ::= <arg> ":"')
        node = Translator().translate(tree)
        self.assertEqual(
            str(node),
            '\n'.join([
                '<arg-header> ::= <arg> <C>',
                '<C> ::= ":"',
            ]),
        )

    def test_nonsolitary_terminals_symbol_taken(self):
        """Make sure non-solitary teminals will have unique name."""
        tree = Parser().parse(
            '<arg-header> ::= <arg> ":"\n'
            '<C> ::= "Another_value"'
        )
        node = Translator().translate(tree)
        self.assertEqual(
            str(node),
            '<arg-header> ::= <arg> <C0>\n'
            '<C> ::= "Another_value"\n'
            '<C0> ::= ":"'
        )

    def test_factor_3plus_RHSs(self):
        """Make sure we refactor RHSs with more than two symbols."""
        tree = Parser().parse(
            '<a> ::= <b> <c> <d>'
        )
        node = Translator().translate(tree)
        self.assertEqual(
            str(node),
            '<a> ::= <b> <a0>\n'
            '<a0> ::= <c> <d>'
        )

    def test_factor_five_length_RHS(self):
        """Make sure recursive calls function correctly."""
        tree = Parser().parse(
            '<a2> ::= ":"\n'
            '<a> ::= <a2> <b> <c> <d> <e>'
        )
        node = Translator().translate(tree)
        expected = (
            '<a2> ::= ":"\n'
            '<a> ::= <a2> <a0>\n'
            '<a0> ::= <b> <a1>\n'
            '<a1> ::= <c> <a3>\n'
            '<a3> ::= <d> <e>'
        )
        self.assertEqual(
            str(node),
            expected,
        )

    def test_eliminate_simplest_epsilon_form(self):
        tree = Parser().parse('<E> ::= "e" | ε')
        node = Translator().translate(tree)
        expected = '<E> ::= "e"'
        self.assertEqual(
            str(node),
            expected,
        )

    def test_removes_empty_productions_after_epsilon_elimination(self):
        tree = Parser().parse(
            '<A> ::= "a"\n'
            '<B> ::= ε'
        )
        node = Translator().translate(tree)
        expected = '<A> ::= "a"'
        self.assertEqual(
            str(node),
            expected,
        )

    def test_eliminate_epsilon_forms(self):
        """Make sure we can eliminate all ε-rules."""
        tree = Parser().parse(
            '<S> ::= <A> <B>\n'
            '<B> ::= "b"\n'
            '<A> ::= "a" | ε'
        )
        node = Translator().translate(tree)
        expected = (
            '<S> ::= <A> <B> | <B>\n'
            '<B> ::= "b"\n'
            '<A> ::= "a"'
        )
        self.assertEqual(
            str(node),
            expected,
        )

    def test_elimination_with_multiple_passes(self):
        """Make sure we can eliminate all ε-rules, even with mult. passes."""
        tree = Parser().parse(
            '<A> ::= <LETTER> <B>\n'
            '<B> ::= <C>\n'
            '<C> ::= <LETTER> | ε\n'
            '<LETTER> ::= "a"'
        )
        node = Translator().translate(tree)
        expected = (
            '<A> ::= <LETTER> <B> | <LETTER>\n'
            '<B> ::= <C>\n'
            '<C> ::= <LETTER>\n'
            '<LETTER> ::= "a"'
        )
        self.assertEqual(
            str(node),
            expected,
            f'\n\nExpected:\n{expected}\n\nBut Got:\n{str(node)}\n\n'
        )
