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
from typing import (
    List,
)

from .node import (
    Node,
    NodeType,
)


class ValidationError(Exception):
    pass


class Validator(object):
    """Validates a CNF production.

    For now, because it's simple, this validator operates
    on a string representation of the production.  In the
    future, we should probably move it to validate the tree.

    """

    def __init__(self, raise_exception: bool = False):
        """Create a new Validator.

        Args:
            raise_exception: If False, this validation returns
                whether the production is valid or not.  If true,
                then it raises an exception with an explanation of
                why.

        """
        self.raise_exception = raise_exception

    def _wrap(self, reason: str) -> bool:
        if self.raise_exception:
            raise ValidationError(reason)
        return False

    def _validate_sequence(self, sequence: Node) -> bool:
        assert sequence.node_type == NodeType.SEQUENCE, (
            f'"{sequence}" is not a Sequence'
        )
        assert len(sequence.children) > 0
        if len(sequence.children) == 1:
            if sequence.children[0].node_type != NodeType.TERMINAL:
                return self._wrap(
                    f'"{sequence}" has only one node: it should be terminal.'
                )
        elif len(sequence.children) == 2:
            if not all([
                x.node_type == NodeType.SYMBOL
                for x in sequence.children
            ]):
                return self._wrap(
                    f'"{sequence}" has two nodes: they should '
                    f'be non-terminals.'
                )
        else:
            return self._wrap(f'"{sequence} has more than 3 token on the RHS.')
        return True

    def _validate_production(self, production: Node) -> bool:
        assert production.node_type == NodeType.PRODUCTION
        for sequence in production.children[1].children:
            if not self._validate_sequence(sequence):
                return False
        return True

    def _validate_import(self, _import: Node) -> bool:
        assert _import.node_type == NodeType.IMPORT

        # There should be a value, if there is an import.
        return _import.value is not None

    def validate(self, grammar: Node) -> bool:
        """Validate that the given production is in CNF.

        Args:
            grammar: The grammar to validate.

        Throws:
            ValidationError: If the grammar was not valid
                and raise_exception is True.

        Returns:
            Whether the grammar is valid or not.

        """
        assert grammar.node_type == NodeType.GRAMMAR
        imports = list()  # type: List[Node]
        if (
            grammar.children
            and grammar.children[0].node_type == NodeType.IMPORTS
        ):
            imports = grammar.children[0].children
            productions = grammar.children[1:]
        else:
            productions = grammar.children
        for _import in imports:
            if not self._validate_import(_import):
                return False
        for production in productions:
            if not self._validate_production(production):
                return False
        return True
