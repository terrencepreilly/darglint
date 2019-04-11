from unittest import (
    TestCase,
)
from bnf_to_cnf.validate import (
    Validator,
)
from bnf_to_cnf.parser import (
    Parser,
)


class ValidateCnfTests(TestCase):

    def setUp(self):
        self.parser = Parser()

    def _p(self, grammar):
        return self.parser.parse(grammar)

    def test_terminal_production(self):
        """Make sure we a terminal production passes."""
        valid_productions = [
            '<COLON> ::= ":"',
            '<PARAM> ::= "Args"',
            '<QUOTE> ::= "\\"\\"\\""',
            # '<PERIOD> ::= "."',
        ]
        for production in valid_productions:
            self.assertTrue(
                Validator().validate(self._p(production)),
                '"{}" should not be valid'.format(production)
            )

    def test_escaped_characters_okay(self):
        """Make sure that special characters are okay if escaped."""
        for c in ', +*()[]|':
            self.assertTrue(
                Validator().validate(
                    self._p('<SOMETHING> ::= "A\\{}B"'.format(c))
                ),
                'Escaping "{}" should allow it.'.format(c),
            )
