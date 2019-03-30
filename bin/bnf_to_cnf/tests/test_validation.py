from unittest import (
    TestCase,
)
from bnf_to_cnf.validate import (
    Validator,
)


class ValidateCnfTests(TestCase):

    def test_terminal_production(self):
        """Make sure we a terminal production passes."""
        valid_productions = [
            'COLON ::= ":"',
            'PARAM ::= "Args"',
            'QUOTE ::= "\"\"\""',
            'PERIOD ::= "."',
        ]
        for production in valid_productions:
            self.assertTrue(
                Validator().validate(production),
                '"{}" should not be valid'.format(production)
            )

    def test_lhs_cannot_contain_parentheses_or_brackets(self):
        """Make sure there are no groupings on the lhs."""
        for l, r in ['()', '[]']:
            invalid_productions = [
                'COLON{right} ::= ":"',
                '{left}COLON ::= ":"',
                'C{left}OLO{right}N ::= ":"',
                '{left}{right}COLON ::= ":"',
            ]
            for production in invalid_productions:
                self.assertFalse(
                    Validator().validate(production.format(left=l, right=r)),
                    '"{}" should not be valid'.format(production)
                )

    def test_lhs_cannot_contain_commas_spaces_pluses_or_asterisks(self):
        """Make sure the lhs has only one item."""
        for c in ', +*':
            invalid_productions = [
                'COLON{}HEADING ::= COLON HEADING'.format(c),
                'COLON{} ::= ":"'.format(c),
                '{}COLON ::= ":"'.format(c),
                'CO{}LON ::= ":"'.format(c),
            ]
            for production in invalid_productions:
                self.assertFalse(
                    Validator().validate(production),
                    '"{}" should not be valid'.format(production),
                )

    def test_rhs_cannot_contain_spaces_pluses_or_asterisks(self):
        """Make sure the rhs has only one item."""
        for c in ', +*|':
            invalid_productions = [
                'ARGS ::= {}Args',
                'ARGS ::= Args{}',
                'ARGS ::= Ar{}gs',
            ]
            for production in invalid_productions:
                self.assertFalse(
                    Validator().validate(production),
                    '"{}" should not be valid'.format(production),
                )

    def test_escaped_characters_okay(self):
        """Make sure that special characters are okay if escaped."""
        for c in ', +*()[]|':
            self.assertTrue(
                Validator().validate('SOMETHING ::= A\\{}B'.format(c)),
                'Escaping "{}" should allow it.'.format(c),
            )
