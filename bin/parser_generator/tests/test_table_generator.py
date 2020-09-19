from collections import OrderedDict
from unittest import TestCase

from parser_generator.generators import (
    LLTableGenerator,
)

from .grammars import (
    lex,
    ONE_TOKEN_GRAMMAR,
)


class LLTableGeneratorTests(TestCase):

    def test_generates_rules(self):
        table_gen = LLTableGenerator(ONE_TOKEN_GRAMMAR)
        rules = table_gen.rules

        expected = OrderedDict()
        expected['start'] = ['one']
        expected['one'] = ['TokenType.ONE']
        self.assertEqual(
            rules,
            expected,
        )
