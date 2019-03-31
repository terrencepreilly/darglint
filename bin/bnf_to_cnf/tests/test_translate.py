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
                '<arg-header> ::= <arg> <QCQ>',
                '<QCQ> ::= ":"',
            ]),
        )
