"""A utility to convert from Backus-Naur form to Chomsky Normal Form.

Backus-Naur Form (BNF) is a more natural way to encode the grammars for
docstrings.  However, the CYK parsing algorithm (in its simplest form)
Chomsky Normal From (CNF).  This utility, intended for use during
development, converts BNF grammars to CNF grammars, using the algorithm
outlined in the Wikipedia page on CNF:
https://en.wikipedia.org/wiki/Chomsky_normal_form.

The general plan here is to parse the BNF, manipulate the tree, then
produce the CNF of the grammar from the modified tree.

"""

import re

LHS = re.compile(r'^\w[\w_-]*$')
RHS = re.compile(r'[\w:_\-"\.]')


class ValidationError(Exception):
    pass


class Validator(object):
    """Validates a CNF production.

    For now, because it's simple, this validator operates
    on a string representation of the production.  In the
    future, we should probably move it to validate the tree.

    """

    def __init__(self, raise_exception=False):
        # type: (bool) -> None
        """Create a new Validator.

        Args:
            raise_exception: If False, this validation returns
                whether the production is valid or not.  If true,
                then it raises an exception with an explanation of
                why.

        """
        self.raise_exception = raise_exception

    def _lhs(self, lhs: str) -> bool:
        if not LHS.match(lhs):
            return self._wrap(f'The lhs, "{lhs}" is not a simple identifier.')
        return True

    def _rhs(self, rhs: str) -> bool:
        i = 0
        while i < len(rhs):

            escaped_character = rhs[i] == '\\'
            if escaped_character:
                i += 2
                continue

            if not RHS.match(rhs[i]):
                return self._wrap(
                    f'The rhs, "{rhs}" contains an invalid character, '
                    f'"{rhs[i]}" at position {i}'
                )
            i += 1

        return True

    def _wrap(self, reason: str) -> bool:
        if self.raise_exception:
            raise ValidationError(reason)
        return False

    def validate(self, production):
        # type: (str) -> bool
        """Validate that the given production is in CNF.

        Args:
            production: The production to validate.

        Returns:
            Whether the production is valid or not.

        """
        # Since this is just an internal tool, it's okay if it's
        # fragile: we can assume that there are spaces around the
        # "::=" operator.
        if production.count(' ::= ') != 1:
            return self._wrap(
                'Production must contain the operator, '
                '"::=", surrounded by a single space.'
            )

        lhs, rhs = production.split(' ::= ')
        return self._lhs(lhs) and self._rhs(rhs)
