"""Defines a base class far describing grammars."""

import abc
from typing import (  # noqa: F401
    Dict,
    List,
    Tuple,
    Union,
)


NonTerminalDerivation = Tuple[str, str]  # Add BaseGrammar to this as union.
TerminalDerivation = str
Derivation = Union[NonTerminalDerivation, TerminalDerivation]


class Production(object):
    """Represents a production in a grammar."""

    def __init__(self, lhs, *rhs):
        # type: (str, Union[NonTerminalDerivation, TerminalDerivation]) -> None
        """Create a new production.

        Args:
            lhs: The left-hand side of the production.
            *rhs: The items in the right-hand side of the
                production.

        """
        self.lhs = lhs
        self.rhs = rhs


class BaseGrammar(abc.ABC):

    @property
    @abc.abstractmethod
    def productions(self):
        # type: () -> List[Production]
        pass

    @property
    @abc.abstractmethod
    def start(self):
        # type: () -> str
        pass

    @classmethod
    def get_symbol_lookup(cls):
        # type: () -> Dict[str, int]
        lookup = dict()  # type: Dict[str, int]

        # We have to tell the type checker that productions is, in fact,
        # a list, since it enumerate actually takes a wider type (Iterable),
        # and it gets confused.
        assert isinstance(cls.productions, list)
        for i, production in enumerate(cls.productions):
            symbol = production.lhs
            lookup[symbol] = i
        return lookup
