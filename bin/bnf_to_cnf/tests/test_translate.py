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
            '''
                <one> ::= "1"
                <zero> ::= "0"
            ''',
        ]
        for example in examples:
            tree = Parser().parse(example)
            self.assertEqual(
                tree,
                Translator().translate(tree),
            )
